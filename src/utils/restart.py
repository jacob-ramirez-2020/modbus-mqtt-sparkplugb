"""
restart_utils.py

Provides functionality to gracefully restart the currently running Python
script. This can be used to reload configuration or recover from failures
without requiring an external process manager.

Includes error handling and logging using print_error.
"""

import os
import sys
import time
from src.utils.logger_module import print_error, log_info, get_log_level_num


def restart_script(delay_seconds: int = 0, exit_code: int = 0):
    """
    Restart the currently running Python script in-place.

    Args:
        delay_seconds (int): Optional number of seconds to wait before restart.
        exit_code (int): Optional exit code to use if restarting fails.

    Raises:
        OSError: If the script cannot be restarted.
    """
    try:
        if get_log_level_num() <= 5:
            log_info(f"Restarting script in {delay_seconds} second(s)...")

        if delay_seconds > 0:
            time.sleep(delay_seconds)

        python = sys.executable
        os.execl(python, python, *sys.argv)
        
        if get_log_level_num() <= 5:
            log_info("Restart Finished.")
    except Exception as e:
        print_error("restart_script", e)
        sys.exit(exit_code)
