'''
__author__ = "Georges Nassopoulos"
__copyright__ = None
__version__ = "1.0.0"
__email__ = "georges.nassopoulos@gmail.com"
__status__ = "Prod"
__desc__ = "Initialization file for utils package — exposes logging utilities globally."
'''

from .logging_utils import get_logger, log_execution_time_and_path

__all__ = [
    "get_logger",
    "log_execution_time_and_path"
]
