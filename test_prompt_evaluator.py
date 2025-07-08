#!/usr/bin/env python3
"""
Comprehensive test suite for the LLM Summary Evaluation Tool's prompt evaluation system.
Tests all code paths and functionality without requiring external dependencies.
"""

import sys
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, 'src')

# Mock external dependencies before any imports
mock_ollama = Mock()
mock_openai = Mock()
mock_openai.OpenAI = Mock()

# Create comprehensive mocks for playwright
mock_sync_playwright = Mock()
mock_timeout_error = Exception

mock_sync_api = Mock()
mock_sync_api.sync_playwright = mock_sync_playwright
mock_sync_api.TimeoutError = mock_timeout_error

mock_bs4 = Mock()
mock_bs4.BeautifulSoup = Mock()

sys.modules['ollama'] = mock_ollama
sys.modules['openai'] = mock_openai
sys.modules['playwright'] = Mock()
sys.modules['playwright.sync_api'] = mock_sync_api
sys.modules['bs4'] = mock_bs4

def test_question_bank_loading():
    """Test that the question bank JSON loads correctly."""
    print("Testing question bank loading...")
    
    try:
        with open('src/data/question_bank.json', 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, dict), "Question bank should be a dictionary"
        assert len(data) > 0, "Question bank should not be empty"
        
        for category, questions in data.items():
            assert isinstance(questions, list), f"Category {category} should be a list"
            assert len(questions) > 0, f"Category {category} should not be empty"
            
            for question in questions:
                required_fields = ['id', 'question', 'expected_answer', 'category', 'scoring_criteria']
                for field in required_fields:
                    assert field in question, f"Question missing required field: {field}"
        
        print(f"✅ Question bank loaded successfully with {len(data)} categories")
        return True
        
    except Exception as e:
        print(f"❌ Question bank loading failed: {e}")
        return False

def test_settings_configuration():
    """Test settings configuration loading."""
    print("Testing settings configuration...")
    
    try:
        from config.settings import Settings
        
        settings = Settings()
        
        # Check basic attributes
        assert hasattr(settings, 'evaluation_model'), "Missing evaluation_model"
        assert hasattr(settings, 'evaluation_temperatures'), "Missing evaluation_temperatures"
        assert hasattr(settings, 'question_bank_path'), "Missing question_bank_path"
        
        # Check evaluation temperatures
        assert len(settings.evaluation_temperatures) == 2, "Should have 2 temperature settings"
        assert 0.0 in settings.evaluation_temperatures, "Should include zero temperature"
        
        print("✅ Settings configuration loaded successfully")
        return True
        
    except Exception as e:
        print(f"❌ Settings configuration failed: {e}")
        return False

class MockModelManager:
    """Mock model manager for testing without dependencies."""
    
    def __init__(self, settings):
        self.settings = settings
        self.responses = {
            "test_model": {
                0.0: "This is a deterministic response",
                0.8: "This is a creative response with more variation!"
            }
        }
    
    def generate_response(self, model, system_prompt, user_prompt, temperature):
        """Mock response generation."""
        return self.responses.get(model, {}).get(temperature, f"Mock response for {model} at temp {temperature}")
    
    def is_model_available(self, model):
        """Mock model availability check."""
        return model in ["test_model", "gemma3:27b-it-q4_K_M"]

class MockOutputGenerator:
    """Mock output generator for testing."""
    
    def __init__(self, settings):
        self.settings = settings

def test_prompt_evaluator_initialization():
    """Test PromptEvaluator initialization without dependencies."""
    print("Testing PromptEvaluator initialization...")
    
    try:
        from config.settings import Settings
        
        # Mock the heavy imports
        with patch('pipelines.prompt_evaluator.ModelManager', MockModelManager):
            with patch('pipelines.prompt_evaluator.OutputGenerator', MockOutputGenerator):
                from pipelines.prompt_evaluator import PromptEvaluator
                
                settings = Settings()
                evaluator = PromptEvaluator(settings)
                
                # Test basic functionality
                categories = evaluator.get_available_categories()
                assert isinstance(categories, list), "Categories should be a list"
                assert len(categories) > 0, "Should have categories"
                
                # Test getting questions by category
                if categories:
                    questions = evaluator.get_questions_by_category(categories[0])
                    assert isinstance(questions, list), "Questions should be a list"
                
                print("✅ PromptEvaluator initialization successful")
                return True
                
    except Exception as e:
        print(f"❌ PromptEvaluator initialization failed: {e}")
        return False

