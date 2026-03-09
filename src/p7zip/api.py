"""
Simplified API for common 7-Zip operations.

This module provides a high-level, user-friendly interface for the most common
archive operations, making it easier to work with 7-Zip without needing to
understand all the advanced features.
"""

from pathlib import Path
from typing import List, Optional

from .binary import auto_detect_binary, set_binary_path
from .core import SevenZipArchive
from .enums import DeleteMode, OverwriteMode
from .types import PathLike, ProgressCallback

# ============================================================================
# Initialization & Configuration
# ============================================================================


def configure_binary(binary_path: Optional[PathLike] = None) -> None:
    """
    Configure the 7-Zip binary path.

    Args:
        binary_path: Path to the 7z binary. If None, attempts auto-detection.

    Example:
        >>> # Auto-detect 7-Zip binary in system PATH
        >>> configure_binary()
        >>>
        >>> # Set a specific 7-Zip installation
        >>> configure_binary("/usr/bin/7zz")
    """
    if binary_path is None:
        auto_detect_binary()
    else:
        set_binary_path(binary_path)


# ============================================================================
# Archive Listing & Inspection
# ============================================================================


def list_archive_contents(
    archive: PathLike, password: Optional[str] = None
) -> List[str]:
    """
    List all files in an archive without extracting.

    Args:
        archive: Path to the archive file
        password: Optional password for encrypted archives

    Returns:
        List of filenames in the archive
        
    Raises:
        FileNotFoundError: If the archive file doesn't exist
        InvalidPasswordError: If the provided password is incorrect
        CannotOpenArchiveError: If the archive cannot be opened (e.g., due to corruption)
        SevenZipExecutionError: For other errors during listing

    Example:
        >>> files = list_archive_contents("backup.7z")
        >>> for file in files:
        ...     print(file)
    """
    with SevenZipArchive(archive, mode="r") as arch:
        if password:
            arch.set_password(password)
        return arch.list_contents()


def verify_archive_integrity(
    archive: PathLike, password: Optional[str] = None,
) -> bool:
    """
    Verify the integrity of an archive.

    Args:
        archive: Path to the archive file
        password: Optional password for encrypted archives

    Returns:
        True if all files pass integrity check, False otherwise
        
    Raises:
        FileNotFoundError: If the archive file doesn't exist
        InvalidPasswordError: If the provided password is incorrect
        CannotOpenArchiveError: If the archive cannot be opened (e.g., due to corruption)
        SevenZipExecutionError: For other errors during testing
        
    Example:
        >>> if verify_archive_integrity("backup.7z"):
        ...     print("Archive is OK")
        ... else:
        ...     print(f"Archive is corrupted")
    """
    with SevenZipArchive(archive, mode="r") as arch:
        if password:
            arch.set_password(password)
        return arch.test_integrity() is None


# ============================================================================
# Extraction Operations
# ============================================================================


def extract_all(
    archive: PathLike,
    destination: PathLike = ".",
    password: Optional[str] = None,
    overwrite: bool = True,
    delete_after: bool = False,
    progress_callback: Optional[ProgressCallback] = None,
) -> Optional[List[str]]:
    """
    Extract all files from an archive to a destination directory.

    This is the simplest way to extract an entire archive.

    Args:
        archive: Path to the archive file
        destination: Directory to extract files to (created if needed)
        password: Optional password for encrypted archives
        overwrite: Whether to overwrite existing files
        delete_after: Whether to delete the archive after extraction
        progress_callback: Optional callback for progress updates

    Returns:
        List of files that failed CRC check, or None if all successful
    
    Raises:
        FileNotFoundError: If the archive file doesn't exist
        InvalidPasswordError: If the provided password is incorrect
        CannotOpenArchiveError: If the archive cannot be opened (e.g., due to corruption)
        SevenZipExecutionError: For other errors during extraction

    Example:
        >>> extract_all("backup.7z", destination="restored/")
        >>> extract_all("encrypted.7z", destination="data/", password="secret123")
    """
    overwrite_mode = (
        OverwriteMode.OVERWRITE_ALL if overwrite else OverwriteMode.SKIP_EXISTING
    )
    delete_mode = DeleteMode.USE_TRASH if delete_after else DeleteMode.NONE

    with SevenZipArchive(
        archive, mode="r", progress_callback=progress_callback
    ) as arch:
        if password:
            arch.set_password(password)
        return arch.extract(
            destination=destination,
            overwrite_mode=overwrite_mode,
            delete_after_extraction=delete_mode,
        )


