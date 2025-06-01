"""run_bench.py - incremental pipeline for StrudelJam (Strudel + LLMs)

 Revised to support *conversational retries*:
 ▸ After a compile failure the next request is sent with the full chat history
   (system → user → assistant → user‑feedback) so the model gets proper context.
 ▸ Adds a generic `chat` helper that accepts an arbitrary messages array.
 ▸ Captures compiler stderr verbatim.
 ▸ JSON card now stores `messages` (trimmed) for reproducibility.
"""
from __future__ import annotations
import argparse, json, os, re, subprocess, sys, textwrap, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

import requests

# ─────────────────────────── paths ────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT / "public" / "prompts"
MODELS_DIR  = ROOT / "models"
DATA_DIR    = ROOT / "public" / "data"
INDEX_JSON  = DATA_DIR / "index.json"
CONTEXT_TXT = ROOT / "context.txt"   # shared system prompt

# ────────────────────────── config ───────────────────────────
DEFAULT_MAX_RETRIES = 3          # overridable via CLI
NODE_TIMEOUT        = 30         # seconds for compile test
OPENROUTER_URL      = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_PARALLEL_WORKERS = 4     # number of concurrent requests

# ─────────────────────────── helpers ──────────────────────────

def load_json(path: Path, default):
    return json.loads(path.read_text("utf-8")) if path.exists() else default

def dump_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), "utf-8")

def slugify(name: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9-]+", "-", name.lower())).strip("-")

def extract_code(text: str) -> str:
    md = re.search(r"```(?:[\w-]*\n)?(.*?)```", text, re.S)
    if md:
        return md.group(1).strip()
    tagged = re.search(r"<CODE>\s*(.*?)\s*</CODE>", text, re.S | re.I)
    return tagged.group(1).strip() if tagged else text.strip()

# ───────────────────── Strudel compile check ───────────────────

def compile_strudel(code: str) -> tuple[bool, str]:
    """Returns (success, stderr)."""
    snippet = textwrap.dedent(f"""
        Promise.all([import('@strudel/core'), import('@strudel/mini'), import('@strudel/tonal')])
          .then(([core, mini, tonal]) => {{
            const m = {{...core, ...mini, ...tonal}};
            try {{ new Function(...Object.keys(m), `{code.replace('`', '\\`')}`)(...Object.values(m)); }}
            catch(e) {{ console.error(e.message); process.exit(1); }}
            process.exit(0);
          }}).catch(e => {{ console.error(e.message); process.exit(1); }});
    """)
    try:
        proc = subprocess.run(["node", "-e", snippet], capture_output=True, text=True, timeout=NODE_TIMEOUT)
        return proc.returncode == 0, (proc.stderr or proc.stdout).strip()
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        return False, str(e)

# ───────────────────── OpenRouter wrapper ─────────────────────

def call_chat(router_id: str, messages: list[dict], timeout=120) -> str:
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY env var not set")
    res = requests.post(
        OPENROUTER_URL,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": router_id, "messages": messages},
        timeout=timeout,
    )
    res.raise_for_status()
    return res.json()["choices"][0]["message"]["content"]

# ───────────────────── discovery helpers ─────────────────────

def discover_prompts() -> Dict[str, str]:
    return {slugify(p.stem): p.read_text("utf-8") for p in PROMPTS_DIR.iterdir() if p.is_file()}

def discover_models() -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    for cfg in MODELS_DIR.glob("*.json"):
        data = load_json(cfg, None)
        if data:
            out[data["id"]] = data
    return out

def existing_pairs() -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    if DATA_DIR.exists():
        for d in DATA_DIR.iterdir():
            if d.is_dir():
                for card in d.glob("*.json"):
                    pairs.add((d.name, card.stem))
    return pairs

# ─────────────────────── worker function ───────────────────────

