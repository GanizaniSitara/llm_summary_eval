"""
Utility functions for LLM Summary Evaluation Tool.
"""

import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional


def ensure_directory(path: str) -> None:
    """Ensure a directory exists, create if necessary."""
    Path(path).mkdir(parents=True, exist_ok=True)


def get_timestamp() -> str:
    """Get current timestamp in standard format."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def safe_filename(filename: str) -> str:
    """Make a filename safe for filesystem."""
    # Remove/replace problematic characters
    safe_chars = "-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return ''.join(c if c in safe_chars else '_' for c in filename)


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.1f}s"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        return f"{hours}h {remaining_minutes}m"


def print_progress_bar(current: int, total: int, prefix: str = "Progress", 
                      suffix: str = "Complete", length: int = 50) -> None:
    """Print a progress bar to console."""
    if total == 0:
        return
        
    percent = f"{100 * (current / float(total)):.1f}"
    filled_length = int(length * current // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='')
    
    if current == total:
        print()  # New line when complete


def validate_file_path(path: str) -> bool:
    """Validate that a file path exists and is readable."""
    try:
        return Path(path).is_file() and os.access(path, os.R_OK)
    except Exception:
        return False


def validate_url(url: str) -> bool:
    """Basic URL validation."""
    return url.startswith(('http://', 'https://'))


def clean_text(text: str) -> str:
    """Clean text for processing (remove extra whitespace, etc.)."""
    if not text:
        return ""
        
    # Replace multiple whitespace with single space
    import re
    cleaned = re.sub(r'\s+', ' ', text.strip())
    return cleaned


def get_file_size(path: str) -> Optional[int]:
    """Get file size in bytes."""
    try:
        return Path(path).stat().st_size
    except Exception:
        return None


def create_backup(file_path: str) -> Optional[str]:
    """Create a backup of a file with timestamp."""
    try:
        original = Path(file_path)
        if not original.exists():
            return None
            
        timestamp = get_timestamp()
        backup_path = original.parent / f"{original.stem}.backup.{timestamp}{original.suffix}"
        
        import shutil
        shutil.copy2(original, backup_path)
        return str(backup_path)
        
    except Exception as e:
        print(f"Could not create backup: {e}")
        return None


class Timer:
    """Simple timer context manager."""
    
    def __init__(self, description: str = "Operation"):
        self.description = description
        self.start_time = None
        self.end_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        print(f"{self.description} started...")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        print(f"{self.description} completed in {format_duration(duration)}")
        
    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        if self.start_time is None:
            return 0
        end = self.end_time or time.time()
        return end - self.start_time