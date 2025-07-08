"""
Evaluation Pipeline for LLM Summary Evaluation Tool.

This module handles running content through multiple LLM models and generating comparison reports.
"""

import time
import webbrowser
from datetime import datetime
from typing import List, Tuple, Dict, Any
from pathlib import Path

import ollama
from openai import OpenAI

from core.models import ModelManager
from core.output import OutputGenerator


class Evaluator:
    """Main evaluation pipeline for processing content through multiple LLMs."""
    
    def __init__(self, settings):
        self.settings = settings
        self.model_manager = ModelManager(settings)
        self.output_generator = OutputGenerator(settings)
        
    def process_articles(self, articles: List[Tuple[str, str]]):
        """
        Process articles extracted from emails.
        articles: List of (title, url) tuples
        """
        from pipelines.web_fetcher import WebFetcher
        
        fetcher = WebFetcher(self.settings)
        
        for i, (title, url) in enumerate(articles, 1):
            print(f"\\n{'='*60}")
            print(f"Processing Article {i}/{len(articles)}: {title}")
            print(f"URL: {url}")
            print('='*60)
            
            # Fetch content
            content = fetcher.fetch_content(url)
            if not content:
                print(f"Skipping article due to fetch failure: {title}")
                continue
                
            # Process through evaluation
            self._evaluate_content(content, title, url)
            
    def process_content(self, content: str, source: str = None):
        """
        Process arbitrary content through evaluation pipeline.
        """
        print(f"\\n{'='*60}")
        print(f"Processing Content from: {source or 'Direct Input'}")
        print('='*60)
        
        self._evaluate_content(content, source=source)
        
    def process_prompt(self, prompt: str):
        """
        Process a direct prompt/question through evaluation pipeline.
        """
        print(f"\\n{'='*60}")
        print(f"Processing Prompt: {prompt[:50]}...")
        print('='*60)
        
        self._evaluate_prompt(prompt)
        
    def _evaluate_content(self, content: str, title: str = None, source: str = None):
        """
        Run content through all configured models and generate comparison report.
        """
        print(f"Content length: {len(content)} characters")
        print(f"Running evaluation with {len(self.settings.models)} models...")
        
        # Collect results from all models
        all_results = []
        
        for model in self.settings.models:
            print(f"\\nProcessing with model: {model}")
            repetitions = self.settings.get_repetitions(model)
            
            model_results = self._run_model_evaluation(
                content, model, repetitions, 
                self.settings.system_prompt, 
                self.settings.user_prompt
            )
            all_results.append(model_results)
            
        # Generate HTML report
        self._generate_report(all_results, title, source, content)
        
    def _evaluate_prompt(self, prompt: str):
        """
        Run a prompt/question through all configured models.
        """
        print(f"Running prompt evaluation with {len(self.settings.models)} models...")
        
        all_results = []
        
        for model in self.settings.models:
            print(f"\\nProcessing with model: {model}")
            repetitions = self.settings.get_repetitions(model)
            
            # For prompts, use the prompt as both system and user context
            model_results = self._run_model_evaluation(
                prompt, model, repetitions,
                self.settings.system_prompt,
                prompt  # Use the prompt directly as user input
            )
            all_results.append(model_results)
            
        # Generate HTML report for prompt
        self._generate_report(all_results, title="Direct Prompt", source=prompt[:100])
        
    def _run_model_evaluation(self, content: str, model: str, repetitions: int, 
                            system_prompt: str, user_prompt: str) -> List[str]:
        """
        Run content through a specific model multiple times.
        Returns list: [model_name, result1, result2, result3, ...]
        """
        model_results = [model]
        total_time = 0
        
        # Pre-load model if it's an Ollama model
        if not self.settings.is_openai_model(model):
            try:
                print("Pre-loading model...")
                ollama.chat(
                    model=model, 
                    messages=[{"role": "system", "content": ""}, {"role": "user", "content": ""}], 
                    keep_alive="30s"
                )
            except Exception as e:
                print(f"Warning: Could not pre-load model {model}: {e}")
                
        # Run evaluations
        for i in range(repetitions):
            print(f"  Run {i+1}/{repetitions}...")
            start_time = time.time()
            
            try:
                result = self.model_manager.get_completion(
                    content, model, system_prompt, user_prompt
                )
                elapsed = time.time() - start_time
                total_time += elapsed
                
                # Format result with timing
                formatted_result = f"{result}<br>(Time: {elapsed:.2f}s)"
                model_results.append(formatted_result)
                
            except Exception as e:
                print(f"  Error in run {i+1}: {e}")
                model_results.append(f"Error: {str(e)}")
                
        # Pad with empty results if needed (for table formatting)
        while len(model_results) < 4:  # model + 3 results
            model_results.append("")
            
        # Print summary
        avg_time = total_time / repetitions if repetitions > 0 else 0
        print(f"  Average time: {avg_time:.2f}s, Total: {total_time:.2f}s")
        
        return model_results
        
    def _generate_report(self, all_results: List[List[str]], title: str = None, 
                        source: str = None, content: str = None):
        """
        Generate and display HTML comparison report.
        """
        # Generate basic HTML table
        html_content = self.output_generator.generate_html_table(
            all_results, title, source, 
            self.settings.system_prompt, 
            self.settings.user_prompt
        )
        
        # Apply difference highlighting
        highlighted_html = self.output_generator.highlight_differences(html_content)
        
        # Save to timestamped file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"summary_table_{timestamp}.highlighted.html"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(highlighted_html)
                
            print(f"\\nReport saved to: {filename}")
            
            # Open in browser
            file_path = Path(filename).absolute()
            webbrowser.open(f"file://{file_path}")
            print("Report opened in browser.")
            
        except Exception as e:
            print(f"Error saving report: {e}")
            
    def run_batch_evaluation(self, contents: List[Tuple[str, str]]):
        """
        Run batch evaluation on multiple content items.
        contents: List of (content, description) tuples
        """
        print(f"\\nStarting batch evaluation of {len(contents)} items...")
        
        for i, (content, description) in enumerate(contents, 1):
            print(f"\\n{'='*80}")
            print(f"Batch Item {i}/{len(contents)}: {description}")
            print('='*80)
            
            self._evaluate_content(content, source=description)