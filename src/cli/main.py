#!/usr/bin/env python3
"""
LLM Summary Evaluation Tool - Central CLI Driver

This script provides a command-line interface for running different evaluation pipelines.
"""

import sys
import os
from pathlib import Path

# Add src directory to path for imports
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    from pipelines.email_processor import EmailProcessor
    from pipelines.web_fetcher import WebFetcher
    from pipelines.evaluator import Evaluator
    from config.settings import Settings
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure you're running from the correct directory and all dependencies are installed.")
    sys.exit(1)


class CLIDriver:
    """Central command-line interface for the LLM evaluation tool."""
    
    def __init__(self):
        self.settings = Settings()
        self.evaluator = Evaluator(self.settings)
        
    def display_main_menu(self):
        """Display the main menu options."""
        print("\n" + "="*50)
        print("LLM Summary Evaluation Tool")
        print("="*50)
        print("1. Process Email Archives")
        print("2. Process Web URLs")
        print("3. Process Direct Text/Prompts")
        print("4. Configuration")
        print("5. Exit")
        print("="*50)
        
    def run_email_pipeline(self):
        """Run the email processing pipeline."""
        print("\n--- Email Processing Pipeline ---")
        processor = EmailProcessor(self.settings)
        
        # Extract articles from email archive
        articles = processor.extract_articles()
        if not articles:
            print("No articles found in email archive.")
            return
            
        print(f"Found {len(articles)} articles to process.")
        
        # Process through evaluation pipeline
        self.evaluator.process_articles(articles)
        
    def run_web_pipeline(self):
        """Run the web fetching pipeline."""
        print("\n--- Web Fetching Pipeline ---")
        fetcher = WebFetcher(self.settings)
        
        # Get URLs from file or user input
        urls = fetcher.get_urls()
        if not urls:
            print("No URLs to process.")
            return
            
        print(f"Found {len(urls)} URLs to process.")
        
        # Process each URL through evaluation pipeline
        for url in urls:
            content = fetcher.fetch_content(url)
            if content:
                self.evaluator.process_content(content, url)
                
    def run_prompt_pipeline(self):
        """Run the direct prompt pipeline."""
        print("\n--- Direct Prompt Pipeline ---")
        
        prompt = input("Enter your prompt/question: ").strip()
        if not prompt:
            print("No prompt provided.")
            return
            
        # Process prompt through evaluation pipeline
        self.evaluator.process_prompt(prompt)
        
    def show_configuration(self):
        """Display and modify configuration settings."""
        print("\n--- Configuration ---")
        print("1. View Current Settings")
        print("2. Modify Model List")
        print("3. Change File Paths")
        print("4. Back to Main Menu")
        
        choice = input("Select option: ").strip()
        
        if choice == "1":
            self.settings.display_settings()
        elif choice == "2":
            self.settings.modify_models()
        elif choice == "3":
            self.settings.modify_paths()
        elif choice == "4":
            return
        else:
            print("Invalid choice.")
            
    def run(self):
        """Main CLI loop."""
        while True:
            try:
                self.display_main_menu()
                choice = input("Select option (1-5): ").strip()
                
                if choice == "1":
                    self.run_email_pipeline()
                elif choice == "2":
                    self.run_web_pipeline()
                elif choice == "3":
                    self.run_prompt_pipeline()
                elif choice == "4":
                    self.show_configuration()
                elif choice == "5":
                    print("Goodbye!")
                    break
                else:
                    print("Invalid choice. Please select 1-5.")
                    
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
                input("Press Enter to continue...")


def main():
    """Entry point for the CLI application."""
    driver = CLIDriver()
    driver.run()


if __name__ == "__main__":
    main()