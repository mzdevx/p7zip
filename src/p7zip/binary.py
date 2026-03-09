"""
7-Zip binary discovery and management utilities.

This module handles locating, validating, and managing the 7-Zip executable
binary across different operating systems.
"""

import os
from pathlib import Path
import platform
import shutil
from typing import Optional

from .exceptions import BinaryNotFoundError
from .types import PathLike

# Global binary path registry
_BINARY_PATH: Optional[str] = None


def _is_executable(file_path: Path) -> bool:
    """
    Check if the given file path points to an executable file.

    Args:
        file_path: Path to the file to check
    Returns:
        True if the file exists and is executable, False otherwise
    """
    if not file_path.exists() or not file_path.is_file():
        return False

    if platform.system().lower() == "windows":
        # On Windows, check for common executable extension
        executable_extensions = [".exe"]
        return file_path.suffix.lower() in executable_extensions
    else:
        # On Unix-like systems, check executable permission
        return os.access(file_path, os.X_OK)


def set_binary_path(binary_path: PathLike) -> None:
    """
    Manually set the path to the 7-Zip binary executable.

    This function validates that the specified binary exists and is executable
    before setting it as the global binary path.

    Args:
        binary_path: Absolute or relative path to the 7z executable.
                    Environment variables (e.g., $HOME) and ~ are expanded.

    Raises:
        BinaryNotFoundError: If the binary doesn't exist or is not executable

    Example:
        >>> set_binary_path("/usr/local/bin/7zz")
        >>> set_binary_path("~/Applications/7-Zip/7z.exe")
    """
    # Expand environment variables and user home directory
    expanded_path = os.path.expanduser(os.path.expandvars(str(binary_path)))

    # Check if file exists
    if not os.path.exists(expanded_path):
        raise BinaryNotFoundError(
            f"Binary not found at specified path: {expanded_path}"
        )

    # Check if file is executable
    if not _is_executable(Path(expanded_path)):
        raise BinaryNotFoundError(
            f"Binary is not executable: {expanded_path}. "
            f"Please check file permissions."
        )

    global _BINARY_PATH
    _BINARY_PATH = os.path.abspath(expanded_path)


def get_binary_path() -> Optional[str]:
    """
    Get the currently configured 7-Zip binary path.

    Returns:
        The absolute path to the 7z binary, or None if not configured

    Example:
        >>> set_binary_path("/usr/bin/7zz")
        >>> get_binary_path()
        '/usr/bin/7zz'
    """
    return _BINARY_PATH


def auto_detect_binary() -> None:
    """
    Automatically detect and configure the 7-Zip binary path.

    This function searches for 7-Zip executables in the system PATH and
    common installation directories. It prioritizes newer binaries (7z, 7zz)
    over legacy ones (7za).

    Search Strategy:
        1. Search system PATH for 7zz, 7z, or 7za (platform-dependent)
        2. On Windows: Check common installation directories

    Raises:
        BinaryNotFoundError: If no 7-Zip binary is found on the system

    Example:
        >>> auto_detect_binary()  # Automatically finds 7z in PATH
        >>> archive = SevenZipArchive("data.7z")  # Ready to use
    """
    global _BINARY_PATH

    current_platform = platform.system().lower()

    # Platform-specific binary names (newer versions first)
    if current_platform == "windows":
        binary_candidates = ["7z.exe", "7za.exe"]
    else:
        binary_candidates = ["7zz", "7z", "7za"]

    # Strategy 1: Search in system PATH
    for binary_name in binary_candidates:
        binary_path = shutil.which(binary_name)
        if binary_path:
            _BINARY_PATH = binary_path
            return

    # Strategy 2: Windows-specific fallback to common installation directories
    if current_platform == "windows":
        common_installation_paths = [
            r"C:\Program Files\7-Zip\7z.exe",
            r"C:\Program Files (x86)\7-Zip\7z.exe",
            r"C:\Program Files\7-Zip\7za.exe",
            r"C:\Program Files (x86)\7-Zip\7za.exe",
        ]
        for path in common_installation_paths:
            if _is_executable(Path(path)):
                _BINARY_PATH = path
                return

    # No binary found - raise error with helpful message
    raise BinaryNotFoundError(
        f"7-Zip binary not found in PATH for platform '{current_platform}'. "
        f"Please install 7-Zip or use set_binary_path() to specify the "
        f"binary location manually. Searched for: {', '.join(binary_candidates)}"
    )
