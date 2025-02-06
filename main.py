import time
import webbrowser
import os
from datetime import datetime
from mailbox_operations import extract_all_article_links_from_mbx
import ollama
from bs4 import BeautifulSoup
import re
import urllib
from playwright.sync_api import sync_playwright, TimeoutError
import csv
from config import SOURCE, MAIL_LINKS_FILE_START_ROW, MAIL_LINKS_FILE_NUM_RECORDS, SYSTEM, USER, PROMPTS, TEMPERATURE, MODELS, DB_PATH, MBX_PATH, CSV_PATH

def generate_html_output(title, url, system, user, all_results):
    html_output = """
    <html>
    <head>
        <style>
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid black; padding: 8px; text-align: left; width: 25%; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>        
        {title_section}       
        <p>URL Examined: <a href="{url}">{url}</a></p>
        <p>System Prompt: {system}</p>
        <p>User Prompt: {user}</p>
        <table>
            <tr><th>Model</th><th>Run 1</th><th>Run 2</th><th>Run 3</th></tr>
    """.format(
        title_section=f"<h2>{title}</h2>" if title else "",
        url=url, system=system, user=user)

    for result in all_results:
        html_output += "<tr>"
        for cell in result:
            html_output += f"<td>{cell}</td>"
        html_output += "</tr>"

    html_output += """
        </table>
    </body>
    </html>
    """
    return html_output


def fetch_content_with_playwright(url, timeout=10000) -> str:
    """
    Fetch content from a URL using Playwright.

    :param url: The URL to fetch content from
    :param timeout: Timeout in milliseconds
    :return: Extracted text content from the page
    """
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context('playwright', headless=False)
        page = browser.new_page()

        try:
            page.goto(url, timeout=timeout)
            page.wait_for_load_state('networkidle', timeout=timeout)
        except TimeoutError:
            print(f"TimeoutError: Failed to load the page within {timeout}ms")
            browser.close()
            return ""

        popup_buttons = [
            'button:text("Close")',
            'button:text("Accept")',
            '[aria-label="Close"]',
            '.modal-close',
            '.popup-close',
            'button.close'
        ]

        for selector in popup_buttons:
            try:
                popup = page.locator(selector).first
                if popup.is_visible():
                    popup.click()
                    break
            except:
                continue

        page.wait_for_timeout(1000)

        # Force reload and wait for content
        page.reload()
        page.wait_for_load_state('networkidle', timeout=timeout)

        html_content = page.inner_html('.main-content')

        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract text from elements within the main-content class
        text_content = ' '.join(element.get_text() for element in soup.select(
            'p, h1, h2, h3, h4, h5, h6'))

        browser.close()

    return text_content


def translate_medium_url(original_url):
    # Parse the original URL
    parsed_url = urllib.parse.urlparse(original_url)

    # Extract the path and query
    path_and_query = parsed_url.path
    if parsed_url.query:
        path_and_query += f"?{parsed_url.query}"

    # Construct the new URL
    new_url = f"https://freedium.cfd/https://medium.com{path_and_query}"

    return new_url


def is_time_string(token):
    # Detect if the token is part of a time string like (Time: xx.x)
    return re.match(r'\(?Time:[^)]*\)?', token)