def test_analytical_scoring():
    """Test analytical scoring methods."""
    print("Testing analytical scoring...")
    
    try:
        from config.settings import Settings
        
        with patch('pipelines.prompt_evaluator.ModelManager', MockModelManager):
            with patch('pipelines.prompt_evaluator.OutputGenerator', MockOutputGenerator):
                from pipelines.prompt_evaluator import PromptEvaluator
                
                settings = Settings()
                evaluator = PromptEvaluator(settings)
                
                # Test analytical scoring
                expected = "The capital of France is Paris"
                responses = {
                    "zero_temp": "Paris is the capital of France",
                    "normal_temp": "The capital of France is definitely Paris"
                }
                
                scores = evaluator._calculate_analytical_scores(expected, responses)
                
                assert isinstance(scores, dict), "Scores should be a dictionary"
                assert "zero_temp" in scores, "Should have zero_temp scores"
                assert "normal_temp" in scores, "Should have normal_temp scores"
                
                for temp_scores in scores.values():
                    assert "word_similarity" in temp_scores, "Should have word similarity"
                    assert "char_similarity" in temp_scores, "Should have char similarity"
                    assert "exact_match" in temp_scores, "Should have exact match"
                    assert "length_ratio" in temp_scores, "Should have length ratio"
                
                print("✅ Analytical scoring test successful")
                return True
                
    except Exception as e:
        print(f"❌ Analytical scoring test failed: {e}")
        return False

def test_evaluation_response_parsing():
    """Test parsing of AI evaluation responses."""
    print("Testing evaluation response parsing...")
    
    try:
        from config.settings import Settings
        
        with patch('pipelines.prompt_evaluator.ModelManager', MockModelManager):
            with patch('pipelines.prompt_evaluator.OutputGenerator', MockOutputGenerator):
                from pipelines.prompt_evaluator import PromptEvaluator
                
                settings = Settings()
                evaluator = PromptEvaluator(settings)
                
                # Test parsing well-formed response
                test_response = "Score: 85\nReasoning: Good answer but missing some details"
                score, reasoning = evaluator._parse_evaluation_response(test_response)
                
                assert score == 85, f"Expected score 85, got {score}"
                assert "missing some details" in reasoning, "Reasoning should be parsed correctly"
                
                # Test parsing malformed response
                bad_response = "This is not a proper evaluation"
                score, reasoning = evaluator._parse_evaluation_response(bad_response)
                
                assert score == 0, "Malformed response should return score 0"
                print(f"  Debug: reasoning = '{reasoning}'")
                assert "Parse error" in reasoning or "error" in reasoning.lower() or "No reasoning provided" in reasoning, "Should indicate parse error or no reasoning"
                
                print("✅ Evaluation response parsing test successful")
                return True
                
    except Exception as e:
        print(f"❌ Evaluation response parsing test failed: {e}")
        return False

def test_single_question_evaluation():
    """Test evaluating a single question."""
    print("Testing single question evaluation...")
    
    try:
        from config.settings import Settings
        
        with patch('pipelines.prompt_evaluator.ModelManager', MockModelManager):
            with patch('pipelines.prompt_evaluator.OutputGenerator', MockOutputGenerator):
                from pipelines.prompt_evaluator import PromptEvaluator
                
                settings = Settings()
                settings.models = ["test_model"]  # Use our mock model
                evaluator = PromptEvaluator(settings)
                
                # Mock the AI evaluation to avoid dependency
                def mock_ai_evaluation(question_data, model_results):
                    return {
                        "test_model": {
                            "zero_temp": {"score": 90, "reasoning": "Excellent response"},
                            "normal_temp": {"score": 85, "reasoning": "Good creative response"}
                        }
                    }
                
                evaluator._perform_ai_evaluation = mock_ai_evaluation
                
                # Test question
                question_data = {
                    "id": "test_001",
                    "question": "What is 2+2?",
                    "expected_answer": "4",
                    "category": "arithmetic",
                    "scoring_criteria": "Exact match required"
                }
                
                result = evaluator.evaluate_single_question(question_data, ["test_model"])
                
                # Validate result structure
                assert "question_data" in result, "Should have question_data"
                assert "model_results" in result, "Should have model_results"
                assert "analytical_scores" in result, "Should have analytical_scores"
                assert "ai_evaluation_scores" in result, "Should have ai_evaluation_scores"
                
                # Check model results
                assert "test_model" in result["model_results"], "Should have test_model results"
                model_result = result["model_results"]["test_model"]
                assert "responses" in model_result, "Should have responses"
                assert "timings" in model_result, "Should have timings"
                
                print("✅ Single question evaluation test successful")
                return True
                
    except Exception as e:
        print(f"❌ Single question evaluation test failed: {e}")
        return False

