import logging

# Create a logger for the module.
LOGGER = logging.getLogger("liveplot")
LOGGER.setLevel(logging.INFO)

# Configure the stream handler.
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = logging.StreamHandler()
handler.setFormatter(formatter)
LOGGER.addHandler(handler)


def debug_mode():
    """
    Set the logger to debug mode.
    """
    LOGGER.setLevel(logging.DEBUG)


def log_to_file(file_path: str):
    """
    Add a file handler to log messages to a specified file.
    """
    file_handler = logging.FileHandler(file_path)
    file_handler.setFormatter(formatter)
    LOGGER.addHandler(file_handler)
