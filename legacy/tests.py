import os
import re
import time
import csv
from datetime import datetime
from bs4 import BeautifulSoup

import pytest
import llm_summary_eval_2 as llm  # ensure the file is named llm_summary_eval_2.py


def test_translate_medium_url():
    original = "https://medium.com/some-article?query=123"
    expected = "https://freedium.cfd/https://medium.com/some-article?query=123"
    assert llm.translate_medium_url(original) == expected


@pytest.mark.parametrize("token,expected", [
    ("(Time: 12.34)", True),
    ("Time: 12.34", True),
    ("(Time: abc)", True),
    ("Not time", False),
])
def test_is_time_string(token, expected):
    result = llm.is_time_string(token)
    if expected:
        assert result is not None
    else:
        assert result is None


def test_highlight_differences_in_html():
    html = """
    <html><body>
      <table>
        <tr><th>Header</th><th>Run1</th><th>Run2</th><th>Run3</th></tr>
        <tr>
          <td>Model1</td>
          <td>Apple Banana</td>
          <td>Apple Cherry</td>
          <td>Banana Cherry</td>
        </tr>
      </table>
    </body></html>
    """
    highlighted = llm.highlight_differences_in_html(html)
    assert "<mark>" in highlighted


def test_read_urls_from_file(tmp_path):
    content = "http://example.com\nhttps://test.com\n"
    file = tmp_path / "urls.txt"
    file.write_text(content)
    urls = llm.read_urls_from_file(str(file))
    assert urls == ["http://example.com", "https://test.com"]


def fake_ollama_chat(*args, **kwargs):
    return {"message": {"content": "Fake summary"}}


def test_send_to_ollama(monkeypatch):
    monkeypatch.setattr(llm, "ollama", type("FakeOllama", (), {"chat": fake_ollama_chat}))
    summary = llm.send_to_ollama("Some text", model="test-model", system="sys", user="usr")
    assert "Fake summary" in summary


def fake_send_to_ollama(text, model="", system="", user=""):
    return "Fake summary"


def test_run_model_through_ollama(monkeypatch):
    monkeypatch.setattr(llm, "send_to_ollama", fake_send_to_ollama)
    results, avg_time = llm.run_model_through_ollama("Content", "test-model", "sys", "usr", repetition=2)
    assert len(results) == 3
    assert "Fake summary" in results[1]
    assert avg_time >= 0


def fake_fetch(url, timeout=10000):
    return "Dummy content for summarization."


def fake_run_model(content, model, system, user, repetition):
    return ([model, "Summary", "Summary", "Summary"], 0.1)


def fake_webbrowser_open(url):
    pass


class FakeFile:
    def __init__(self):
        self.content = ""
    def write(self, data):
        self.content += data
    def read(self):
        return self.content
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def fake_open_factory(fake_files):
    def fake_open(filename, mode, encoding=None):
        fake_file = FakeFile()
        fake_files[filename] = fake_file
        return fake_file
    return fake_open


def test_summarize_url(monkeypatch):
    fake_files = {}
    monkeypatch.setattr(llm, "fetch_content_with_playwright", fake_fetch)
    monkeypatch.setattr(llm, "run_model_through_ollama", fake_run_model)
    monkeypatch.setattr(llm, "webbrowser", type("FakeWebbrowser", (), {"open": fake_webbrowser_open}))
    monkeypatch.setattr(os, "remove", lambda filename: None)
    monkeypatch.setattr("builtins.open", fake_open_factory(fake_files))
    test_url = "http://example.com"
    llm.summarize_url(test_url, title="Test Title")
    assert any("summary_table_" in fname for fname in fake_files.keys())


def test_process_question(monkeypatch):
    fake_files = {}
    monkeypatch.setattr(llm, "run_model_through_ollama", fake_run_model)
    monkeypatch.setattr(llm, "webbrowser", type("FakeWebbrowser", (), {"open": fake_webbrowser_open}))
    monkeypatch.setattr(os, "remove", lambda filename: None)
    monkeypatch.setattr("builtins.open", fake_open_factory(fake_files))
    llm.process_question("Test question?")
    assert any("summary_table_" in fname for fname in fake_files.keys())


def test_process_articles_from_csv(tmp_path, monkeypatch):
    csv_content = "Title,Like Count,Link\nTest Article,100,http://medium.com/test\n"
    csv_file = tmp_path / "articles.csv"
    csv_file.write_text(csv_content)
    monkeypatch.setattr(llm, "summarize_url", lambda url, title=None: None)
    llm.process_articles_from_csv(str(csv_file), start_row=0, num_records=1)


def test_main_file(tmp_path, monkeypatch):
    urls_content = "http://example.com\n"
    urls_file = tmp_path / "urls.txt"
    urls_file.write_text(urls_content)
    monkeypatch.setattr(llm, "summarize_url", lambda url, title=None: None)
    monkeypatch.setattr(llm, "print", lambda *args, **kwargs: None)
    llm.main(source="file", file_path=str(urls_file))


def fake_extract(mbx_path, csv_path):
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("Title,Like Count,Link\nTest,10,http://medium.com/test\n")


def test_main_email(monkeypatch, tmp_path):
    monkeypatch.setattr(llm, "extract_all_article_links_from_mbx", fake_extract)
    monkeypatch.setattr(llm, "process_articles_from_csv", lambda csv_path, start_row, num_records: None)
    llm.main(source="email")


def test_main_prompt(monkeypatch):
    monkeypatch.setattr(llm, "process_question_prompt", lambda prompt: None)
    llm.main(source="prompt", prompt="Test prompt")
