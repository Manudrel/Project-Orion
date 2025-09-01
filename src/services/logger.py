import logging
from logging.handlers import TimedRotatingFileHandler
import os

# Create Logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)
log_files = len(os.listdir("logs"))


# Configure the log handler to rotate daily
log_handler = TimedRotatingFileHandler(
    filename=f"logs/elara.log",
    when="midnight",
    interval=1,
    backupCount=7,
    encoding="utf-8"
)

# Fortmat the log messages
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log_handler.setFormatter(formatter)

# Create a logger for the Elara bot
logger = logging.getLogger("ElaraBot")
logger.setLevel(logging.DEBUG)
logger.addHandler(log_handler)

# Logger for discord.py
discord_logger = logging.getLogger("Discord")
discord_logger.setLevel(logging.INFO)  # can be adjusted as needed
discord_logger.addHandler(log_handler)

# Logger for command_parser.py
parser_logger = logging.getLogger("Parser")
parser_logger.setLevel(logging.DEBUG)  # can be adjusted as needed
parser_logger.addHandler(log_handler)

# Expose the logger for use in other modules
__all__ = ["logger"]
