#!/bin/bash
# StrudelJam Test Runner

echo "🎵 StrudelJam Test Suite"
echo "========================"

# Check if we're in the right directory
if [ ! -f "context.txt" ]; then
    echo "❌ Error: Must run from project root directory"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Run the main test suite
echo ""
echo "1️⃣ Running system tests..."
python3 scripts/test_pipeline.py
TEST1_EXIT=$?

# Run the mock pipeline test
echo ""
echo "2️⃣ Running mock pipeline test..."
python3 scripts/test_mock_run.py
TEST2_EXIT=$?

# Summary
echo ""
echo "========================"
if [ $TEST1_EXIT -eq 0 ] && [ $TEST2_EXIT -eq 0 ]; then
    echo "✅ All tests passed!"
    echo ""
    echo "Next steps:"
    echo "1. Set your OpenRouter API key: export OPENROUTER_API_KEY=sk-..."
    echo "2. Install dependencies:"
    echo "   - pip install -r requirements.txt"
    echo "   - npm install -g @strudel/core"
    echo "3. Run the pipeline: python3 scripts/run_bench.py"
    echo "4. Start local server: python3 -m http.server 8000 -d public"
    exit 0
else
    echo "❌ Some tests failed. Please fix issues before proceeding."
    exit 1
fi 