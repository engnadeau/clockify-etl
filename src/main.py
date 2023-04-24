import logging
from config import settings

# Set up logging with a custom format
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt=settings.logging.datetime_fmt,
    level=settings.logging.log_level,
)
