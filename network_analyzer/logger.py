"""Logging configuration and utilities."""

import logging
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Any, Optional


class NetworkAnalyzerLogger:
    """Logger for network analysis with structured output."""

    def __init__(self, log_dir: str = "./logs", comment: Optional[str] = None):
        """Initialize logger.

        Args:
            log_dir: Directory for log files
            comment: Optional free-text comment to embed in logs and filename
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.comment = comment

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Extract first word of comment for filename (alphanumeric only)
        filename_suffix = ""
        if comment:
            first_word = re.split(r'[\s_\-/\\]+', comment.strip())[0]
            first_word = re.sub(r'[^a-zA-Z0-9]', '', first_word)
            if first_word:
                filename_suffix = f"_{first_word}"

        self.log_file = self.log_dir / f"network_analysis_{timestamp}{filename_suffix}.log"
        self.text_log_file = self.log_dir / f"network_analysis_{timestamp}{filename_suffix}_output.txt"

        self._setup_logging()
        self.data: dict[str, Any] = {}

        # Initialize text log file with comment as first content
        with open(self.text_log_file, 'w') as f:
            f.write("WWWIEBUSCH Network Analyzer - Output Log\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            if comment:
                f.write(f"Comment:   {comment}\n")
            f.write("=" * 80 + "\n\n")

    def _setup_logging(self):
        """Configure logging."""
        # Remove all existing handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        # Configure file handler only (no console output)
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )

        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(file_handler)

        # Reduce noise from some loggers
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)

    def log_section(self, section: str, data: Any):
        """Log a section of data.

        Args:
            section: Section name
            data: Data to log
        """
        self.data[section] = data
        logging.info(f"=== {section} ===")

        if isinstance(data, dict):
            for key, value in data.items():
                logging.info(f"{key}: {value}")
        else:
            logging.info(str(data))

    def save_json(self):
        """Save structured data as JSON."""
        json_file = self.log_file.with_suffix('.json')
        with open(json_file, 'w') as f:
            json.dump(self.data, f, indent=2, default=str)
        logging.info(f"JSON data saved to: {json_file}")

    def get_log_path(self) -> str:
        """Get log file path.

        Returns:
            Path to log file
        """
        return str(self.log_file)

    def write_output(self, text: str):
        """Write text to the output log file.

        Args:
            text: Text to write to log
        """
        with open(self.text_log_file, 'a') as f:
            f.write(text + '\n')


def get_logger(name: str) -> logging.Logger:
    """Get logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
