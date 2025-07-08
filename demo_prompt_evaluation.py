#!/usr/bin/env python3
"""
Demo script to test the prompt evaluation system with mock models.
This demonstrates the functionality without requiring actual LLM APIs.
"""

import sys
import json
from unittest.mock import Mock
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

# Mock dependencies
sys.modules['ollama'] = Mock()
sys.modules['openai'] = Mock()
mock_sync_api = Mock()
sys.modules['playwright.sync_api'] = mock_sync_api
sys.modules['bs4'] = Mock()

from config.settings import Settings
from pipelines.prompt_evaluator import PromptEvaluator

class DemoModelManager:
    """Demo model manager with realistic responses."""
    
    def __init__(self, settings):
        self.settings = settings
        
    def generate_response(self, model, system_prompt, user_prompt, temperature):
        """Generate demo responses based on the question."""
        # Create different responses based on temperature and question
        responses = {
            "What is 2 + 2?": {
                0.0: "4",
                0.8: "The answer is 4."
            },
            "What is the capital of France?": {
                0.0: "Paris",
                0.8: "Paris is the capital of France."
            },
            "Complete this sentence: The quick brown fox jumps over the...": {
                0.0: "lazy dog",
                0.8: "lazy dog. This is a famous pangram sentence!"
            },
            "What does API stand for?": {
                0.0: "Application Programming Interface",
                0.8: "API stands for Application Programming Interface, which is a way for different software applications to communicate with each other."
            }
        }
        
        # Find matching question
        for question, temps in responses.items():
            if question.lower() in user_prompt.lower():
                return temps.get(temperature, f"Demo response for {model} at temp {temperature}")
        
        # Default response
        if temperature == 0.0:
            return "This is a consistent response."
        else:
            return "This is a more creative and varied response with additional details!"
    
    def is_model_available(self, model):
        """Mock model availability."""
        return model in ["demo_model", "gemma3:27b-it-q4_K_M"]

def demo_single_question():
    """Demo evaluating a single question."""
    print("=== Demo: Single Question Evaluation ===\n")
    
    # Setup
    settings = Settings()
    settings.models = ["demo_model"]
    settings.evaluation_model = "gemma3:27b-it-q4_K_M"
    
    # Mock the model manager
    evaluator = PromptEvaluator(settings)
    evaluator.model_manager = DemoModelManager(settings)
    
    # Mock AI evaluation
    def mock_ai_evaluation(question_data, model_results):
        return {
            "demo_model": {
                "zero_temp": {"score": 95, "reasoning": "Excellent exact match to expected answer"},
                "normal_temp": {"score": 88, "reasoning": "Good answer with additional context"}
            }
        }
    evaluator._perform_ai_evaluation = mock_ai_evaluation
    
    # Test question
    question_data = {
        "id": "demo_001",
        "question": "What is 2 + 2?",
        "expected_answer": "4",
        "category": "arithmetic",
        "scoring_criteria": "Exact numerical match required",
        "difficulty": "easy"
    }
    
    # Evaluate
    result = evaluator.evaluate_single_question(question_data, ["demo_model"])
    
    # Display results
    print(f"Question: {question_data['question']}")
    print(f"Expected: {question_data['expected_answer']}")
    print()
    
    model_result = result["model_results"]["demo_model"]
    analytical = result["analytical_scores"]["demo_model"]
    ai_scores = result["ai_evaluation_scores"]["demo_model"]
    
    print("Results:")
    print("--------")
    
    for temp_label in ["zero_temp", "normal_temp"]:
        temp_name = "Temperature 0.0" if temp_label == "zero_temp" else "Temperature 0.8"
        response = model_result["responses"][temp_label]
        timing = model_result["timings"][temp_label]
        
        analytical_score = analytical[temp_label]
        ai_score = ai_scores[temp_label]
        
        print(f"\n{temp_name}:")
        print(f"  Response: '{response}'")
        print(f"  Execution Time: {timing:.3f}s")
        print(f"  Word Similarity: {analytical_score['word_similarity']}")
        print(f"  Character Similarity: {analytical_score['char_similarity']}")
        print(f"  Exact Match: {analytical_score['exact_match']}")
        print(f"  AI Score: {ai_score['score']}/100")
        print(f"  AI Reasoning: {ai_score['reasoning']}")