def extract_files(
    archive: PathLike,
    files: List[str],
    destination: PathLike = ".",
    password: Optional[str] = None,
    overwrite: bool = True,
    delete_after: bool = False,
    progress_callback: Optional[ProgressCallback] = None,
) -> Optional[List[str]]:
    """
    Extract specific files from an archive.

    Args:
        archive: Path to the archive file
        files: List of specific files/directories to extract from the archive
        destination: Directory to extract files to
        password: Optional password for encrypted archives
        overwrite: Whether to overwrite existing files
        delete_after: Whether to delete the archive after extraction
        progress_callback: Optional callback for progress updates

    Returns:
        List of files that failed CRC check, or None if all successful
        
    Raises:
        FileNotFoundError: If the archive file doesn't exist
        InvalidPasswordError: If the provided password is incorrect
        CannotOpenArchiveError: If the archive cannot be opened (e.g., due to corruption)
        SevenZipExecutionError: For other errors during extraction

    Example:
        >>> extract_files("backup.7z", ["documents/report.pdf", "photos/"], "restored/")
        >>> extract_files("encrypted.7z", ["config.ini"], password="secret")
    """
    overwrite_mode = (
        OverwriteMode.OVERWRITE_ALL if overwrite else OverwriteMode.SKIP_EXISTING
    )
    delete_mode = DeleteMode.USE_TRASH if delete_after else DeleteMode.NONE

    with SevenZipArchive(
        archive, mode="r", progress_callback=progress_callback
    ) as arch:
        if password:
            arch.set_password(password)
        return arch.extract(
            destination=destination,
            specific_files_or_dirs=files,
            delete_after_extraction=delete_mode,
            overwrite_mode=overwrite_mode,
        )


def extract_by_pattern(
    archive: PathLike,
    destination: PathLike = ".",
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    password: Optional[str] = None,
    overwrite: bool = True,
    delete_after: bool = False,
    progress_callback: Optional[ProgressCallback] = None,
) -> Optional[List[str]]:
    """
    Extract files matching specific patterns from an archive.

    Args:
        archive: Path to the archive file
        destination: Directory to extract files to
        include_patterns: List of glob patterns for files to include
        exclude_patterns: List of glob patterns for files to exclude
        password: Optional password for encrypted archives
        overwrite: Whether to overwrite existing files
        delete_after: Whether to delete the archive after extraction
        progress_callback: Optional callback for progress updates

    Returns:
        List of files that failed CRC check, or None if all successful
        
    Raises:
        FileNotFoundError: If the archive file doesn't exist
        InvalidPasswordError: If the provided password is incorrect
        CannotOpenArchiveError: If the archive cannot be opened (e.g., due to corruption)
        SevenZipExecutionError: For other errors during extraction

    Example:
        >>> # Extract only PDF files
        >>> extract_by_pattern("backup.7z", include_patterns=["*.pdf"])
        >>>
        >>> # Extract all files except temporary ones
        >>> extract_by_pattern(
        ...     "backup.7z",
        ...     exclude_patterns=["*.tmp", "*.log", "*/__pycache__/*"]
        ... )
    """
    overwrite_mode = (
        OverwriteMode.OVERWRITE_ALL if overwrite else OverwriteMode.SKIP_EXISTING
    )
    delete_mode = DeleteMode.USE_TRASH if delete_after else DeleteMode.NONE

    with SevenZipArchive(
        archive, mode="r", progress_callback=progress_callback
    ) as arch:
        if password:
            arch.set_password(password)
        return arch.extract(
            destination=destination,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            delete_after_extraction=delete_mode,
            overwrite_mode=overwrite_mode,
        )


# ============================================================================
# Compression Operations
# ============================================================================


def compress(
    archive: PathLike,
    sources: List[PathLike],
    password: Optional[str] = None,
    compression_level: int = 5,
    archive_format: str = "7z",
    encrypt_headers: bool = False,
    exclude_patterns: Optional[List[str]] = None,
    include_patterns: Optional[List[str]] = None,
    delete_after: bool = False,
    progress_callback: Optional[ProgressCallback] = None,
) -> None:
    """
    Create a compressed archive with optional compression and encryption.

    Args:
        archive: Output archive path
        sources: List of files and/or directories to compress
        password: Optional password for encryption
        compression_level: Compression level (0-9)
        archive_format: Archive format ("7z", "zip" or any other format supported by 7-Zip)
        encrypt_headers: Whether to encrypt headers (requires password and 7z format)
        exclude_patterns: List of glob patterns for files to exclude
        include_patterns: List of glob patterns for files to include
        delete_after: Whether to delete source directory after compression
        progress_callback: Optional callback for progress updates
        
    Raises:
        ValueError: If compression level is invalid

    Example:
        >>> compress("my_project/", "project_backup.7z", password="pwd123")
    """
    with SevenZipArchive(
        archive, mode="w", progress_callback=progress_callback
    ) as arch:
        if password:
            arch.set_password(password)

        arch.compress(
            sources=sources,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            format=archive_format,
            compression_level=compression_level,
            encrypt_headers=encrypt_headers if archive_format == "7z" else False,
            delete_after_compression=DeleteMode.USE_TRASH if delete_after else DeleteMode.NONE
        )


