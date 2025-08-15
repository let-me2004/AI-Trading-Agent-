# logger_setup.py

import logging
import sys

def setup_logger():
    """
    Configures a logger to output to both the console and a file.
    """
    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO) # Set the lowest level of messages to handle

    # Create a formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(module)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Create a handler to write to the console (stdout)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.setFormatter(formatter)

    # Create a handler to write to a file
    file_handler = logging.FileHandler('cognito_trader.log')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # Add the handlers to the logger
    # Check if handlers have already been added to prevent duplication
    if not logger.handlers:
        logger.addHandler(stdout_handler)
        logger.addHandler(file_handler)
    
    return logger