def highlight_differences_in_html(html_content):
    import string  # Ensure string module is imported
    soup = BeautifulSoup(html_content, 'lxml')
    rows = soup.find_all('tr')[1:]  # Skip the header row

    for row in rows:
        cells = row.find_all('td')
        if len(cells) == 4:
            run_texts = [cells[i + 1].decode_contents() for i in range(3)]

            run_tokens_list = []
            normalized_words_list = []
            word_to_runs = {}

            for i, run_text in enumerate(run_texts):
                # Tokenize the text including words, punctuation, and whitespace
                # Adjusted regex to better capture words with periods and numbers

                # old tokens = re.findall(r'\s+|\w+[\w\.\d]*|[^\w\s]', run_text)
                tokens = re.findall(r'\s+|\w+[\w\.]*|[^\w\s]', run_text)
                normalized_words_set = set()
                tokens_with_normalized = []

                idx = 0
                while idx < len(tokens):
                    token = tokens[idx]
                    # Handle time strings as a single token
                    if token.strip() == '(' and idx + 4 < len(tokens):
                        possible_time_string = ''.join(tokens[idx:idx+5])
                        if is_time_string(possible_time_string):
                            tokens_with_normalized.append((possible_time_string, None))
                            idx += 5
                            continue
                    if token.strip():
                        # Token is not just whitespace
                        normalized_word = token.lower().strip(string.punctuation)
                        if normalized_word:
                            normalized_words_set.add(normalized_word)
                            tokens_with_normalized.append((token, normalized_word))
                        else:
                            # Token is punctuation
                            tokens_with_normalized.append((token, None))
                    else:
                        # Token is whitespace
                        tokens_with_normalized.append((token, None))
                    idx += 1

                run_tokens_list.append(tokens_with_normalized)
                normalized_words_list.append(normalized_words_set)

                # Build word to runs mapping
                for token, normalized_word in tokens_with_normalized:
                    if normalized_word:
                        word_to_runs.setdefault(normalized_word, set()).add(i)

            # Identify unique words for each run
            unique_words = []
            for i in range(3):
                unique = {word for word in normalized_words_list[i] if len(word_to_runs[word]) == 1}
                unique_words.append(unique)

            # Highlight unique words in each run
            for i in range(3):
                tokens_with_normalized = run_tokens_list[i]
                highlighted_text = ''
                for token, normalized_word in tokens_with_normalized:
                    if normalized_word and normalized_word in unique_words[i]:
                        highlighted_text += f'<mark>{token}</mark>'
                    else:
                        highlighted_text += token
                # Replace the cell content
                cells[i + 1].clear()
                new_content = BeautifulSoup(highlighted_text, 'html.parser')
                cells[i + 1].append(new_content)

    return str(soup)


def read_urls_from_file(file_path):
    """
    Read URLs from a text file, one URL per line.

    :param file_path: Path to the text file containing URLs
    :return: List of URLs
    """
    with open(file_path, 'r') as file:
        urls = [line.strip() for line in file if line.strip()]
    return urls


def send_to_ollama(text, model="", system=SYSTEM, user=USER):
    """
    Summarize text using Ollama library.

    :param text: Text to summarize
    :param model: Model to use for summarization
    :return: Summarized text or error message
    """
    if model != "gpt-4o-mini-2024-07-18":
        try:
            response = ollama.chat(model=model,
                                   options={'temperature': TEMPERATURE},
                                   messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"{user}\n\n{text}"},
            ])
            return response['message']['content']
        except Exception as e:
            print(f"Error using Ollama library: {e}")
            return f"Error: Failed to get summary from Ollama. Details: {str(e)}"
    else:
        from openai import OpenAI
        client = OpenAI()
        completion = client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            temperature = TEMPERATURE,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"{user}\n\n{text}"}
            ]
        )
        return(completion.choices[0].message.content)

def run_model_through_ollama(content, model, system_prompt, user_prompt, repetition=3):
    model_results = [model]
    total_time = 0

    if model != "gpt-4o-mini-2024-07-18":
        ollama.chat(model=model, messages=[{"role": "system", "content": ""}, {"role": "user", "content": ""}], keep_alive="30s")

    for i in range(repetition):
        time_now = time.time()
        summary = send_to_ollama(content, model, system=system_prompt, user=user_prompt)
        time_taken = time.time() - time_now
        total_time += time_taken
        model_results.append(f"{summary}<br>(Time: {time_taken:.2f}s)")

    model_results.extend([""] * (3 - repetition))
    avg_time = total_time / repetition
    return model_results, avg_time

