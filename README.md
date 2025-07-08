# LLM Summary Evaluation Tool

A modular framework for evaluating and comparing text summarization across multiple LLM models. Process content from email archives, web URLs, or direct prompts, then generate HTML reports highlighting differences between model outputs.

## Features

- **Multi-Source Processing**: Email archives (OE Classic), web URLs, or direct text input
- **Pre-saved Prompt Evaluation**: Question/answer pairs with dual temperature testing
- **Multi-Model Support**: Both Ollama (local) and OpenAI models
- **Analytical & AI-based Scoring**: Word similarity, difflib comparison, and LLM evaluation
- **Automatic Comparison**: Runs multiple evaluations and highlights unique words between outputs
- **Medium Integration**: Automatic translation of Medium URLs to Freedium for better access
- **Interactive CLI**: Menu-driven interface for easy operation
- **HTML Reports**: Timestamped comparison tables with difference highlighting and scoring metrics

## Quick Start

### Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Playwright browsers:**
   ```bash
   playwright install chromium
   ```

3. **Setup LLM APIs:**
   - For Ollama: Install and start [Ollama](https://ollama.ai)
   - For OpenAI: Set your `OPENAI_API_KEY` environment variable

### Running the Tool

```bash
python run.py
```

This launches an interactive CLI with menu options:

1. **Process Email Archives** - Extract and evaluate articles from OE Classic email files
2. **Process Web URLs** - Fetch and evaluate content from web pages  
3. **Process Direct Text/Prompts** - Evaluate custom text or questions
4. **Evaluate Pre-saved Prompts** - Test models against question/answer pairs with dual temperature
5. **Configuration** - Manage models, paths, and settings

## Architecture

### Modular Design
```
src/
├── cli/main.py                 # Central CLI driver
├── pipelines/
│   ├── email_processor.py      # Email archive processing
│   ├── web_fetcher.py          # Web content fetching
│   ├── evaluator.py            # LLM evaluation pipeline
│   └── prompt_evaluator.py     # Pre-saved prompt evaluation
├── core/
│   ├── models.py               # Model management
│   ├── output.py               # HTML generation
│   └── utils.py                # Shared utilities
├── data/
│   └── question_bank.json      # Pre-saved question/answer pairs
└── config/settings.py          # Configuration management
```

### Processing Pipelines

- **Email Pipeline**: Extracts articles from OE Classic .mbx files
- **Web Pipeline**: Fetches content using Playwright with popup handling
- **Evaluation Pipeline**: Runs content through multiple models with timing analysis
- **Prompt Evaluation Pipeline**: Tests models against pre-saved question/answer pairs with dual temperature testing (0.0 for consistency, 0.8 for creativity)

## Configuration

The tool includes interactive configuration through the CLI:

- **Model Management**: Add/remove LLM models
- **File Paths**: Configure email archive and output locations  
- **Processing Settings**: Adjust repetition counts and prompts

Default models include:
- `gpt-4o-mini-2024-07-18` (OpenAI - runs once)
- Various Ollama models (run 3x for consistency analysis)

## Output

Generates timestamped HTML reports with:
- Side-by-side model comparisons
- Execution timing for each model
- Highlighting of unique words/phrases between outputs
- **Prompt Evaluation Scoring**: Analytical metrics (word/character similarity) and AI-based evaluation using gemma3:27b-it-q4_K_M
- **Temperature Comparison**: Shows consistency vs creativity in model responses
- Summary statistics and category-based performance analysis
- Automatic browser opening for immediate viewing

## Legacy Support

Original monolithic files are preserved in the `legacy/` directory for reference and backward compatibility.

## Dependencies

- **ollama**: Local LLM API client
- **openai**: OpenAI API client  
- **playwright**: Web scraping and content extraction
- **beautifulsoup4**: HTML parsing and processing

## Development

See [CLAUDE.md](CLAUDE.md) for detailed development guidance and architecture documentation. 

