import sqlite3
from email import policy
from email.parser import BytesParser
import urllib.parse
import time
from bs4 import BeautifulSoup
import spacy
import ollama
from playwright.sync_api import sync_playwright
from datetime import datetime
import webbrowser
import os
import re
import string

SYSTEM = "You are a summarization assistant."
USER = "Provide short summary of the text. No more than one paragraph or three sentences. TEXT START:\n\n"
TEMPERATURE = 0.6
MODELS = ["llama3.1:8b-instruct-fp16",
          "llama3.2:3b-instruct-fp16",
          "llama3.1:70b-instruct-q4_K_M",
          "jean-luc/big-tiger-gemma:27b-v1c-Q6_K",
          "qwen2.5:32b-instruct-q8_0",
          "phi3:3.8b-mini-128k-instruct-q4_K_M", # fast but verbose
          "phi3:14b-medium-128k-instruct-q8_0",

          # "command-r:35b-v0.1-q4_1",
          # "qwen2",
          # "qwen:72b",
          # "gemma2",
          # "gemma2:27b",
          # "phi3:14b", # take instruct
          # "phi3","phi3.5" # crap
          # "dolphin-mixtral:8x22b", # good but slow, high CPU doesn't fit into 2x3090, overflows to RAM
          # "dolphin-mixtral", # too verbose
          # "llama3.1:70b-instruct-fp16", # 143GB don't run this locally 48GB VRAM and 64GB RAM is not enough
          # "command-r:latest", # not amazing
          # "llama3.1", # needs to be instruct? verbal diarrhea
          # "llama3.1:70b", # ditto

          # OPENAI - only runs once to save tokens, see code
          # "gpt-4o-mini-2024-07-18",
          ]

# Load the spaCy model for named entity recognition
nlp = spacy.load("en_core_web_sm")


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

def highlight_words(text, words_to_highlight):
    """Wrap words in <mark> tags for highlighting."""
    for word in words_to_highlight:
        text = text.replace(word, f"<mark>{word}</mark>")
    return text

def fetch_medium_content_from_freediumdotcfg_with_playwright(url, timeout=10000) -> str:
    """
    Fetch content from a URL using Playwright.

    :param url: The URL to fetch content from
    :param timeout: Timeout in milliseconds
    :return: Extracted text content from the page
    """
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context('playwright',headless=False)
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
            options={'temperature': TEMPERATURE},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"{user}\n\n{text}"}
            ]
        )
        return(completion.choices[0].message.content)


def fetch_and_summarize(url):
    content = fetch_medium_content_from_freediumdotcfg_with_playwright(url)
    # content = chop_off_intro(content) # this was for legacy method of extraction from Freedium
    all_results = []

    for model in MODELS:
        model_results = [model]
        repetition = 1 if model == "gpt-4o-mini-2024-07-18" else 3

        total_time = 0
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
        <h2>Summary Table</h2>        
        <p>URL Examined: <a href="{url}">{url}</a></p>
        <p>System Prompt: {system}</p>
        <p>User Prompt: {user}</p>
        <table>
            <tr><th>Model</th><th>Run 1</th><th>Run 2</th><th>Run 3</th></tr>
    """.format(url=url, system=SYSTEM, user=USER)

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


def extract_article_links(html_content):
    """
    Extracts the titles and links of major articles from the given HTML content.

    Parameters:
        html_content (str): The HTML content as a string.

    Returns:
        List[Tuple[str, str]]: A list of tuples containing article titles and their corresponding links.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    articles = []

    # Find all article containers
    article_containers = soup.find_all('div', class_='cb cc cd ce cf cg ch ci cj')

    for container in article_containers:
        # Find the <b> tag with an 'id' attribute (title)
        title_tag = container.find('b', id=True)
        if title_tag:
            title = title_tag.get_text(strip=True)
            # Find the parent <a> tag with href
            link_tag = title_tag.find_parent('a', href=True)
            if link_tag:
                href = link_tag['href']
                articles.append((title, href))

    return articles


def analyze_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get total email count
    cursor.execute("SELECT COUNT(*) FROM mbx")
    total_count = cursor.fetchone()[0]

    # Get the top 1 email
    cursor.execute("SELECT id, subjectStrip, size, uidl FROM mbx ORDER BY id LIMIT 1")
    email_data = cursor.fetchone()

    conn.close()
    return total_count, email_data


