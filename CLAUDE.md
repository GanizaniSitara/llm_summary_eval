# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
This is a modular LLM evaluation framework for testing text summarization across multiple models. The project extracts content from various sources (email archives, web URLs, or direct prompts), processes it through different LLM models, and generates HTML reports highlighting differences between model outputs.

## New Modular Architecture

### Directory Structure
```
src/
├── cli/
│   └── main.py                 # Central CLI driver with menu interface
├── pipelines/
│   ├── email_processor.py      # Email archive extraction pipeline
│   ├── web_fetcher.py          # Web content fetching (Medium/Freedium)
│   └── evaluator.py            # LLM evaluation pipeline
├── core/
│   ├── models.py               # Model management (Ollama/OpenAI)
│   ├── output.py               # HTML generation & highlighting
│   └── utils.py                # Shared utilities
└── config/
    └── settings.py             # Configuration management

legacy/                         # Old monolithic files (preserved)
run.py                         # Main launcher script
```

## Development Commands

### Running the Application
```bash
# Main CLI interface with menus
python run.py

# Direct CLI execution
python src/cli/main.py
```

### Testing
```bash
# Run tests (currently in legacy/ - needs updating)
pytest legacy/tests.py

# Test specific functionality
python -c "from src.core.models import ModelManager; print('Models OK')"
```

### Development Setup
```bash
# Install dependencies (no requirements.txt yet - check legacy files)
pip install ollama openai playwright beautifulsoup4

# Playwright browser setup
playwright install chromium
```

## Key Architectural Improvements

### Separation of Concerns
- **Email Processing**: `EmailProcessor` class handles OE Classic .mbx files
- **Web Fetching**: `WebFetcher` handles URL content with Medium→Freedium translation
- **Evaluation**: `Evaluator` manages multi-model processing and comparison
- **Output**: `OutputGenerator` creates HTML reports with difference highlighting

### CLI Interface
- Menu-driven interface replaces configuration file switching
- Interactive model management and path configuration
- Clear separation between different content sources

### Model Management
- Unified interface for Ollama and OpenAI models
- Automatic model availability testing
- Configurable repetition counts (3x for Ollama, 1x for OpenAI)

### Configuration
- Centralized `Settings` class replaces scattered config variables
- Interactive configuration modification
- Runtime model list validation

## Processing Pipelines

### Email Pipeline
1. Extract articles from OE Classic email archive (.mbx)
2. Parse HTML content to find article links
3. Save extracted articles to CSV
4. Process subset based on configuration

### Web Pipeline
1. Load URLs from file or manual input
2. Transform Medium URLs to Freedium for better access
3. Use Playwright for content extraction with popup handling
4. Extract clean text from main content areas

### Evaluation Pipeline
1. Run content through all configured models
2. Support multiple repetitions per model
3. Time each execution for performance analysis
4. Generate timestamped HTML reports
5. Apply difference highlighting between model outputs

## Important Implementation Details

### Model Integration
- OpenAI models run once to save tokens
- Ollama models run 3x for consistency analysis
- Models are pre-loaded when possible for better performance
- Error handling preserves partial results

### Content Processing
- Playwright runs in non-headless mode for better content access
- Automatic popup/modal dismissal
- Multiple content selector fallbacks
- BeautifulSoup for clean text extraction

### Output Generation
- HTML tables with responsive design
- Difference highlighting using tokenization and comparison
- Time string handling for performance data
- Automatic browser opening for generated reports

## Migration Notes
- Original files moved to `legacy/` directory
- Configuration migrated from `config.py` to `Settings` class
- Tests need updating for new modular structure
- Main functionality preserved but better organized

## Dependencies
- `ollama` - Local LLM API
- `openai` - OpenAI API client
- `playwright` - Web scraping
- `beautifulsoup4` - HTML parsing
- `csv` - Data export (built-in)

## Troubleshooting
- Ensure Playwright browsers are installed: `playwright install chromium`
- Check model availability with the CLI configuration menu
- Verify file paths in settings for email archives
- Run from project root directory to ensure proper imports