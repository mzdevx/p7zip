"""
Type definitions and protocols for 7-Zip archive operations.

This module defines callback protocols and type aliases used throughout
the library for type safety and clear API contracts.
"""

from pathlib import Path
from typing import Protocol, Union, runtime_checkable


@runtime_checkable
class ProgressCallback(Protocol):
    """
    Protocol for progress reporting callback functions.

    Progress callbacks are invoked during archive operations (compression,
    extraction, testing) to report real-time progress updates. They receive
    the name of the compressed file, the current percentage,
    and the name of the file (within the compressed file) that is being processed.

    Args:
        archivename: Name of compressed file
        percentage: Progress percentage (0-100)
        filename: Name of the file currently being processed

    Example:
        >>> def show_progress(archivename: str, percentage: int, filename: str) -> None:
        ...     print(f"[{percentage}%] Processing: {filename} in {archivename}")
        ...
        >>> archive = SevenZipArchive("data.7z", progress_callback=show_progress)
        >>> archive.compress(["folder/"])
    """

    def __call__(
        self, archivename: str, percentage: int, filename: str
    ) -> None:
        """
        Execute progress callback with current status.

        Args:
            archivename: Name of compressed file
            percentage: Current progress percentage (0-100)
            filename: Name of file being processed
        """
        ...


@runtime_checkable
class CompletionCallback(Protocol):
    """
    Protocol for operation completion callback functions.

    Completion callbacks are invoked when an archive operation finishes,
    whether successfully or with errors. They receive the name of the compressed
    file and message describing the operation outcome.

    Args:
        archivename: Name of compressed file
        message: Completion status message

    Example:
        >>> def on_complete(archivename: str, message: str) -> None:
        ...     print(f"Process archive: {archivename} finished. {message}")
        ...
        >>> archive = SevenZipArchive("backup.7z", completion_callback=on_complete)
        >>> archive.extract("output/")
    """

    def __call__(self, archivename: str, message: str) -> None:
        """
        Execute completion callback with status message.

        Args:
            archivename: Name of compressed file
            message: Message describing the operation outcome
        """
        ...


# Type alias for filesystem paths
PathLike = Union[str, Path]
"""Type alias for paths that can be either strings or Path objects."""
