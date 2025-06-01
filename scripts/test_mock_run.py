#!/usr/bin/env python3
"""Mock test for StrudelJam pipeline - simulates a run without API calls."""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent))
import run_bench

def mock_pipeline_run():
    """Simulate a pipeline run with mocked API calls."""
    print("\n🎭 Mock Pipeline Test\n")
    
    # Create a temporary directory for test data
    with tempfile.TemporaryDirectory() as tmpdir:
        # Override the DATA_DIR for this test
        original_data_dir = run_bench.DATA_DIR
        run_bench.DATA_DIR = Path(tmpdir) / "data"
        run_bench.INDEX_JSON = run_bench.DATA_DIR / "index.json"
        
        # Mock the OpenRouter API call with correct signature
        def mock_call_chat(router_id, messages):
            print(f"  Mock API call: {router_id}")
            # Get the user prompt from messages
            user_msg = next((m for m in messages if m['role'] == 'user'), None)
            if not user_msg:
                return '<CODE>s("sine").freq(440)</CODE>'
            
            instructions = user_msg['content'].lower()
            # Return different responses based on the prompt
            if "jazz" in instructions:
                return '<CODE>s("bd hh*2, ~ cp").swing(0.1).fast(2)</CODE>'
            elif "techno" in instructions:
                return '<CODE>stack(s("bd*4"), s("~ hh*2").delay(0.5))</CODE>'
            elif "alien" in instructions:
                return '<CODE>s("sine").freq("200 400 600").fast(3).gain(0.5)</CODE>'
            elif "ambient" in instructions:
                return '<CODE>s("sine").freq(seq(200,250,300,350)).slow(8).gain(0.3)</CODE>'
            elif "color yellow" in instructions:
                return '<CODE>s("triangle").freq(550).gain(0.4).room(0.5)</CODE>'
            elif "trap" in instructions:
                return '<CODE>stack(s("bd*2"), s("~ cp"), s("hh*8").gain(0.5))</CODE>'
            else:
                return '<CODE>s("sine").freq(440).gain(0.5)</CODE>'
        
        # Mock the compile check to succeed for valid patterns
        def mock_compile_strudel(code):
            print(f"  Mock compile: {code[:30]}...")
            # Simple check - if it starts with 's(' or 'stack(' it's probably valid
            if code.strip().startswith(('s(', 'stack(', 'seq(')):
                return True, ""
            else:
                return False, "Invalid Strudel pattern"
        
        try:
            # Apply mocks
            with patch('run_bench.call_chat', side_effect=mock_call_chat):
                with patch('run_bench.compile_strudel', side_effect=mock_compile_strudel):
                    with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'sk-mock-key'}):
                        # Run the pipeline
                        print("Running mock pipeline...")
                        run_bench.run(only_new=False, parallel_workers=1)  # Use single worker for predictable test
                        
                        # Check results
                        if run_bench.INDEX_JSON.exists():
                            index = json.loads(run_bench.INDEX_JSON.read_text())
                            print(f"\n✅ Generated index.json with {len(index)} prompts")
                            
                            for entry in index:
                                print(f"\n  Prompt: {entry['title']}")
                                print(f"  Models tested: {len(entry['models'])}")
                                
                                # Check that data files were created
                                for model in entry['models']:
                                    card_path = run_bench.DATA_DIR / model['card']
                                    if card_path.exists():
                                        card_data = json.loads(card_path.read_text())
                                        status = "✓" if card_data['success'] else "✗"
                                        print(f"    {status} {model['name']}")
                                    else:
                                        print(f"    ⚠️  Missing: {model['card']}")
                            
                            print("\n✅ Mock pipeline test completed successfully!")
                            return True
                        else:
                            print("\n❌ No index.json generated")
                            return False
                            
        except Exception as e:
            print(f"\n❌ Mock test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Restore original paths
            run_bench.DATA_DIR = original_data_dir
            run_bench.INDEX_JSON = original_data_dir / "index.json"

if __name__ == "__main__":
    success = mock_pipeline_run()
    sys.exit(0 if success else 1) 