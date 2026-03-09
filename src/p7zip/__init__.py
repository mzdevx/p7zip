"""
p7zip - Python wrapper for 7-Zip archive operations.

This library provides a high-level, Pythonic interface to 7-Zip functionality,
supporting compression, extraction, encryption, and pattern-based filtering.

Basic Usage:
    >>> from p7zip import SevenZipArchive, auto_detect_binary, CompressionLevel
    >>>
    >>> # Configure 7-Zip binary
    >>> auto_detect_binary()
    >>>
    >>> # Create an encrypted archive
    >>> archive = SevenZipArchive("backup.7z", mode="w")
    >>> archive.set_password("secret")
    >>> archive.compress(["documents/"], compression_level=CompressionLevel.MAXIMUM)
    >>>
    >>> # Extract an archive
    >>> archive = SevenZipArchive("backup.7z", mode="r")
    >>> archive.set_password("secret")
    >>> archive.extract("restore/")
"""

__version__ = "1.0.1"
__author__ = "MZDevX"
__license__ = "MIT"

# Core functionality
from .binary import auto_detect_binary, get_binary_path, set_binary_path
from .core import SevenZipArchive

# Enumerations
from .enums import (
    CompressionLevel,
    CompressionMethod,
    DeleteMode,
    OverwriteMode,
)

# Exceptions
from .exceptions import (
    BinaryNotFoundError,
    CannotOpenArchiveError,
    CRCFailedError,
    InvalidPasswordError,
    SevenZipException,
    SevenZipExecutionError,
)

# Type definitions
from .types import CompletionCallback, PathLike, ProgressCallback

__all__ = [
    # Version and metadata
    "__version__",
    "__author__",
    "__license__",
    # Core functionality
    "SevenZipArchive",
    "set_binary_path",
    "get_binary_path",
    "auto_detect_binary",
    # Exceptions
    "SevenZipException",
    "BinaryNotFoundError",
    "CannotOpenArchiveError",
    "InvalidPasswordError",
    "CRCFailedError",
    "SevenZipExecutionError",
    # Enumerations
    "CompressionLevel",
    "CompressionMethod",
    "OverwriteMode",
    "DeleteMode",
    # Type definitions
    "ProgressCallback",
    "CompletionCallback",
    "PathLike",
]