def test_html_report_generation():
    """Test HTML report generation."""
    print("Testing HTML report generation...")
    
    try:
        from config.settings import Settings
        
        with patch('pipelines.prompt_evaluator.ModelManager', MockModelManager):
            with patch('pipelines.prompt_evaluator.OutputGenerator', MockOutputGenerator):
                from pipelines.prompt_evaluator import PromptEvaluator
                
                settings = Settings()
                evaluator = PromptEvaluator(settings)
                
                # Create mock evaluation results
                mock_results = {
                    "category": "test_category",
                    "timestamp": "2023-01-01T00:00:00",
                    "summary_stats": {
                        "total_questions": 1,
                        "model_averages": {
                            "test_model": {
                                "zero_temp": {"average_score": 90, "min_score": 90, "max_score": 90, "total_questions": 1}
                            }
                        }
                    },
                    "question_results": [{
                        "question_data": {"id": "test_001", "question": "Test?", "expected_answer": "Test", "category": "test"},
                        "model_results": {
                            "test_model": {
                                "responses": {"zero_temp": "Test response"},
                                "timings": {"zero_temp": 0.5}
                            }
                        },
                        "analytical_scores": {
                            "test_model": {
                                "zero_temp": {"word_similarity": 0.8, "char_similarity": 0.9, "exact_match": False}
                            }
                        },
                        "ai_evaluation_scores": {
                            "test_model": {
                                "zero_temp": {"score": 90, "reasoning": "Good response"}
                            }
                        }
                    }]
                }
                
                # Test HTML generation
                html_content = evaluator._create_evaluation_html(mock_results)
                
                assert isinstance(html_content, str), "HTML should be a string"
                assert "<html>" in html_content, "Should be valid HTML"
                assert "test_category" in html_content, "Should include category"
                assert "Test?" in html_content, "Should include question"
                
                print("✅ HTML report generation test successful")
                return True
                
    except Exception as e:
        print(f"❌ HTML report generation test failed: {e}")
        return False

def test_cli_integration():
    """Test CLI integration points."""
    print("Testing CLI integration...")
    
    try:
        from config.settings import Settings
        
        # Test that CLI can import the new modules
        with patch('pipelines.prompt_evaluator.ModelManager', MockModelManager):
            with patch('pipelines.prompt_evaluator.OutputGenerator', MockOutputGenerator):
                from cli.main import CLIDriver
                
                # This should not raise import errors
                driver = CLIDriver()
                
                assert hasattr(driver, 'prompt_evaluator'), "CLI should have prompt_evaluator"
                assert hasattr(driver, 'run_evaluation_pipeline'), "CLI should have evaluation pipeline method"
                
                print("✅ CLI integration test successful")
                return True
                
    except Exception as e:
        print(f"❌ CLI integration test failed: {e}")
        return False

def run_all_tests():
    """Run all tests and return summary."""
    print("=" * 60)
    print("LLM Summary Evaluation Tool - Prompt Evaluator Test Suite")
    print("=" * 60)
    
    tests = [
        test_question_bank_loading,
        test_settings_configuration,
        test_prompt_evaluator_initialization,
        test_analytical_scoring,
        test_evaluation_response_parsing,
        test_single_question_evaluation,
        test_html_report_generation,
        test_cli_integration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 All tests passed! The prompt evaluation system is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)