'''
__author__ = "Georges Nassopoulos"
__copyright__ = None
__version__ = "1.0.0"
__email__ = "georges.nassopoulos@gmail.com"
__status__ = "Prod"
__desc__ = "Central logging utilities and execution timer for all project modules."
'''

import logging
import os
import sys
import time
import functools
import inspect
from pathlib import Path
from dotenv import load_dotenv

## ============================================================
## GLOBAL CONFIGURATION
## ============================================================

load_dotenv()

# DEBUG=true  -> logs DEBUG
# DEBUG=false -> logs INFO
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"

# LOG_TO_CONSOLE=true -> show logs ALSO in terminal
LOG_TO_CONSOLE = os.getenv("LOG_TO_CONSOLE", "true").lower() == "true"

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

## Map logger names to their log files
LOG_FILES = {
    "constants": LOG_DIR / "constants.log",
    "ocr_utils": LOG_DIR / "ocr_utils.log",
    "ocr": LOG_DIR / "ocr.log",
    "service": LOG_DIR / "service.log",
    "main": LOG_DIR / "main.log",
    "tests": LOG_DIR / "tests.log",
    "default": LOG_DIR / "generic.log"
}

def get_absolute_path():
    """Return the absolute path of the current file"""
    return os.path.abspath(__file__)

def get_logger(name: str) -> logging.Logger:
    """
        Return a logger configured for a specific module

        Args:
            name (str): Logical name of the module (e.g. 'train_model', 'service')

        Returns:
            logging.Logger: Configured logger instance with rotating file handler
    """

    ## Get a logger instance by name
    logger = logging.getLogger(name)

    ## Avoid adding multiple handlers if already configured
    if logger.handlers:
        return logger

    ## Set logger level based on DEBUG_MODE
    logger.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)

    ## Select appropriate log file path
    log_file = LOG_FILES.get(name, LOG_FILES["default"])

    ## Define log format
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"
    )

    ## --------------------------------------------------------
    ## File handler (always enabled)
    ## --------------------------------------------------------
    fh = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    fh.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    ## --------------------------------------------------------
    ## Console handler (optional)
    ## --------------------------------------------------------
    if LOG_TO_CONSOLE:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    ## Prevent propagation to root logger (avoid duplicate logs)
    logger.propagate = False

    return logger
    
def log_execution_time_and_path(func):
    """
        Decorator to log the execution time and source path of any function (sync or async)

        Returns:
            Decorated function with logging instrumentation
    """

    ## Check if the function is async
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):

            ## Extract module name and get logger
            logger_name = func.__module__.split('.')[-1]
            logger = get_logger(logger_name)

            ## Get absolute path of script
            abs_path = get_absolute_path()

            ## Log start
            logger.debug(f"Async function '{func.__name__}' started from: {abs_path}")

            ## Start timer
            start_time = time.time()
            try:
                ## Execute async function
                return await func(*args, **kwargs)
            except Exception as e:
                ## Log exception
                logger.exception(f"Error in async function '{func.__name__}': {e}")
                raise
            finally:
                ## Log execution time
                end_time = time.time()
                logger.info(f"Async function '{func.__name__}' executed in {end_time - start_time:.4f}s | Path: {abs_path}")

        return wrapper

    else:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            ## Extract module name and get logger
            logger_name = func.__module__.split('.')[-1]
            logger = get_logger(logger_name)

            ## Get absolute path of script
            abs_path = get_absolute_path()

            ## Log start
            logger.debug(f"Function '{func.__name__}' started from: {abs_path}")

            ## Start timer
            start_time = time.time()
            try:
                ## Execute sync function
                return func(*args, **kwargs)
            except Exception as e:
                ## Log exception
                logger.exception(f"Error in function '{func.__name__}': {e}")
                raise
            finally:
                ## Log execution time
                end_time = time.time()
                logger.info(f"Function '{func.__name__}' executed in {end_time - start_time:.4f}s | Path: {abs_path}")

        return wrapper