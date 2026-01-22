import logging


class ColorFormatter(logging.Formatter):
    """Custom logging formatter that adds color codes based on log level."""

    # Color codes.
    dark_grey = "\x1b[90m"
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    def __init__(self, fmt=None):
        # Initialize the base class.
        super().__init__()

        if fmt is None:
            fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

        self.formatters = {
            logging.DEBUG: logging.Formatter(
                ColorFormatter.dark_grey + fmt + ColorFormatter.reset
            ),
            logging.INFO: logging.Formatter(
                ColorFormatter.grey + fmt + ColorFormatter.reset
            ),
            logging.WARNING: logging.Formatter(
                ColorFormatter.yellow + fmt + ColorFormatter.reset
            ),
            logging.ERROR: logging.Formatter(
                ColorFormatter.red + fmt + ColorFormatter.reset
            ),
            logging.CRITICAL: logging.Formatter(
                ColorFormatter.bold_red + fmt + ColorFormatter.reset
            ),
        }

    def format(self, record):
        return self.formatters[record.levelno].format(record)


# Create a logger for the module.
LOGGER = logging.getLogger("liveplot")
LOGGER.setLevel(logging.WARNING)

# Configure the stream handler.
formatter = ColorFormatter()
handler = logging.StreamHandler()
handler.setFormatter(formatter)
LOGGER.addHandler(handler)


def info_mode():
    """Set the logger to info mode."""
    LOGGER.setLevel(logging.INFO)


def debug_mode():
    """Set the logger to debug mode."""
    LOGGER.setLevel(logging.DEBUG)


def log_to_file(file_path: str):
    """Add a file handler to log messages to a specified file."""
    file_handler = logging.FileHandler(file_path)
    file_handler.setFormatter(formatter)
    LOGGER.addHandler(file_handler)
