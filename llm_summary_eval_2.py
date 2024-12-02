import time
import webbrowser
import os
from datetime import datetime
from mailbox_operations import analyze_db, analyze_mbx, extract_article_links, extract_all_article_links_from_mbx
import ollama
from bs4 import BeautifulSoup
import re
import urllib
from playwright.sync_api import sync_playwright
import csv


SYSTEM = "You are a summarization assistant."
USER = "Provide once sentence summary of the text. Start the sentence with a verb like describes, explains or similar. TEXT START:\n\n"
TEMPERATURE = 0.6
MODELS = [
            # small models
            # "phi3:3.8b",
            #"phi3:latest",
            #"phi3:3.8b-mini-128k-instruct-q4_K_M",
            # "qwen2:latest",
            #"llama3.1:latest",
            #"gemma2:latest",
            # "llama3.2:3b-instruct-fp16",
            #"llama3.2-vision:latest",
            #"phi3:14b",

            # medium models
            # "phi3:14b-medium-128k-instruct-q8_0",
            # "gemma2:27b",
            # "llama3.1:8b-instruct-fp16",
            # "qwen2.5-coder:32b",
            # "command-r:latest",
            # "command-r:35b-v0.1-q4_1",
            # "jean-luc/big-tiger-gemma:27b-v1c-Q6_K",

            # large models
            # "phi3:14b-medium-128k-instruct-fp16",
            # "qwen2.5:32b-instruct-q8_0",
            # "qwen2.5-coder:32b-instruct-q8_0",
            # "qwen:72b", # ends up running on CPU on 2x3090 ... :(
            # "llama3.1:70b-instruct-q4_K_M",
            # "qwen2.5:72b-instruct-q4_K_S", # this one too, runs on CPU on 2x3090
            "llama3.2-vision:11b-instruct-fp16",
            "command-r-plus:104b-08-2024-q3_K_S" # Still doesn't fit at 46GB
            # ollama run command-r-plus:104b-08-2024-q2_K #this one is 39GB



            # Already tested
            # "command-r-plus:104b", # 55GB,need to drop to q3_K_S
            # "llama3.2-vision:90b", # on CPU, no quantization that will run on 2x3090 in VRAM
            # "phi3:14b", # take instruct not the genral one
            # "phi3","phi3.5" # crap
            # "dolphin-mixtral:8x22b", # good but slow, high CPU doesn't fit into 2x3090, overflows to RAM
            # "dolphin-mixtral", # too verbose
            # "llama3.1:70b-instruct-fp16", # 143GB don't run this locally 48GB VRAM and 64GB RAM is not enough
            # "command-r:latest", # not amazing
            # "llama3.1", # needs to be instruct? verbal diarrhea
            # "llama3.1:70b", # ditto

            # OPENAI
            # only runs once to save tokens, see code
            # "gpt-4o-mini-2024-07-18",
          ]




def fetch_medium_content_from_freediumdotcfg_with_playwright(url, timeout=10000) -> str:
    """
    Fetch content from a URL using Playwright.

    :param url: The URL to fetch content from
    :param timeout: Timeout in milliseconds
    :return: Extracted text content from the page
    """
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context('playwright', headless=False)
        page = browser.new_page()

        page.goto(url)
        page.wait_for_load_state('networkidle', timeout=timeout)

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
                tokens = re.findall(r'\s+|\w+[\w\.\d]*|[^\w\s]', run_text)
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



def summarize_with_ollama(text, model="", system=SYSTEM, user=USER):
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


def read_paths_from_file(file_path):
    """
    Read file paths from a text file, one path per line.

    :param file_path: Path to the text file containing file paths
    :return: List of file paths
    """
    with open(file_path, 'r') as file:
        paths = [line.strip() for line in file if line.strip()]
    return paths

def fetch_and_summarize(url, title = None):
    content = fetch_medium_content_from_freediumdotcfg_with_playwright(url)
    # content = chop_off_intro(content) # this was for legacy method of extraction from Freedium
    all_results = []

    for model in MODELS:
        model_results = [model]
        repetition = 1 if model == "gpt-4o-mini-2024-07-18" else 3

        total_time = 0
        if model != "gpt-4o-mini-2024-07-18":
            ollama.chat(model=model, messages=[{"role": "system", "content": ""},
                {"role": "user", "content": ""}],keep_alive="30s")
        for i in range(repetition):
            time_now = time.time()
            summary = summarize_with_ollama(content, model)
            time_taken = time.time() - time_now
            total_time += time_taken

            model_results.append(f"{summary}<br>(Time: {time_taken:.2f}s)")

        # Fill empty cells if less than 3 repetitions
        model_results.extend([""] * (3 - repetition))

        all_results.append(model_results)

        avg_time = total_time / repetition
        print(f"Model: {model}, Average time: {avg_time:.2f} seconds")

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
        title_section = f"<h2>{title}</h2>" if title else "",
        url=url, system=SYSTEM, user=USER)

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
            fetch_and_summarize(translated_link, title = title)
            print("X" * 50)
            print("X" * 50)
            print("X" * 50)


def main(source='email', file_path=None):
    db_path = r'C:\Users\admin\AppData\Local\OEClassic\User\Main Identity\00_Medium.db'
    mbx_path = r'C:\Users\admin\AppData\Local\OEClassic\User\Main Identity\00_Medium.mbx'
    csv_path = 'extracted_articles.csv'

    start_time = time.time()

    if source == 'file':
        if not file_path:
            raise ValueError("File path must be provided when source is 'file'.")

        urls = read_urls_from_file(file_path)
        for idx, url in enumerate(urls, 1):
            print(f"{idx}. URL: {url}")
            fetch_and_summarize(url)
            print("X" * 50)
            print("X" * 50)
            print("X" * 50)

    elif source == 'local_files':
        pass

    elif source == 'email':
        print("Analyzing mail storage...")
        extract_all_article_links_from_mbx(mbx_path, csv_path)
        process_articles_from_csv('extracted_articles.csv', start_row=25, num_records=1)

    else:
        raise ValueError("Invalid source. Must be 'email', 'file', or 'local_files'.")

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time:.2f} seconds.")

if __name__ == "__main__":
    #source = 'file'
    source = 'email'
    main(source=source, file_path='urls.txt')