def process_single_benchmark(
    pslug: str, 
    mid: str, 
    prompt_text: str, 
    context: str, 
    models: dict, 
    max_retries: int
) -> dict:
    """Process a single (prompt, model) benchmark and return the result card."""
    rid = models[mid].get("openrouter_id", mid)
    print(f"→ {pslug} | {rid}")

    start = time.perf_counter()
    success = False
    compile_err, code, rawresp = "", "", ""
    attempts = 0

    # Chat history begins with system & user
    history = [
        {"role": "system", "content": context},
        {"role": "user", "content": prompt_text},
    ]

    while attempts < max_retries and not success:
        attempts += 1
        try:
            rawresp = call_chat(rid, history)
            history.append({"role": "assistant", "content": rawresp})
            code = extract_code(rawresp)
            success, compile_err = compile_strudel(code)
            if success:
                break
            # add feedback and retry
            feedback = (
                f"The Strudel code above failed to compile with this error:\n{compile_err}\n\n"
                "Please correct the code and return *only* a working Strudel snippet inside a <CODE>...</CODE> tag or fenced ``` block."
            )
            history.append({"role": "user", "content": feedback})
            print(f"  ✗ compile failed (attempt {attempts}/{max_retries}) for {pslug}/{mid}")
        except Exception as e:
            compile_err = str(e)
            print(f"  ⚠ error: {compile_err} (attempt {attempts}/{max_retries}) for {pslug}/{mid}")
            time.sleep(2 * attempts)

    duration = round(time.perf_counter() - start, 2)
    card = {
        "model": mid,
        "router_id": rid,
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "success": success,
        "durationSec": duration,
        "attempts": attempts,
        "code": code if success else None,
        "compileError": None if success else compile_err,
        "rawResponse": None if success else rawresp,
        "messages": history[-6:],  # last few for brevity
    }

    # Save the card
    pdir = DATA_DIR / pslug
    pdir.mkdir(parents=True, exist_ok=True)
    dump_json(pdir / f"{mid}.json", card)
    
    print(f"{'✓' if success else '✗'} {pslug}/{mid} completed in {duration}s")
    
    return {"pslug": pslug, "mid": mid, "success": success}

# ─────────────────────────── main loop ────────────────────────

def run(only_new: bool = False, max_retries: int = DEFAULT_MAX_RETRIES,
        prompt_filter: Optional[str] = None, model_filter: Optional[str] = None,
        force: bool = False, parallel_workers: int = DEFAULT_PARALLEL_WORKERS):

    prompts, models = discover_prompts(), discover_models()
    context = CONTEXT_TXT.read_text("utf-8") if CONTEXT_TXT.exists() else ""

    if prompt_filter:
        prompts = {k: v for k, v in prompts.items() if k == prompt_filter}
    if model_filter:
        models = {k: v for k, v in models.items() if k == model_filter}

    if not prompts or not models:
        print("⚠ Nothing to do – check filters.")
        return

    todo = [(p, m) for p in prompts for m in models]
    if only_new and not force:
        done = existing_pairs()
        todo = [pair for pair in todo if pair not in done]
    if not todo:
        print("✨ All combinations already processed.")
        return

    print(f"📊 Processing {len(todo)} benchmarks with {parallel_workers} parallel workers...")
    
    # Process benchmarks in parallel
    results = []
    with ThreadPoolExecutor(max_workers=parallel_workers) as executor:
        # Submit all tasks
        future_to_pair = {}
        for pslug, mid in todo:
            future = executor.submit(
                process_single_benchmark,
                pslug, mid, prompts[pslug], context, models, max_retries
            )
            future_to_pair[future] = (pslug, mid)
        
        # Process completed futures
        try:
            for future in as_completed(future_to_pair):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    pslug, mid = future_to_pair[future]
                    print(f"⚠ Failed to process {pslug}/{mid}: {e}")
        except KeyboardInterrupt:
            print("\n⏹ Interrupted – cancelling remaining tasks...")
            executor.shutdown(wait=False, cancel_futures=True)
            print("⏹ Partial results will be kept.")
            
    # Update index after all processing is complete
    index = load_json(INDEX_JSON, [])
    index_map = {(e["promptSlug"], m["name"]) for e in index for m in e.get("models", [])}
    
    # Add new entries to index
    for result in results:
        pslug, mid = result["pslug"], result["mid"]
        if (pslug, mid) not in index_map:
            entry = next((x for x in index if x["promptSlug"] == pslug), None)
            if not entry:
                entry = {"promptSlug": pslug, "title": " ".join(pslug.split("-")), "dateRun": datetime.now(timezone.utc).date().isoformat(), "models": []}
                index.append(entry)
            entry["models"].append({"name": mid, "card": f"{pslug}/{mid}.json"})
            index_map.add((pslug, mid))

    index.sort(key=lambda e: e["dateRun"], reverse=True)
    dump_json(INDEX_JSON, index)
    
    # Summary
    successful = sum(1 for r in results if r["success"])
    print(f"\n✓ Benchmark complete: {successful}/{len(results)} successful")

# ───────────────────────── entry point ────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Run StrudelJam benchmark pipeline")
    ap.add_argument("--only-new", action="store_true", help="Skip combos that already have data")
    ap.add_argument("--prompt", help="Slug of a single prompt to run")
    ap.add_argument("--model", help="ID of a single model to run")
    ap.add_argument("--force", action="store_true", help="Overwrite existing data")
    ap.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES)
    ap.add_argument("--parallel", type=int, default=DEFAULT_PARALLEL_WORKERS, help="Number of parallel workers")
    args = ap.parse_args()

    run(
        only_new=args.only_new,
        max_retries=args.max_retries,
        prompt_filter=args.prompt,
        model_filter=args.model,
        force=args.force,
        parallel_workers=args.parallel,
    )