def summarize_url(url, title = None):
    content = fetch_content_with_playwright(url)
    all_results = []

    for model in MODELS:
        repetition = 1 if model == "gpt-4o-mini-2024-07-18" else 3
        model_start_time = time.time()
        model_results, avg_time = run_model_through_ollama(content, model, SYSTEM, USER, repetition)
        all_results.append(model_results)
        model_end_time = time.time()
        model_time = model_end_time - model_start_time
        print(f"Model: {model}, Average: {avg_time:.2f}s, Total: {model_time:.2f}s")

    html_output = generate_html_output(title, url, SYSTEM, USER, all_results)

    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"summary_table_{timestamp}.html"

    # Write HTML to file with timestamped name
    with open(filename, "w", encoding='utf-8') as f:
        f.write(html_output)

    print(f"Summary table has been written to '{filename}'")

    print("\n Highlighting differences in proper nouns...")
    # Example usage
    with open(filename, 'r', encoding='utf-8') as file:
        html_content = file.read()
    os.remove(filename)

    highlighted_html = highlight_differences_in_html(html_content)
    highlighted_filename = f"summary_table_{timestamp}.highlighted.html"

    with open(highlighted_filename, 'w', encoding='utf-8') as file:
        file.write(highlighted_html)

    webbrowser.open(f"file://{highlighted_filename}")

def process_question(question):
    all_results = []

    for model in MODELS:
        repetition = 1 if model == "gpt-4o-mini-2024-07-18" else 3
        model_start_time = time.time()
        model_results, avg_time = run_model_through_ollama(question, model, SYSTEM, question, repetition)
        all_results.append(model_results)
        model_end_time = time.time()
        model_time = model_end_time - model_start_time
        print(f"Model: {model}, Average: {avg_time:.2f}s, Total: {model_time:.2f}s")

    html_output = generate_html_output(None, None, SYSTEM, USER, all_results)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"summary_table_{timestamp}.html"

    with open(filename, "w", encoding='utf-8') as f:
        f.write(html_output)

    print(f"Summary table has been written to '{filename}'")

    webbrowser.open(f"file://{filename}")

def process_question_prompt(prompt):
    """
    Process a question prompt from the user.
    """
    question = prompt if prompt else input("Please enter your question: ")
    process_question(question)


def process_articles_from_csv(csv_path, start_row=0, num_records=None):
    """
    Process articles from a CSV file.

    :param csv_path: Path to the CSV file
    :param start_row: Row number to start processing from (0-based index)
    :param num_records: Number of records to process
    """
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

        if num_records is None:
            num_records = len(rows) - start_row

        for row in rows[start_row:start_row + num_records]:
            title = row['Title']
            like_count = row['Like Count']
            link = row['Link']
            translated_link = translate_medium_url(link)
            print(f"Processing article: {title}\n   Link: {translated_link}\n")
            summarize_url(translated_link, title = title)
            print("X" * 50)
            print("X" * 50)
            print("X" * 50)


def main(source='email', file_path=None, prompt=None):
    db_path = DB_PATH
    mbx_path = MBX_PATH
    csv_path = CSV_PATH

    start_time = time.time()
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if source == 'file':
        if not file_path:
            raise ValueError("File path must be provided when source is 'file'.")

        urls = read_urls_from_file(file_path)
        for idx, url in enumerate(urls, 1):
            print(f"{idx}. URL: {url}")
            summarize_url(url)
            print("X" * 50)
            print("X" * 50)
            print("X" * 50)

    elif source == 'prompt':
        process_question_prompt(prompt)

    elif source == 'email':
        print("Analyzing mail storage...")
        extract_all_article_links_from_mbx(mbx_path, csv_path)
        process_articles_from_csv('extracted_articles.csv',
                                  start_row=MAIL_LINKS_FILE_START_ROW,
                                  num_records=MAIL_LINKS_FILE_NUM_RECORDS)

    else:
        raise ValueError("Invalid source. Must be 'email', 'file', or 'local_files'.")

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Execution time: {execution_time:.2f} seconds.")


if __name__ == "__main__":
    if SOURCE == 'file':
        main(source=SOURCE, file_path='urls.txt')
    elif SOURCE == 'email':
        main(source=SOURCE)
    elif SOURCE == 'prompt':
        main(source=SOURCE, prompt=USER)
    elif SOURCE == 'confluence':
        main(source=SOURCE)
    else:
        raise ValueError("Invalid source. Must be 'email', 'file', 'prompt', or 'confluence'.")
