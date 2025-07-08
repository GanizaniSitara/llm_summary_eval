"""
Configuration management for LLM Summary Evaluation Tool.
"""

import os
from typing import List, Dict, Any


class Settings:
    """Centralized configuration management."""
    
    def __init__(self):
        self.load_default_settings()
        
    def load_default_settings(self):
        """Load default configuration settings."""
        # Model configuration
        self.models = [
            "gpt-4o-mini-2024-07-18",  # OpenAI model (runs once)
            # Add more models as needed
        ]
        
        # Model parameters
        self.temperature = 0.8
        self.openai_models = {"gpt-4o-mini-2024-07-18"}
        
        # Prompts
        self.system_prompt = "You are a summarization assistant."
        self.user_prompt = "Provide once sentence summary of the text. Start the sentence with a verb like describes, explains or similar. TEXT START:\\n\\n"
        
        # File paths
        self.db_path = r'C:\\Users\\admin\\AppData\\Local\\OEClassic\\User\\Main Identity\\00_Medium.db'
        self.mbx_path = r'C:\\Users\\admin\\AppData\\Local\\OEClassic\\User\\Main Identity\\00_Medium.mbx'
        self.csv_path = 'extracted_articles.csv'
        self.urls_file = 'urls.txt'
        
        # Processing settings
        self.mail_start_row = 44
        self.mail_num_records = 1
        self.repetitions = 3  # For non-OpenAI models
        
        # Alternative prompt sets for evaluation
        self.prompt_sets = {
            "product_vision": [
                "Rate the relevance of the provided document to **documenting product vision** on a scale of 0 to 100...",
                # Add more prompts as needed
            ],
            "product_roadmap": [
                "Rate the relevance of the provided document to **documenting a product roadmap** on a scale of 0 to 100...",
                # Add more prompts as needed
            ],
            "architecture_vision": [
                "Rate how well the document conveys an **architecture vision** on a scale from 0 to 100...",
                # Add more prompts as needed
            ],
            "service_vision": [
                "Rate the provided document's relevance to defining a **service vision** from 0 to 100...",
                # Add more prompts as needed
            ],
            "security_vision": [
                "Rate the document's relevance in defining a **security vision** from 0 to 100...",
                # Add more prompts as needed
            ],
            "lean_test_strategy": [
                "Rate how well the document defines a **lean test strategy** from 0 to 100...",
                # Add more prompts as needed
            ]
        }
        
    def display_settings(self):
        """Display current configuration settings."""
        print("\\n--- Current Settings ---")
        print(f"Models: {self.models}")
        print(f"Temperature: {self.temperature}")
        print(f"System Prompt: {self.system_prompt}")
        print(f"User Prompt: {self.user_prompt[:50]}...")
        print(f"Email Archive Path: {self.mbx_path}")
        print(f"URLs File: {self.urls_file}")
        print(f"CSV Output: {self.csv_path}")
        
    def modify_models(self):
        """Interactive model configuration."""
        print("\\n--- Model Configuration ---")
        print("Current models:")
        for i, model in enumerate(self.models, 1):
            print(f"{i}. {model}")
            
        print("\\nOptions:")
        print("1. Add model")
        print("2. Remove model")
        print("3. Back")
        
        choice = input("Select option: ").strip()
        
        if choice == "1":
            new_model = input("Enter model name: ").strip()
            if new_model and new_model not in self.models:
                self.models.append(new_model)
                print(f"Added model: {new_model}")
        elif choice == "2":
            try:
                index = int(input("Enter model number to remove: ")) - 1
                if 0 <= index < len(self.models):
                    removed = self.models.pop(index)
                    print(f"Removed model: {removed}")
                else:
                    print("Invalid model number.")
            except ValueError:
                print("Please enter a valid number.")
                
    def modify_paths(self):
        """Interactive path configuration."""
        print("\\n--- Path Configuration ---")
        print("1. Email Archive Path")
        print("2. URLs File Path")
        print("3. CSV Output Path")
        print("4. Back")
        
        choice = input("Select option: ").strip()
        
        if choice == "1":
            new_path = input(f"Current: {self.mbx_path}\\nNew path: ").strip()
            if new_path:
                self.mbx_path = new_path
                print("Email archive path updated.")
        elif choice == "2":
            new_path = input(f"Current: {self.urls_file}\\nNew path: ").strip()
            if new_path:
                self.urls_file = new_path
                print("URLs file path updated.")
        elif choice == "3":
            new_path = input(f"Current: {self.csv_path}\\nNew path: ").strip()
            if new_path:
                self.csv_path = new_path
                print("CSV output path updated.")
                
    def is_openai_model(self, model: str) -> bool:
        """Check if a model is an OpenAI model."""
        return model in self.openai_models
        
    def get_repetitions(self, model: str) -> int:
        """Get number of repetitions for a model."""
        return 1 if self.is_openai_model(model) else self.repetitions