"""
Model Management for LLM Summary Evaluation Tool.

This module handles interactions with different LLM APIs (Ollama, OpenAI).
"""

import ollama
from openai import OpenAI
from typing import Optional


class ModelManager:
    """Manages interactions with different LLM models and APIs."""
    
    def __init__(self, settings):
        self.settings = settings
        self.openai_client = None
        
    def get_completion(self, text: str, model: str, system_prompt: str, user_prompt: str) -> str:
        """
        Get completion from the specified model.
        
        Args:
            text: The content to process
            model: Model identifier
            system_prompt: System prompt for the model
            user_prompt: User prompt template
            
        Returns:
            Model response text
        """
        if self.settings.is_openai_model(model):
            return self._get_openai_completion(text, model, system_prompt, user_prompt)
        else:
            return self._get_ollama_completion(text, model, system_prompt, user_prompt)
            
    def _get_openai_completion(self, text: str, model: str, system_prompt: str, user_prompt: str) -> str:
        """Get completion from OpenAI API."""
        try:
            if not self.openai_client:
                self.openai_client = OpenAI()
                
            completion = self.openai_client.chat.completions.create(
                model=model,
                temperature=self.settings.temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{user_prompt}\\n\\n{text}"}
                ]
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            error_msg = f"OpenAI API Error: {str(e)}"
            print(f"  {error_msg}")
            return error_msg
            
    def _get_ollama_completion(self, text: str, model: str, system_prompt: str, user_prompt: str) -> str:
        """Get completion from Ollama API."""
        try:
            response = ollama.chat(
                model=model,
                options={'temperature': self.settings.temperature},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{user_prompt}\\n\\n{text}"}
                ]
            )
            
            return response['message']['content']
            
        except Exception as e:
            error_msg = f"Ollama Error: {str(e)}"
            print(f"  {error_msg}")
            return error_msg
            
    def test_model_availability(self, model: str) -> bool:
        """
        Test if a model is available and responding.
        
        Args:
            model: Model identifier
            
        Returns:
            True if model is available, False otherwise
        """
        try:
            test_prompt = "Hello"
            result = self.get_completion(test_prompt, model, "You are a helpful assistant.", "Say hello.")
            return "error" not in result.lower()
            
        except Exception:
            return False
            
    def list_available_models(self) -> dict:
        """
        Get lists of available models by type.
        
        Returns:
            Dictionary with 'ollama' and 'openai' model lists
        """
        available = {
            'ollama': [],
            'openai': ['gpt-4o-mini-2024-07-18', 'gpt-4', 'gpt-3.5-turbo']  # Common OpenAI models
        }
        
        # Check Ollama models
        try:
            ollama_models = ollama.list()
            available['ollama'] = [model['name'] for model in ollama_models.get('models', [])]
        except Exception as e:
            print(f"Could not list Ollama models: {e}")
            
        return available
        
    def validate_model_list(self, models: list) -> list:
        """
        Validate a list of models and return only available ones.
        
        Args:
            models: List of model identifiers
            
        Returns:
            List of validated, available models
        """
        available_models = self.list_available_models()
        all_available = available_models['ollama'] + available_models['openai']
        
        validated = []
        for model in models:
            if model in all_available:
                validated.append(model)
            else:
                print(f"Warning: Model '{model}' not found in available models")
                
        return validated