# Bazos AI Scraper

An intelligent Terminal User Interface (TUI) application that natively scrapes Bazos.cz classified listings and utilizes an autonomous LLM Agent (via OpenRouter/Google Gemini) to fetch, parse, and evaluate listings against any custom natural language objective.

## Features
- **Agentic AI Search**: Parses natural-language prompts like `"I want a used Lifepo4 battery for my 48v PV system"` directly into optimal Bazos queries and categories.
- **Smart Evaluation**: Downloads the listings and actively evaluates each one with Gemini, outputting a 1-10 relevance Score alongside a custom Description/Summary explaining the exact product state and why it matches your needs.
- **Multi-Category & Pagination**: Autonomously determines if a query needs to cross-search multiple categories at once. Click "Load More" to infinitely fetch down the index!
- **Interactive TUI**: Built on top of `Textual`, featuring live background-processing data tables that natively handle mouse functionality and can instantly open Bazos links in your browser!
- **HTML Export Support**: Generate standalone, interactive HTML and Plotly metric graphs outlining your fetched dataset with the click of a button.

## Setup
1. Clone the repository and initialize a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
2. Create a `.env` file in the root containing your API key:
```env
OPENROUTER_API_KEY=sk-or-v1-xxxxxx
```
3. Boot the application:
```bash
./run.sh
```

## Technology Stack
- **Textual**: Terminal Application GUI
- **httpx**: Asynchronous HTTP handling (Bazos JSON extraction)
- **OpenAI / OpenRouter**: Autonomous intent parsing and evaluation pipeline
- **Pandas / Plotly / Jinja2**: Rapid static data visualization rendering

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