def analyze_mbx(mbx_path):
    with open(mbx_path, 'rb') as file:
        while True:
            line = file.readline()
            if not line:
                break  # End of file reached

            # Decode the line and strip whitespace
            line_str = line.decode('utf-8', errors='ignore').strip()

            # Look for the message header start
            if line_str == '[hdr]':
                # Read the next line, which should be 'mlen=...'
                mlen_line = file.readline()
                if not mlen_line:
                    break  # End of file reached

                mlen_str = mlen_line.decode('utf-8', errors='ignore').strip()
                if mlen_str.startswith('mlen='):
                    # Extract and parse the message length
                    mlen_value = mlen_str[len('mlen='):]
                    try:
                        mlen = int(mlen_value, 16)  # Parse as hexadecimal
                    except ValueError:
                        print(f"Invalid mlen value: {mlen_value}")
                        continue  # Skip this message and continue

                    # Expect the next line to be '[msg]'
                    msg_line = file.readline()
                    if not msg_line:
                        break  # End of file reached

                    msg_line_str = msg_line.decode('utf-8', errors='ignore').strip()
                    if msg_line_str == '[msg]':
                        # Read the message content of specified length
                        msg_content = file.read(mlen)
                        if len(msg_content) < mlen:
                            print("Incomplete message content.")
                            break  # Cannot proceed further

                        # Parse the email content
                        parser = BytesParser(policy=policy.default)
                        try:
                            email_message = parser.parsebytes(msg_content)
                        except Exception as e:
                            print(f"Error parsing email: {e}")
                            return None, None

                        # Extract subject and HTML body
                        subject = email_message['subject']
                        html_body = ""
                        if email_message.is_multipart():
                            for part in email_message.walk():
                                content_type = part.get_content_type()
                                if content_type == 'text/html':
                                    charset = part.get_content_charset()
                                    html_body = part.get_payload(decode=True).decode(charset, errors='replace')
                                    break
                        else:
                            if email_message.get_content_type() == 'text/html':
                                charset = email_message.get_content_charset()
                                html_body = email_message.get_payload(decode=True).decode(charset, errors='replace')

                        return subject, html_body
                    else:
                        print(f"Expected '[msg]', but found: {msg_line_str}")
                        break  # Invalid format, stop parsing
                else:
                    print(f"Expected 'mlen=', but found: {mlen_str}")
                    break  # Invalid format, stop parsing
            else:
                # Skip lines until we find the next '[hdr]'
                continue

    return None, None


def read_urls_from_file(file_path):
    """
    Read URLs from a text file, one URL per line.

    :param file_path: Path to the text file containing URLs
    :return: List of URLs
    """
    with open(file_path, 'r') as file:
        urls = [line.strip() for line in file if line.strip()]
    return urls

def read_paths_from_file(file_path):
    """
    Read file paths from a text file, one path per line.

    :param file_path: Path to the text file containing file paths
    :return: List of file paths
    """
    with open(file_path, 'r') as file:
        paths = [line.strip() for line in file if line.strip()]
    return paths


def main(source='email', file_path=None):
    """
    Main function to analyze mail storage, read URLs from a file, or process local text files and summarize content.

    :param source: Source of URLs or file paths ('email', 'file', or 'local_files')
    :param file_path: Path to the text file containing URLs or file paths (required if source is 'file' or 'local_files')
    """
    # Paths to the files
    db_path = r'C:\Users\admin\AppData\Local\OEClassic\User\Main Identity\00_Medium.db'
    mbx_path = r'C:\Users\admin\AppData\Local\OEClassic\User\Main Identity\00_Medium.mbx'

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
        PROCESS_TOP_N = 3

        # Analyze DB
        db_count, db_email = analyze_db(db_path)
        print(f"\nDatabase Analysis:")
        print(f"Total emails in DB: {db_count}")
        print("Top email from DB (id, subject, size, uidl):")
        print(db_email)

        # Analyze MBX
        subject, html_body = analyze_mbx(mbx_path)
        if subject is not None:
            print(f"\nMBX File Analysis:")
            print(f"Subject: {subject}")

            html_content = html_body
            article_links = extract_article_links(html_content)

            # Print the extracted article titles and links
            for idx, (title, link) in enumerate(article_links[:PROCESS_TOP_N], 1):
                translated_link = translate_medium_url(link)
                print(f"{idx}. {title}\n   Link: {translated_link}\n")
                fetch_and_summarize(translated_link)
                print("X" * 50)
                print("X" * 50)
                print("X" * 50)

        else:
            print("Could not parse the email from MBX file.")

    else:
        raise ValueError("Invalid source. Must be 'email', 'file', or 'local_files'.")

    end_time = time.time()
    # Calculate and print the execution time
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time:.2f} seconds.")

if __name__ == "__main__":
    # Example usage:
    main(source='file', file_path='urls.txt')
    # main(source='email')

