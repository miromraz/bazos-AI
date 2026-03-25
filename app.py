import asyncio
import logging
import pandas as pd
import webbrowser
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Header, Footer, Input, Button, Static, DataTable
from textual import work, on

from core.client import BazosClient
from ai.filter import AIFilter
from reporting.export import export_html_report

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class BazosApp(App):
    """A Textual App to scrape and analyze Bazos listings."""
    
    CSS = """
    Screen {
        layout: vertical;
    }
    #search-form {
        height: auto;
        padding: 1;
        border: solid green;
    }
    #results-container {
        height: 1fr;
        border: solid blue;
    }
    .input-row {
        height: auto;
        layout: horizontal;
    }
    Input {
        width: 1fr;
    }
    Button {
        width: 20;
    }
    """
    
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit app"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        
        with Container(id="search-form"):
            with Horizontal(classes="input-row"):
                yield Input(placeholder="Describe what you want (e.g. 'Lifepo4 battery for PV')", id="prompt-input")
                yield Button("Search", id="search-btn", variant="primary")
                yield Button("Load More", id="load-more-btn", variant="warning", disabled=True)
                yield Button("Export HTML", id="export-btn", variant="success", disabled=True)
            yield Static("Ready.", id="status-bar")
            
        with VerticalScroll(id="results-container"):
            yield DataTable(id="results-table")
            
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("ID", "Title", "Price", "AI Score", "Description", "Meets Criteria")
        table.cursor_type = "row"
        table.zebra_stripes = True

    @on(DataTable.RowSelected)
    def open_listing(self, event: DataTable.RowSelected) -> None:
        row_key = event.row_key.value
        selected = next((ad for ad in getattr(self, "current_results", []) if str(ad.get("id")) == row_key), None)
        
        if selected and selected.get("url"):
            url = selected["url"]
            self.update_status(f"Opening {url} in browser...")
            logging.info(f"Opening listing {url} via UI.")
            webbrowser.open(url)
        else:
            self.update_status("Error: Could not find URL for this listing.")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "search-btn":
            self.start_search()
        elif event.button.id == "load-more-btn":
            self.load_more()
        elif event.button.id == "export-btn":
            self.export_results()

    def start_search(self) -> None:
        self.query_one("#export-btn", Button).disabled = True
        self.query_one("#load-more-btn", Button).disabled = True
        self.current_results = []
        self.current_offset = 0
        prompt = self.query_one("#prompt-input", Input).value
        self.current_prompt = prompt
        
        table = self.query_one(DataTable)
        table.clear()
        
        self.fetch_and_analyze(prompt, is_load_more=False)

    def load_more(self) -> None:
        self.query_one("#load-more-btn", Button).disabled = True
        self.current_offset += 20
        # Passing empty prompt because we will reuse state
        self.fetch_and_analyze(self.current_prompt, is_load_more=True)

    @work(exclusive=True)
    async def fetch_and_analyze(self, prompt: str, is_load_more: bool = False) -> None:
        client = BazosClient()
        ai = AIFilter()
        
        try:
            if not ai.api_key or ai.api_key == "dummy_key":
                msg = "Error: OPENROUTER_API_KEY is required for AI agent tasks."
                self.update_status(msg)
                logging.error(msg)
                return
                
            # 1. Parse Intent
            if not is_load_more:
                self.update_status(f"Parsing intent for: '{prompt}'...")
                logging.info("--- New Search Started ---")
                logging.info(f"Prompt: {prompt}")
                
                intent = await ai.parse_search_intent(prompt)
                logging.info(f"Parsed Intent: {intent}")
                
                self.current_query = intent.get("query", "")
                cats = intent.get("categories", [])
                if not isinstance(cats, list):
                    cats = [cats] if cats else []
                self.current_categories = cats if len(cats) > 0 else [""]
            else:
                logging.info(f"--- Loading More (Offset: {self.current_offset}) ---")
            
            # 2. Fetch Multi-Category
            all_ads = []
            for cat in self.current_categories:
                msg = f"Searching Bazos for '{self.current_query}' in category '{cat}' (Offset: {self.current_offset})..."
                self.update_status(msg)
                logging.info(msg)
                
                res = await client.search_ads(query=self.current_query, section=cat, offset=self.current_offset, limit=20)
                ads = res if isinstance(res, list) else res.get("ads", [])
                all_ads.extend(ads)
            
            if not all_ads:
                self.update_status("No additional results found.")
                logging.warning("No results found on Bazos for this pagination batch.")
                return
                
            self.update_status(f"Found {len(all_ads)} listings. Reading listings and evaluating...")
            logging.info(f"Found {len(all_ads)} listings combined. Beginning Gemini evaluation...")
            
            # 3. Analyze
            analyzed = await ai.evaluate_listings(all_ads, prompt)
            logging.info(f"Gemini evaluation completed successfully.")
                
            # 4. Update Table
            self.populate_table(analyzed, is_load_more)
            self.update_status("Analysis complete.")
            
        except Exception as e:
            self.update_status(f"Error: {e}")
            logging.exception("Exception during search and evaluation workflow:")
            
        finally:
            await client.close()
            
    def update_status(self, msg: str) -> None:
        try:
            self.query_one("#status-bar", Static).update(msg)
        except Exception:
            pass
        
    def populate_table(self, ads: list, is_load_more: bool = False) -> None:
        try:
            if is_load_more:
                combined_ads = self.current_results + ads
            else:
                combined_ads = ads

            # Sort by AI score, descending
            def get_score(ad):
                try:
                    return float(ad.get("ai_eval", {}).get("score", 0))
                except (ValueError, TypeError):
                    return 0
            
            sorted_ads = sorted(combined_ads, key=get_score, reverse=True)
            self.current_results = sorted_ads
            
            table = self.query_one(DataTable)
            table.clear() # Clear and repopulate entirely because of resorting
            for ad in sorted_ads:
                ai_eval = ad.get("ai_eval", {})
                table.add_row(
                    str(ad.get("id")),
                    str(ad.get("title")),
                    str(ad.get("price_formatted", ad.get("price", "-"))),
                    str(ai_eval.get("score", "-")),
                    str(ai_eval.get("description", "-")),
                    str(ai_eval.get("meets_criteria", "-")),
                    key=str(ad.get("id"))
                )
            if self.current_results:
                self.query_one("#export-btn", Button).disabled = False
                self.query_one("#load-more-btn", Button).disabled = False
        except Exception:
            pass
            
    def export_results(self) -> None:
        if not hasattr(self, 'current_results') or not self.current_results:
            self.update_status("No results to export.")
            return
            
        try:
            path = export_html_report(self.current_results, getattr(self, 'current_query', 'Bazos Search'))
            self.update_status(f"Exported to {path}")
            logging.info(f"Successfully exported HTML report to {path}")
        except Exception as e:
            self.update_status(f"Export failed: {e}")
            logging.exception("Failed to export HTML report:")

if __name__ == "__main__":
    app = BazosApp()
    app.run()
