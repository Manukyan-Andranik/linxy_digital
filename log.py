import urllib3
import logging
from colorlog import ColoredFormatter
import os
from datetime import datetime

class Logger:
    @staticmethod
    def load_logger(name, log_dir="logs", log_level=logging.INFO):
        # Ensure the log directory exists
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Create a filename based on the current date
        current_date = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(log_dir, f"{current_date}_log.log")

        # Configure colored logging for console
        formatter = ColoredFormatter(
            "%(log_color)s%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
            datefmt='%Y-%m-%d %H:%M:%S',
            reset=True,
            log_colors={
                'DEBUG':    'cyan',
                'INFO':     'green',
                'WARNING':  'yellow',
                'ERROR':    'red',
                'CRITICAL': 'bold_red',
            }
        )

        # Create console handler for colored logs
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)

        # Create file handler for logging to a file
        logger = logging.getLogger(f"  {name}  ")
        logger.setLevel(log_level)
        logger.addHandler(console_handler)

        if log_file:
            # File handler for writing logs to a file
            file_formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        # Set logging level for urllib3 and http.client to suppress detailed logs
        urllib3_logger = logging.getLogger("urllib3")
        urllib3_logger.setLevel(logging.WARNING)

        http_client_logger = logging.getLogger("http.client")
        http_client_logger.setLevel(logging.WARNING)

        # Alternatively, you can disable them completely:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        return logger
