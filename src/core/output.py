"""
Output Generation for LLM Summary Evaluation Tool.

This module handles HTML report generation and difference highlighting.
"""

import re
import string
from typing import List, Dict, Set
from bs4 import BeautifulSoup


class OutputGenerator:
    """Handles generation of HTML reports and difference highlighting."""
    
    def __init__(self, settings):
        self.settings = settings
        
    def generate_html_table(self, results: List[List[str]], title: str = None, 
                           source: str = None, system_prompt: str = "", 
                           user_prompt: str = "") -> str:
        """
        Generate HTML table from model results.
        
        Args:
            results: List of model results [model_name, result1, result2, result3]
            title: Optional title for the report
            source: Source description (URL, file, etc.)
            system_prompt: System prompt used
            user_prompt: User prompt used
            
        Returns:
            HTML string
        """
        html_content = self._get_html_template()
        
        # Build title section
        title_section = f"<h2>{title}</h2>" if title else ""
        
        # Build source section
        source_section = ""
        if source:
            if source.startswith('http'):
                source_section = f'<p>URL Examined: <a href="{source}">{source}</a></p>'
            else:
                source_section = f'<p>Source: {source}</p>'
                
        # Build prompt sections
        system_section = f"<p><strong>System Prompt:</strong> {system_prompt}</p>" if system_prompt else ""
        user_section = f"<p><strong>User Prompt:</strong> {user_prompt}</p>" if user_prompt else ""
        
        # Build table rows
        table_rows = ""
        for result_row in results:
            table_rows += "<tr>"
            for cell in result_row:
                table_rows += f"<td>{cell}</td>"
            table_rows += "</tr>"
            
        # Format the complete HTML
        formatted_html = html_content.format(
            title_section=title_section,
            source_section=source_section,
            system_section=system_section,
            user_section=user_section,
            table_rows=table_rows
        )
        
        return formatted_html
        
    def _get_html_template(self) -> str:
        """Get the base HTML template."""
        return """
        <html>
        <head>
            <title>LLM Summary Evaluation Report</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 20px; 
                    line-height: 1.6;
                }}
                table {{ 
                    border-collapse: collapse; 
                    width: 100%; 
                    margin-top: 20px;
                }}
                th, td {{ 
                    border: 1px solid #ddd; 
                    padding: 12px; 
                    text-align: left; 
                    vertical-align: top;
                }}
                th {{ 
                    background-color: #f2f2f2; 
                    font-weight: bold;
                }}
                tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                mark {{ 
                    background-color: #ffeb3b; 
                    padding: 2px 4px;
                    border-radius: 3px;
                }}
                .model-name {{ 
                    font-weight: bold; 
                    width: 15%;
                }}
                .result-cell {{ 
                    width: 28%;
                }}
                h2 {{ 
                    color: #333; 
                    border-bottom: 2px solid #007acc;
                    padding-bottom: 5px;
                }}
                p {{ 
                    margin: 10px 0; 
                }}
                a {{ 
                    color: #007acc; 
                    text-decoration: none;
                }}
                a:hover {{ 
                    text-decoration: underline; 
                }}
            </style>
        </head>
        <body>
            {title_section}
            {source_section}
            {system_section}
            {user_section}
            
            <table>
                <tr>
                    <th class="model-name">Model</th>
                    <th class="result-cell">Run 1</th>
                    <th class="result-cell">Run 2</th>
                    <th class="result-cell">Run 3</th>
                </tr>
                {table_rows}
            </table>
        </body>
        </html>
        """
        
    def highlight_differences(self, html_content: str) -> str:
        """
        Highlight unique words in each model's outputs.
        
        Args:
            html_content: HTML content to process
            
        Returns:
            HTML with differences highlighted
        """
        soup = BeautifulSoup(html_content, 'lxml')
        rows = soup.find_all('tr')[1:]  # Skip header row
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 4:  # model + 3 result columns
                self._highlight_row_differences(cells)
                
        return str(soup)
        
    def _highlight_row_differences(self, cells):
        """Highlight differences within a single row of results."""
        # Get the result cells (skip model name cell)
        result_cells = cells[1:4]
        run_texts = [cell.decode_contents() for cell in result_cells]
        
        # Tokenize each run
        tokenized_runs = []
        all_normalized_words = []
        word_to_runs = {}
        
        for i, run_text in enumerate(run_texts):
            tokens = self._tokenize_text(run_text)
            normalized_words = set()
            tokens_with_normalized = []
            
            idx = 0
            while idx < len(tokens):
                token = tokens[idx]
                
                # Handle time strings as single tokens
                if self._is_time_string_start(token, tokens, idx):
                    time_string = self._extract_time_string(tokens, idx)
                    tokens_with_normalized.append((time_string, None))
                    idx += len(time_string.split())
                    continue
                    
                if token.strip():
                    # Non-whitespace token
                    normalized_word = token.lower().strip(string.punctuation)
                    if normalized_word:
                        normalized_words.add(normalized_word)
                        tokens_with_normalized.append((token, normalized_word))
                        
                        # Track which runs contain this word
                        word_to_runs.setdefault(normalized_word, set()).add(i)
                    else:
                        # Punctuation only
                        tokens_with_normalized.append((token, None))
                else:
                    # Whitespace
                    tokens_with_normalized.append((token, None))
                    
                idx += 1
                
            tokenized_runs.append(tokens_with_normalized)
            all_normalized_words.append(normalized_words)
            
        # Find unique words for each run
        unique_words = []
        for i in range(len(result_cells)):
            if i < len(all_normalized_words):
                unique = {word for word in all_normalized_words[i] 
                         if len(word_to_runs[word]) == 1}
                unique_words.append(unique)
            else:
                unique_words.append(set())
                
        # Apply highlighting
        for i, cell in enumerate(result_cells):
            if i < len(tokenized_runs):
                highlighted_text = self._apply_highlighting(
                    tokenized_runs[i], 
                    unique_words[i] if i < len(unique_words) else set()
                )
                
                # Replace cell content
                cell.clear()
                new_content = BeautifulSoup(highlighted_text, 'html.parser')
                cell.append(new_content)
                
    def _tokenize_text(self, text: str) -> List[str]:
        """Tokenize text into words, punctuation, and whitespace."""
        # Regex to capture words (including periods), whitespace, and punctuation
        return re.findall(r'\\s+|\\w+[\\w\\.]*|[^\\w\\s]', text)
        
    def _is_time_string_start(self, token: str, tokens: List[str], idx: int) -> bool:
        """Check if this token starts a time string pattern like '(Time: 12.34)'."""
        if token.strip() == '(' and idx + 4 < len(tokens):
            possible_time = ''.join(tokens[idx:idx+5])
            return self._is_time_string(possible_time)
        return False
        
    def _is_time_string(self, token: str) -> bool:
        """Check if token matches time string pattern."""
        return re.match(r'\\(?Time:[^)]*\\)?', token) is not None
        
    def _extract_time_string(self, tokens: List[str], start_idx: int) -> str:
        """Extract complete time string starting at given index."""
        # Simple extraction of 5 tokens for time pattern
        return ''.join(tokens[start_idx:start_idx+5])
        
    def _apply_highlighting(self, tokens_with_normalized: List[tuple], 
                          unique_words: Set[str]) -> str:
        """Apply highlighting to unique words in tokenized text."""
        highlighted = ''
        
        for token, normalized_word in tokens_with_normalized:
            if normalized_word and normalized_word in unique_words:
                highlighted += f'<mark>{token}</mark>'
            else:
                highlighted += token
                
        return highlighted
        
    def generate_summary_report(self, results: List[Dict]) -> str:
        """
        Generate a summary report of multiple evaluations.
        
        Args:
            results: List of evaluation result dictionaries
            
        Returns:
            HTML summary report
        """
        # This could be extended for batch processing summaries
        pass