import logging
from logging.handlers import TimedRotatingFileHandler




def init_logger():
    # Configure the logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)  # Set the desired logging level (INFO or ERROR)

    # Create a TimedRotatingFileHandler to rotate logs daily and keep them for the last month
    log_handler = TimedRotatingFileHandler('data_loader.log', when='D', interval=1, backupCount=30)

    # Create a formatter to specify the log format
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # Set the formatter for the handler
    log_handler.setFormatter(log_formatter)

    # Add the handler to the logger
    logger.addHandler(log_handler)

    return logger