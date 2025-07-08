#!/usr/bin/env python3
"""
LLM Summary Evaluation Tool - Central CLI Driver

This script provides a command-line interface for running different evaluation pipelines.
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime

# Add src directory to path for imports
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    from pipelines.email_processor import EmailProcessor
    from pipelines.web_fetcher import WebFetcher
    from pipelines.evaluator import Evaluator
    from pipelines.prompt_evaluator import PromptEvaluator
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
        self.prompt_evaluator = PromptEvaluator(self.settings)
        
    def display_main_menu(self):
        """Display the main menu options."""
        print("\n" + "="*50)
        print("LLM Summary Evaluation Tool")
        print("="*50)
        print("1. Process Email Archives")
        print("2. Process Web URLs")
        print("3. Process Direct Text/Prompts")
        print("4. Evaluate Pre-saved Prompts")
        print("5. Configuration")
        print("q. Quit")
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
        
    def run_evaluation_pipeline(self):
        """Run the pre-saved prompt evaluation pipeline."""
        print("\n--- Pre-saved Prompt Evaluation Pipeline ---")
        
        # Display available categories
        categories = self.prompt_evaluator.get_available_categories()
        if not categories:
            print("No question categories found. Please check the question bank.")
            return
        
        print("\nAvailable question categories:")
        for i, category in enumerate(categories, 1):
            questions = self.prompt_evaluator.get_questions_by_category(category)
            print(f"{i}. {category} ({len(questions)} questions)")
        
        print(f"{len(categories) + 1}. Evaluate all categories")
        print(f"{len(categories) + 2}. Back to main menu")
        
        try:
            choice = int(input("\nSelect category: ").strip())
            
            if choice == len(categories) + 2:  # Back to main menu
                return
            elif choice == len(categories) + 1:  # Evaluate all
                selected_categories = categories
            elif 1 <= choice <= len(categories):
                selected_categories = [categories[choice - 1]]
            else:
                print("Invalid choice.")
                return
        except ValueError:
            print("Please enter a valid number.")
            return
        
        # Get available models
        print(f"\nAvailable models: {', '.join(self.settings.models)}")
        model_input = input("Enter models to test (comma-separated, or press Enter for all): ").strip()
        
        if model_input:
            models_to_test = [m.strip() for m in model_input.split(',')]
            # Validate models
            models_to_test = [m for m in models_to_test if m in self.settings.models]
        else:
            models_to_test = self.settings.models
        
        if not models_to_test:
            print("No valid models selected.")
            return
        
        print(f"\nWill test models: {', '.join(models_to_test)}")
        print(f"Temperature settings: {self.settings.evaluation_temperatures}")
        
        confirm = input("Proceed with evaluation? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Evaluation cancelled.")
            return
        
        # Run evaluations
        all_results = []
        
        for category in selected_categories:
            print(f"\n{'='*50}")
            print(f"Evaluating category: {category}")
            print(f"{'='*50}")
            
            try:
                results = self.prompt_evaluator.evaluate_category(category, models_to_test)
                if "error" not in results:
                    all_results.append(results)
                    
                    # Generate report for this category
                    report_path = self.prompt_evaluator.generate_evaluation_report(
                        results, f"prompt_eval_{category}_{int(time.time())}.html"
                    )
                    
                    print(f"\nCategory '{category}' evaluation completed.")
                    print(f"Report saved to: {report_path}")
                    
                    # Display summary
                    if "summary_stats" in results:
                        self._display_evaluation_summary(results["summary_stats"])
                else:
                    print(f"Error evaluating category '{category}': {results['error']}")
                    
            except Exception as e:
                print(f"Error evaluating category '{category}': {e}")
        
        # Optionally generate combined report
        if len(all_results) > 1:
            print(f"\nGenerate combined report for all {len(all_results)} categories? (y/N): ", end="")
            if input().strip().lower() == 'y':
                combined_results = {
                    "timestamp": datetime.now().isoformat(),
                    "categories": all_results,
                    "summary": "Combined evaluation across multiple categories"
                }
                combined_path = self.prompt_evaluator.generate_evaluation_report(
                    combined_results, f"prompt_eval_combined_{int(time.time())}.html"
                )
                print(f"Combined report saved to: {combined_path}")
    
    def _display_evaluation_summary(self, stats):
        """Display a summary of evaluation statistics."""
        print(f"\n--- Summary Statistics ---")
        print(f"Total questions: {stats.get('total_questions', 0)}")
        
        for model, model_stats in stats.get("model_averages", {}).items():
            print(f"\n{model}:")
            for temp_label, temp_stats in model_stats.items():
                temp_name = "Zero Temperature" if temp_label == "zero_temp" else "Normal Temperature"
                avg_score = temp_stats.get("average_score", 0)
                print(f"  {temp_name}: {avg_score}/100 average score")
    
        
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
                choice = input("Select option (1-5, q): ").strip()
                
                if choice == "1":
                    self.run_email_pipeline()
                elif choice == "2":
                    self.run_web_pipeline()
                elif choice == "3":
                    self.run_prompt_pipeline()
                elif choice == "4":
                    self.run_evaluation_pipeline()
                elif choice == "5":
                    self.show_configuration()
                elif choice.lower() == "q":
                    print("Goodbye!")
                    break
                else:
                    print("Invalid choice. Please select 1-6.")
                    
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