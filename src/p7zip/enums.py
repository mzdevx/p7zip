"""
Enumeration types for 7-Zip archive operations.

This module defines all enumeration types used throughout the library for
compression, encryption, file handling, and deletion operations.
"""

from enum import IntEnum, StrEnum


class CompressionLevel(IntEnum):
    """
    Compression level for creating archives.

    Higher levels provide better compression ratios but require more processing
    time and memory. Level 0 (STORE) provides no compression, while level 9
    (ULTRA) provides maximum compression at the cost of speed.

    Attributes:
        STORE: No compression applied (fastest, largest file size)
        FASTEST: Minimal compression (very fast, large file size)
        FAST: Low compression (fast, moderately large file size)
        NORMAL: Balanced compression (default, good speed/size ratio)
        MAXIMUM: High compression (slower, smaller file size)
        ULTRA: Maximum compression (slowest, smallest file size)
    """

    STORE = 0  # No compression
    FASTEST = 1  # Fastest compression
    FAST = 3  # Fast compression
    NORMAL = 5  # Normal compression (default)
    MAXIMUM = 7  # Maximum compression
    ULTRA = 9  # Ultra compression (slowest)


class CompressionMethod(StrEnum):
    """
    Supported compression algorithms for archives.

    Different compression methods provide varying levels of compression ratio,
    speed, and compatibility with different archive formats.

    Attributes:
        LZMA2: Default for .7z format, provides best compression ratio
        LZMA: Legacy LZMA compression, good compatibility
        PPMD: PPMd algorithm, optimized for text files
        BZIP2: BZip2 algorithm, good for general purpose compression
        DEFLATE: DEFLATE algorithm, ZIP-compatible
        COPY: No compression, stores files as-is
    """

    LZMA2 = "lzma2"  # Default for .7z format, best compression
    LZMA = "lzma"  # Legacy LZMA compression
    PPMD = "ppmd"  # PPMd algorithm, good for text
    BZIP2 = "bzip2"  # BZip2 algorithm
    DEFLATE = "deflate"  # DEFLATE algorithm (ZIP compatible)
    COPY = "copy"  # No compression (store only)


class OverwriteMode(StrEnum):
    """
    Modes for handling existing files during extraction.

    Attributes:
        OVERWRITE_ALL: Overwrite all existing files without prompting
        SKIP_EXISTING: Skip files that already exist
        RENAME: Rename extracted files to avoid overwriting existing ones
    """

    OVERWRITE_ALL = "a"  # Always overwrite existing files
    SKIP_EXISTING = "s"  # Skip existing files
    RENAME = "t"  # Rename new files to avoid overwriting


class DeleteMode(StrEnum):
    """
    Modes for deleting files or directories after operations.

    Attributes:
        NONE: Do not delete files
        USE_TRASH: Move files to system trash/recycle bin (recoverable)
        PERMANENT: Permanently delete files (not recoverable)
    """

    NONE = "none"  # Do not delete
    USE_TRASH = "trash"  # Move to trash/recycle bin
    PERMANENT = "permanent"  # Permanently delete