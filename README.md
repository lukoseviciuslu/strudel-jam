# StrudelJam 🎵

A public benchmark gallery showing how different LLMs generate [Strudel](https://strudel.cc) music patterns.

**[View Live Demo →](https://YOUR-USERNAME.github.io/strudel-jam)**

## What is this?

StrudelJam automatically:
- 🤖 Calls various LLMs with music generation prompts
- 🎹 Validates the generated Strudel code
- 📊 Creates a beautiful gallery of working patterns
- 🎵 Lets visitors play and edit the patterns in-browser

## Requirements

- Python 3.6+ (uses f-strings)
- Node.js 18+ (for Strudel validation)
- OpenRouter API key

## Quick Start

### 1. Fork & Clone

```bash
git clone https://github.com/YOUR-USERNAME/strudel-jam
cd strudel-jam
```

### 2. Set up OpenRouter API Key

Get your API key from [OpenRouter](https://openrouter.ai) and add it to your repo's secrets:

1. Go to Settings → Secrets → Actions
2. Add `OPENROUTER_API_KEY` with your key

### 3. Enable GitHub Pages

1. Go to Settings → Pages
2. Source: Deploy from a branch
3. Branch: `gh-pages` / `root`
4. Save

### 4. Run the Pipeline

Either:
- Push new prompts/models to trigger automatically
- Go to Actions → StrudelJam Pipeline → Run workflow

## Adding Content

### New Prompts

Create a file in `public/prompts/`:

```markdown
# public/prompts/funky-bassline.md
Create a funky slap bass line in E minor at 95 BPM.
Use ghost notes and syncopation.
```

### New Models

Create a JSON file in `models/`:

```json
{
  "id": "mixtral-8x7b",
  "displayName": "Mixtral 8x7B",
  "openrouter_id": "mistralai/mixtral-8x7b-instruct"
}
```

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt
npm install -g @strudel/core

# Set API key
export OPENROUTER_API_KEY=sk-...

# Run benchmark (with parallel processing)
python scripts/run_bench.py --only-new --parallel 4

# Run specific prompt/model
python scripts/run_bench.py --prompt jazzy-chords --model gpt-4o

# Serve locally
python -m http.server 8000 -d public
```

## How It Works

1. **Discovery**: Finds all prompt × model combinations
2. **Generation**: Calls each model via OpenRouter (with conversational retries)
3. **Validation**: Tests code with `@strudel/core` (headless)
4. **Storage**: Saves results to `/data` (git-tracked)
5. **Display**: Static site with embedded Strudel players

The pipeline uses parallel workers (default: 4) to speed up processing and includes a conversational retry mechanism - if code fails to compile, it sends the error back to the model for correction.

## Project Structure

```
strudel-jam/
├── models/           # LLM configurations  
├── public/           # Static website
│   ├── prompts/      # Music generation prompts
│   ├── data/         # Generated results (auto-committed)
│   ├── p/            # Individual prompt pages
│   └── pages/        # JavaScript modules
├── scripts/          # Pipeline code
└── .github/          # CI/CD workflows
```

## Advanced Options

- `--max-retries N`: Number of retry attempts (default: 3)
- `--parallel N`: Number of parallel workers (default: 4)
- `--force`: Overwrite existing results

## Dependencies

- **Python**: requests
- **Node.js**: @strudel/core, @strudel/mini, @strudel/web
- **Browser**: @strudel/embed (loaded from CDN)

## Customization

- Edit `context.txt` to change the system prompt
- Modify `public/` for custom styling
- Adjust pipeline settings in `scripts/run_bench.py`

## Contributing

1. Add interesting prompts that showcase different musical styles
2. Add new models as they become available
3. Improve the UI/UX of the gallery

## License

MIT - Feel free to fork and create your own music AI galleries!

---

Built with [Strudel](https://strudel.cc) and [OpenRouter](https://openrouter.ai) 