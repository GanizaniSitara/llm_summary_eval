"""
Prompt Evaluation Pipeline for LLM Summary Evaluation Tool.

This module provides functionality for evaluating LLMs using pre-saved question/answer pairs
with dual temperature testing and both analytical and AI-based scoring.
"""

import json
import time
import difflib
from typing import Dict, List, Any, Tuple
from datetime import datetime
from pathlib import Path

# Import core modules
from core.models import ModelManager
from core.output import OutputGenerator


class PromptEvaluator:
    """Evaluates LLM responses against expected answers using multiple scoring methods."""
    
    def __init__(self, settings):
        self.settings = settings
        self.model_manager = ModelManager(settings)
        self.output_generator = OutputGenerator(settings)
        self.question_bank = self._load_question_bank()
        
    def _load_question_bank(self) -> Dict[str, List[Dict]]:
        """Load questions from the question bank JSON file."""
        try:
            question_bank_path = Path(self.settings.question_bank_path)
            if not question_bank_path.exists():
                print(f"Warning: Question bank not found at {question_bank_path}")
                return {}
                
            with open(question_bank_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading question bank: {e}")
            return {}
    
    def get_available_categories(self) -> List[str]:
        """Get list of available question categories."""
        return list(self.question_bank.keys())
    
    def get_questions_by_category(self, category: str) -> List[Dict]:
        """Get questions for a specific category."""
        return self.question_bank.get(category, [])
    
    def evaluate_single_question(self, question_data: Dict, models: List[str]) -> Dict[str, Any]:
        """
        Evaluate a single question against multiple models with dual temperature testing.
        
        Args:
            question_data: Dictionary containing question, expected_answer, etc.
            models: List of model names to test
            
        Returns:
            Dictionary containing all evaluation results
        """
        question = question_data["question"]
        expected_answer = question_data["expected_answer"]
        question_id = question_data.get("id", "unknown")
        
        print(f"\n--- Evaluating Question: {question_id} ---")
        print(f"Question: {question}")
        print(f"Expected: {expected_answer}")
        
        results = {
            "question_data": question_data,
            "model_results": {},
            "timestamp": datetime.now().isoformat(),
            "analytical_scores": {},
            "ai_evaluation_scores": {}
        }
        
        # Test each model at both temperatures
        for model in models:
            print(f"\nTesting model: {model}")
            model_results = {"responses": {}, "timings": {}}
            
            for temp in self.settings.evaluation_temperatures:
                temp_label = "zero_temp" if temp == 0.0 else "normal_temp"
                print(f"  Temperature {temp}...")
                
                start_time = time.time()
                
                # Get response from model
                try:
                    response = self.model_manager.generate_response(
                        model=model,
                        system_prompt="You are a helpful assistant. Answer the question directly and concisely.",
                        user_prompt=question,
                        temperature=temp
                    )
                    
                    execution_time = time.time() - start_time
                    
                    model_results["responses"][temp_label] = response
                    model_results["timings"][temp_label] = execution_time
                    
                    print(f"    Response: {response[:100]}...")
                    
                except Exception as e:
                    print(f"    Error: {e}")
                    model_results["responses"][temp_label] = f"ERROR: {str(e)}"
                    model_results["timings"][temp_label] = 0
            
            results["model_results"][model] = model_results
            
            # Calculate analytical scores for this model
            results["analytical_scores"][model] = self._calculate_analytical_scores(
                expected_answer, model_results["responses"]
            )
        
        # Perform AI-based evaluation
        results["ai_evaluation_scores"] = self._perform_ai_evaluation(
            question_data, results["model_results"]
        )
        
        return results
    
    def _calculate_analytical_scores(self, expected: str, responses: Dict[str, str]) -> Dict[str, Any]:
        """Calculate analytical similarity scores between expected and actual responses."""
        scores = {}
        
        for temp_label, response in responses.items():
            if response.startswith("ERROR:"):
                scores[temp_label] = {
                    "word_similarity": 0.0,
                    "char_similarity": 0.0,
                    "length_ratio": 0.0,
                    "exact_match": False
                }
                continue
            
            # Word-level similarity using difflib
            expected_words = expected.lower().split()
            response_words = response.lower().split()
            
            word_similarity = difflib.SequenceMatcher(
                None, expected_words, response_words
            ).ratio()
            
            # Character-level similarity
            char_similarity = difflib.SequenceMatcher(
                None, expected.lower(), response.lower()
            ).ratio()
            
            # Length ratio
            length_ratio = min(len(response), len(expected)) / max(len(response), len(expected))
            
            # Exact match (case insensitive)
            exact_match = expected.lower().strip() == response.lower().strip()
            
            scores[temp_label] = {
                "word_similarity": round(word_similarity, 3),
                "char_similarity": round(char_similarity, 3),
                "length_ratio": round(length_ratio, 3),
                "exact_match": exact_match
            }
        
        return scores
    
    def _perform_ai_evaluation(self, question_data: Dict, model_results: Dict) -> Dict[str, Any]:
        """Use gemma3 model to evaluate response quality against expected answers."""
        evaluation_scores = {}
        
        # Check if evaluation model is available
        if not self.model_manager.is_model_available(self.settings.evaluation_model):
            print(f"Warning: Evaluation model {self.settings.evaluation_model} not available")
            return {"error": "Evaluation model not available"}
        
        question = question_data["question"]
        expected = question_data["expected_answer"]
        criteria = question_data.get("scoring_criteria", "General accuracy and relevance")
        
        for model_name, results in model_results.items():
            model_scores = {}
            
            for temp_label, response in results["responses"].items():
                if response.startswith("ERROR:"):
                    model_scores[temp_label] = {"score": 0, "reasoning": "Error in response generation"}
                    continue
                
                # Create evaluation prompt
                eval_prompt = f"""
Evaluate the following AI response against the expected answer.

Question: {question}
Expected Answer: {expected}
AI Response: {response}

Scoring Criteria: {criteria}

Please provide:
1. A score from 0-100 (where 100 is perfect match to expected answer)
2. Brief reasoning for the score

Format your response as:
Score: [number]
Reasoning: [explanation]
"""
                
                try:
                    evaluation = self.model_manager.generate_response(
                        model=self.settings.evaluation_model,
                        system_prompt="You are an expert evaluator. Provide objective, consistent scoring.",
                        user_prompt=eval_prompt,
                        temperature=0.0  # Use zero temperature for consistent evaluation
                    )
                    
                    # Parse score and reasoning
                    score, reasoning = self._parse_evaluation_response(evaluation)
                    model_scores[temp_label] = {"score": score, "reasoning": reasoning}
                    
                except Exception as e:
                    print(f"Error in AI evaluation: {e}")
                    model_scores[temp_label] = {"score": 0, "reasoning": f"Evaluation error: {str(e)}"}
            
            evaluation_scores[model_name] = model_scores
        
        return evaluation_scores
    
    def _parse_evaluation_response(self, evaluation: str) -> Tuple[int, str]:
        """Parse the AI evaluation response to extract score and reasoning."""
        try:
            lines = evaluation.strip().split('\n')
            score = 0
            reasoning = "No reasoning provided"
            
            for line in lines:
                if line.startswith('Score:'):
                    score_text = line.replace('Score:', '').strip()
                    # Extract just the number
                    score = int(''.join(filter(str.isdigit, score_text)))
                elif line.startswith('Reasoning:'):
                    reasoning = line.replace('Reasoning:', '').strip()
            
            # Ensure score is within bounds
            score = max(0, min(100, score))
            
            return score, reasoning
            
        except Exception as e:
            print(f"Error parsing evaluation: {e}")
            return 0, f"Parse error: {str(e)}"
    
    def evaluate_category(self, category: str, models: List[str]) -> Dict[str, Any]:
        """Evaluate all questions in a category against specified models."""
        questions = self.get_questions_by_category(category)
        if not questions:
            return {"error": f"No questions found in category: {category}"}
        
        print(f"\n=== Evaluating Category: {category} ===")
        print(f"Questions: {len(questions)}")
        print(f"Models: {', '.join(models)}")
        
        category_results = {
            "category": category,
            "timestamp": datetime.now().isoformat(),
            "models": models,
            "question_results": [],
            "summary_stats": {}
        }
        
        # Evaluate each question
        for question_data in questions:
            result = self.evaluate_single_question(question_data, models)
            category_results["question_results"].append(result)
        
        # Calculate summary statistics
        category_results["summary_stats"] = self._calculate_category_stats(
            category_results["question_results"]
        )
        
        return category_results
    
    def _calculate_category_stats(self, question_results: List[Dict]) -> Dict[str, Any]:
        """Calculate summary statistics for a category evaluation."""
        stats = {
            "total_questions": len(question_results),
            "model_averages": {},
            "temperature_comparison": {}
        }
        
        # Aggregate scores by model and temperature
        model_scores = {}
        
        for result in question_results:
            for model, ai_scores in result.get("ai_evaluation_scores", {}).items():
                if model not in model_scores:
                    model_scores[model] = {"zero_temp": [], "normal_temp": []}
                
                for temp_label, score_data in ai_scores.items():
                    if isinstance(score_data, dict) and "score" in score_data:
                        model_scores[model][temp_label].append(score_data["score"])
        
        # Calculate averages
        for model, temps in model_scores.items():
            stats["model_averages"][model] = {}
            for temp_label, scores in temps.items():
                if scores:
                    stats["model_averages"][model][temp_label] = {
                        "average_score": round(sum(scores) / len(scores), 1),
                        "min_score": min(scores),
                        "max_score": max(scores),
                        "total_questions": len(scores)
                    }
        
        return stats
    
    def generate_evaluation_report(self, evaluation_results: Dict, output_filename: str = None) -> str:
        """Generate HTML report for prompt evaluation results."""
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"prompt_evaluation_{timestamp}.html"
        
        # Use the existing output generator with custom template for prompt evaluation
        html_content = self._create_evaluation_html(evaluation_results)
        
        output_path = Path(output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\nEvaluation report saved to: {output_path.absolute()}")
        return str(output_path.absolute())
    
    def _create_evaluation_html(self, results: Dict) -> str:
        """Create HTML content for evaluation results."""
        # This is a simplified version - would be enhanced based on OutputGenerator patterns
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Prompt Evaluation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 10px; margin-bottom: 20px; }}
        .question {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; }}
        .model-result {{ margin: 10px 0; padding: 10px; background-color: #f9f9f9; }}
        .score {{ font-weight: bold; color: #007acc; }}
        .temperature {{ margin: 5px 0; padding: 5px; background-color: #fff; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Prompt Evaluation Report</h1>
        <p>Generated: {results.get('timestamp', 'Unknown')}</p>
        <p>Category: {results.get('category', 'Unknown')}</p>
    </div>
"""
        
        # Add summary statistics
        if "summary_stats" in results:
            html += "<h2>Summary Statistics</h2>"
            stats = results["summary_stats"]
            
            html += "<table>"
            html += "<tr><th>Model</th><th>Temperature</th><th>Average Score</th><th>Min/Max</th><th>Questions</th></tr>"
            
            for model, model_stats in stats.get("model_averages", {}).items():
                for temp_label, temp_stats in model_stats.items():
                    temp_display = "0.0 (Zero)" if temp_label == "zero_temp" else "0.8 (Normal)"
                    html += f"""
                    <tr>
                        <td>{model}</td>
                        <td>{temp_display}</td>
                        <td class="score">{temp_stats['average_score']}</td>
                        <td>{temp_stats['min_score']}-{temp_stats['max_score']}</td>
                        <td>{temp_stats['total_questions']}</td>
                    </tr>
                    """
            html += "</table>"
        
        # Add individual question results
        html += "<h2>Individual Question Results</h2>"
        
        for i, question_result in enumerate(results.get("question_results", []), 1):
            question_data = question_result["question_data"]
            html += f"""
            <div class="question">
                <h3>Question {i}: {question_data.get('id', 'Unknown')}</h3>
                <p><strong>Question:</strong> {question_data['question']}</p>
                <p><strong>Expected Answer:</strong> {question_data['expected_answer']}</p>
                <p><strong>Category:</strong> {question_data.get('category', 'Unknown')}</p>
            """
            
            # Model results
            for model, model_data in question_result.get("model_results", {}).items():
                html += f'<div class="model-result"><h4>{model}</h4>'
                
                for temp_label, response in model_data.get("responses", {}).items():
                    temp_display = "Temperature 0.0 (Zero)" if temp_label == "zero_temp" else "Temperature 0.8 (Normal)"
                    timing = model_data.get("timings", {}).get(temp_label, 0)
                    
                    # Get AI evaluation score
                    ai_score = question_result.get("ai_evaluation_scores", {}).get(model, {}).get(temp_label, {})
                    score = ai_score.get("score", "N/A")
                    reasoning = ai_score.get("reasoning", "No reasoning available")
                    
                    # Get analytical scores
                    analytical = question_result.get("analytical_scores", {}).get(model, {}).get(temp_label, {})
                    
                    html += f"""
                    <div class="temperature">
                        <h5>{temp_display}</h5>
                        <p><strong>Response:</strong> {response}</p>
                        <p><strong>AI Evaluation Score:</strong> <span class="score">{score}/100</span></p>
                        <p><strong>Reasoning:</strong> {reasoning}</p>
                        <p><strong>Analytical Scores:</strong> 
                           Word Similarity: {analytical.get('word_similarity', 'N/A')}, 
                           Char Similarity: {analytical.get('char_similarity', 'N/A')}, 
                           Exact Match: {analytical.get('exact_match', 'N/A')}
                        </p>
                        <p><strong>Execution Time:</strong> {timing:.2f}s</p>
                    </div>
                    """
                
                html += '</div>'
            
            html += '</div>'
        
        html += """
</body>
</html>
"""
        return html