def demo_category_evaluation():
    """Demo evaluating a category of questions."""
    print("\n\n=== Demo: Category Evaluation ===\n")
    
    # Setup
    settings = Settings()
    settings.models = ["demo_model"]
    settings.evaluation_model = "gemma3:27b-it-q4_K_M"
    
    evaluator = PromptEvaluator(settings)
    evaluator.model_manager = DemoModelManager(settings)
    
    # Mock AI evaluation for all questions
    def mock_ai_evaluation(question_data, model_results):
        # Different scores based on question difficulty
        scores = {
            "easy": {"zero_temp": 95, "normal_temp": 88},
            "medium": {"zero_temp": 85, "normal_temp": 82},
            "hard": {"zero_temp": 75, "normal_temp": 78}
        }
        
        difficulty = question_data.get("difficulty", "medium")
        question_scores = scores.get(difficulty, scores["medium"])
        
        return {
            "demo_model": {
                "zero_temp": {
                    "score": question_scores["zero_temp"], 
                    "reasoning": f"Good answer for {difficulty} question"
                },
                "normal_temp": {
                    "score": question_scores["normal_temp"], 
                    "reasoning": f"Creative response for {difficulty} question"
                }
            }
        }
    evaluator._perform_ai_evaluation = mock_ai_evaluation
    
    # Evaluate basic reasoning category
    category = "basic_reasoning"
    questions = evaluator.get_questions_by_category(category)
    
    print(f"Evaluating category: {category}")
    print(f"Number of questions: {len(questions)}")
    print()
    
    # Process first 2 questions for demo
    demo_questions = questions[:2]
    results = {
        "category": category,
        "question_results": [],
        "summary_stats": {}
    }
    
    for question_data in demo_questions:
        print(f"Processing: {question_data['question'][:50]}...")
        result = evaluator.evaluate_single_question(question_data, ["demo_model"])
        results["question_results"].append(result)
    
    # Calculate summary stats
    results["summary_stats"] = evaluator._calculate_category_stats(results["question_results"])
    
    # Display summary
    print("\nSummary Statistics:")
    print("------------------")
    stats = results["summary_stats"]
    print(f"Total Questions: {stats['total_questions']}")
    
    for model, model_stats in stats["model_averages"].items():
        print(f"\n{model}:")
        for temp_label, temp_stats in model_stats.items():
            temp_name = "Zero Temperature" if temp_label == "zero_temp" else "Normal Temperature"
            print(f"  {temp_name}: {temp_stats['average_score']}/100 average")

def demo_html_generation():
    """Demo HTML report generation."""
    print("\n\n=== Demo: HTML Report Generation ===\n")
    
    # Create mock results
    mock_results = {
        "category": "demo_category",
        "timestamp": "2023-01-01T12:00:00",
        "models": ["demo_model"],
        "summary_stats": {
            "total_questions": 2,
            "model_averages": {
                "demo_model": {
                    "zero_temp": {"average_score": 90.0, "min_score": 85, "max_score": 95, "total_questions": 2},
                    "normal_temp": {"average_score": 85.0, "min_score": 82, "max_score": 88, "total_questions": 2}
                }
            }
        },
        "question_results": [
            {
                "question_data": {
                    "id": "demo_001",
                    "question": "What is 2 + 2?",
                    "expected_answer": "4",
                    "category": "arithmetic"
                },
                "model_results": {
                    "demo_model": {
                        "responses": {"zero_temp": "4", "normal_temp": "The answer is 4."},
                        "timings": {"zero_temp": 0.123, "normal_temp": 0.156}
                    }
                },
                "analytical_scores": {
                    "demo_model": {
                        "zero_temp": {"word_similarity": 1.0, "char_similarity": 1.0, "exact_match": True},
                        "normal_temp": {"word_similarity": 0.8, "char_similarity": 0.6, "exact_match": False}
                    }
                },
                "ai_evaluation_scores": {
                    "demo_model": {
                        "zero_temp": {"score": 95, "reasoning": "Perfect exact match"},
                        "normal_temp": {"score": 88, "reasoning": "Good answer with context"}
                    }
                }
            }
        ]
    }
    
    settings = Settings()
    evaluator = PromptEvaluator(settings)
    
    # Generate HTML
    html_content = evaluator._create_evaluation_html(mock_results)
    
    # Save to file
    output_file = "demo_report.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"HTML report generated: {output_file}")
    print(f"Report size: {len(html_content):,} characters")
    print("✅ HTML generation successful")

def main():
    """Run all demos."""
    print("🚀 LLM Prompt Evaluation System Demo")
    print("=" * 50)
    
    try:
        demo_single_question()
        demo_category_evaluation()
        demo_html_generation()
        
        print("\n" + "=" * 50)
        print("🎉 All demos completed successfully!")
        print("The prompt evaluation system is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)