def compress_as_7z(
    archive: PathLike,
    sources: List[PathLike],
    password: Optional[str] = None,
    compression_level: int = 5,
    encrypt_headers: bool = False,
    exclude_patterns: Optional[List[str]] = None,
    include_patterns: Optional[List[str]] = None,
    delete_after: bool = False,
    progress_callback: Optional[ProgressCallback] = None,
) -> None:
    """
    Create a 7z archive with optional compression and encryption.

    Args:
        archive: Path to the output archive file
        sources: List of files and/or directories to compress
        password: Optional password for encryption
        compression_level: Compression level (0=store, 5=normal, 9=maximum)
        encrypt_headers: Whether to encrypt archive headers (requires password)
        exclude_patterns: List of glob patterns for files to exclude
        include_patterns: List of glob patterns for files to include
        delete_after: Whether to delete source files after compression
        progress_callback: Optional callback for progress updates
        
    Raises:
        ValueError: If compression level is invalid

    Example:
        >>> # Simple compression
        >>> compress_as_7z("backup.7z", ["documents/", "photos/"])
        >>>
        >>> # Compressed backup with encryption
        >>> compress_as_7z(
        ...     "secure.7z",
        ...     ["sensitive_data/"],
        ...     password="mypassword",
        ...     compression_level=9,
        ...     encrypt_headers=True,
        ...     delete_after=False
        ... )
    """
    delete_mode = DeleteMode.USE_TRASH if delete_after else DeleteMode.NONE

    with SevenZipArchive(
        archive, mode="w", progress_callback=progress_callback
    ) as arch:
        if password:
            arch.set_password(password)

        arch.compress(
            sources=sources,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            format="7z",
            compression_level=compression_level,
            encrypt_headers=encrypt_headers,
            delete_after_compression=delete_mode,
        )


def compress_as_zip(
    archive: PathLike,
    sources: List[PathLike],
    password: Optional[str] = None,
    compression_level: int = 5,
    exclude_patterns: Optional[List[str]] = None,
    include_patterns: Optional[List[str]] = None,
    delete_after: bool = False,
    progress_callback: Optional[ProgressCallback] = None,
) -> None:
    """
    Create a ZIP archive with optional compression and encryption.

    This is similar to compress_as_7z but produces ZIP format instead.

    Args:
        archive: Path to the output archive file
        sources: List of files and/or directories to compress
        password: Optional password for encryption
        compression_level: Compression level (0=store, 5=normal, 9=maximum)
        exclude_patterns: List of glob patterns for files to exclude
        include_patterns: List of glob patterns for files to include
        delete_after: Whether to delete source files after compression
        progress_callback: Optional callback for progress updates
        
    Raises:
        ValueError: If compression level is invalid

    Example:
        >>> # Simple ZIP creation
        >>> compress_as_zip("archive.zip", ["documents/"])
        >>>
        >>> # Encrypted ZIP
        >>> compress_as_zip(
        ...     "archive.zip",
        ...     ["confidential/"],
        ...     password="secret123"
        ... )
    """
    delete_mode = DeleteMode.USE_TRASH if delete_after else DeleteMode.NONE

    with SevenZipArchive(
        archive, mode="w", progress_callback=progress_callback
    ) as arch:
        if password:
            arch.set_password(password)

        arch.compress(
            sources=sources,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            format="zip",
            compression_level=compression_level,
            delete_after_compression=delete_mode,
        )


# ============================================================================
# Utility Functions
# ============================================================================


def get_archive_size(archive: PathLike) -> int:
    """
    Get the size of an archive file in bytes.

    Args:
        archive: Path to the archive file

    Returns:
        Size in bytes

    Example:
        >>> size = get_archive_size("backup.7z")
        >>> print(f"Archive size: {size / (1024**2):.2f} MB")
    """
    return Path(archive).stat().st_size


def archive_exists(archive: PathLike) -> bool:
    """
    Check if an archive file exists.

    Args:
        archive: Path to the archive file

    Returns:
        True if archive exists, False otherwise

    Example:
        >>> if archive_exists("backup.7z"):
        ...     print("Backup found")
    """
    return Path(archive).exists()