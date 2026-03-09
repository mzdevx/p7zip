"""
Core archive operations for 7-Zip.

This module provides the main SevenZipArchive class for creating, extracting,
testing and get info from 7-Zip archives with support for encryption, compression, and
pattern-based file filtering.
"""

import re
import sys
from pathlib import Path
from typing import List, Literal, Optional, Union

from .command_executor import execute_7z_command, execute_7z_command_with_output
from .enums import (
    CompressionLevel,
    CompressionMethod,
    DeleteMode,
    OverwriteMode,
)
from .exceptions import CRCFailedError
from .filesystem_utils import delete_path
from .pattern_filter import filter_paths_by_patterns, prepare_sources_and_exclusions
from .types import CompletionCallback, PathLike, ProgressCallback


class SevenZipArchive:
    """
    High-level interface for 7-Zip archive operations.

    This class provides methods for compressing files into archives, extracting
    archives, and testing archive integrity. It supports encryption, custom
    compression levels, pattern-based filtering, and progress callbacks.

    Attributes:
        file: Path to the archive file
        progress_callback: Optional callback for progress updates
        completion_callback: Optional callback for operation completion

    Example:
        >>> # Create an archive
        >>> archive = SevenZipArchive("backup.7z", mode="w")
        >>> archive.set_password("secret123")
        >>> archive.compress(["documents/", "photos/"], exclude_patterns=["*.tmp"])
        >>>
        >>> # Extract an archive
        >>> archive = SevenZipArchive("backup.7z", mode="r")
        >>> archive.set_password("secret123")
        >>> archive.extract("restore/", overwrite_mode=OverwriteMode.SKIP_EXISTING)
        >>>
        >>> # Test archive integrity
        >>> archive = SevenZipArchive("backup.7z", mode="r")
        >>> failed_files = archive.test_integrity()
        >>> if failed_files:
        ...     print(f"CRC errors in: {failed_files}")
    """

    def __init__(
        self,
        file: PathLike,
        mode: Literal["r", "w"] = "r",
        progress_callback: Optional[ProgressCallback] = None,
        completion_callback: Optional[CompletionCallback] = None,
    ):
        """
        Initialize a SevenZipArchive instance.

        Args:
            file: Path to the archive file (for creation or extraction)
            mode: Mode of operation - 'r' for read/extract, 'w' for write/compress
            progress_callback: Optional callback function for progress updates.
                             Called with (archivename: str, percentage: int, filename: str)
            completion_callback: Optional callback function for operation completion.
                               Called with (archivename: str, message: str)

        Example:
            >>> def show_progress(archivename: str, percentage: int, filename: str) -> None:
            ...     print(f"[{percentage}%] {archivename}: Processing {filename}")
            ...
            >>> archive = SevenZipArchive("data.7z", progress_callback=show_progress)
        """
        self.file = Path(file)
        self.mode = mode
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback

        self._password: Optional[str] = None
        self._working_dir: Optional[Path] = None

    def __enter__(self) -> "SevenZipArchive":
        """Context manager entry point."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit point."""
        self.close()

    def close(self) -> None:
        """
        Close the archive.

        Note: p7zip doesn't maintain persistent file handles.
        """
        pass

    # -------------------------------------------------------------------------
    # Working Directory Management
    # -------------------------------------------------------------------------

    def set_working_directory(self, directory: PathLike) -> None:
        """
        Set the base directory for resolving relative paths.

        All relative paths in subsequent operations will be resolved against
        this directory. The directory is created if it doesn't exist.

        Args:
            directory: Path to the working directory (absolute or relative)

        Example:
            >>> archive = SevenZipArchive("backup.7z", mode="w")
            >>> archive.set_working_directory("/tmp/workspace")
            >>> archive.compress(["data/"])  # Resolves to /tmp/workspace/data/
        """
        self._working_dir = Path(directory).resolve()
        self._working_dir.mkdir(parents=True, exist_ok=True)

    def get_working_directory(self) -> Optional[Path]:
        """
        Get the currently configured working directory.

        Returns:
            The working directory Path, or None if not set

        Example:
            >>> archive = SevenZipArchive("backup.7z")
            >>> archive.set_working_directory("/tmp")
            >>> archive.get_working_directory()
            PosixPath('/tmp')
        """
        return self._working_dir

    def _resolve_path(self, path: PathLike) -> Path:
        """
        Resolve a path to an absolute Path object.

        If a working directory is set and the path is relative, it will be
        resolved relative to the working directory. Otherwise, it's resolved
        relative to the current working directory.

        Args:
            path: File or directory path (absolute or relative)

        Returns:
            Fully resolved absolute Path object

        Example:
            >>> archive = SevenZipArchive("backup.7z")
            >>> archive.set_working_directory("/data")
            >>> archive._resolve_path("file.txt")
            PosixPath('/data/file.txt')
        """
        resolved = Path(path).expanduser()
        if not resolved.is_absolute() and self._working_dir:
            resolved = self._working_dir / resolved
        return resolved.resolve()

    # -------------------------------------------------------------------------
    # Password Management
    # -------------------------------------------------------------------------

    def set_password(self, password: str) -> None:
        """
        Set the password for encryption or decryption operations.

        This password will be used for:
        - Encrypting archives during compression
        - Decrypting archives during extraction
        - Accessing password-protected archives during testing

        Args:
            password: Password string for encryption/decryption

        Example:
            >>> archive = SevenZipArchive("secure.7z", mode="w")
            >>> archive.set_password("MySecretPassword123")
            >>> archive.compress(["sensitive_data/"], encrypt_headers=True)
        """
        self._password = password

    # -------------------------------------------------------------------------
    # Validation Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _validate_volume_size(volume_size: Optional[str]) -> Optional[str]:
        """
        Validate the volume size string for multi-volume archives.

        Args:
            volume_size: Volume size string (e.g., "100m", "1g")

        Returns:
            Validated volume size string or None if volume_size is None

        Raises:
            ValueError: If the volume size format is invalid

        Example:
            >>> SevenZipArchive._validate_volume_size("200m")
            '200m'
            >>> SevenZipArchive._validate_volume_size("2G")
            '2g'
        """
        if volume_size is None:
            return None

        volume_size = volume_size.lower()
        if not re.match(r"^\d+[bkmg]$", volume_size):
            raise ValueError(
                f"Invalid volume size: {volume_size}. "
                "Must be a number followed by 'b', 'k', 'm', or 'g'."
            )

        return volume_size

    @staticmethod
    def _validate_compression_level(level: Union[CompressionLevel, int]) -> int:
        """
        Validate and convert compression level to integer.

        Args:
            level: Compression level as CompressionLevel enum or int (0-9)

        Returns:
            Validated compression level as integer

        Raises:
            ValueError: If integer level is not between 0 and 9

        Example:
            >>> SevenZipArchive._validate_compression_level(CompressionLevel.ULTRA)
            9
            >>> SevenZipArchive._validate_compression_level(5)
            5
        """
        if isinstance(level, CompressionLevel):
            return level.value

        if not 0 <= level <= 9:
            raise ValueError(
                f"Invalid compression level: {level}. "
                "Must be between 0 (store) and 9 (ultra)."
            )
        return level

    # -------------------------------------------------------------------------
    # Compression
    # -------------------------------------------------------------------------

    def compress(
        self,
        sources: List[PathLike],
        exclude_patterns: Optional[List[str]] = None,
        include_patterns: Optional[List[str]] = None,
        volume_size: Optional[str] = None,
        format: Optional[str] = None,
        compression_level: Union[CompressionLevel, int] = CompressionLevel.NORMAL,
        compression_method: Optional[Union[CompressionMethod, str]] = None,
        encrypt_headers: bool = False,
        delete_after_compression: DeleteMode = DeleteMode.NONE,
    ) -> None:
        """
        Compress files and directories into an archive.

        Creates a 7-Zip archive from the specified sources with support for
        pattern-based filtering, encryption, custom compression, and multi-volume
        archives.

        Args:
            sources: List of files and/or directories to compress
            exclude_patterns: Optional list of glob patterns for files to exclude.
                            Takes priority over include_patterns.
            include_patterns: Optional list of glob patterns for files to include.
                            If specified, only matching files are included.
            volume_size: Optional volume size for splitting archives (e.g., "100m", "1g")
            format: Optional archive format (e.g., "7z", "zip"). If None, inferred from filename
            compression_level: Compression level (0-9 or CompressionLevel enum)
            compression_method: Optional compression algorithm (e.g., "lzma2", "deflate")
            encrypt_headers: If True, encrypt archive headers (requires password)
            delete_after_compression: Whether to delete source files after compression

        Pattern Matching:
            - Patterns with "/" match full relative paths
            - Patterns without "/" match filenames only
            - Exclude patterns override include patterns
            - Empty directories are always excluded
            
        Raises:
            RuntimeError: If archive is not opened in write mode
            ValueError: If compression level or volume size is invalid

        Example:
            >>> archive = SevenZipArchive("backup.7z", mode="w")
            >>> archive.set_password("secret")
            >>> archive.compress(
            ...     sources=["documents/", "photos/"],
            ...     exclude_patterns=["*.tmp", "*.log", "*/cache/*"],
            ...     include_patterns=["*.pdf", "*.jpg", "*.png"],
            ...     compression_level=CompressionLevel.MAXIMUM,
            ...     encrypt_headers=True,
            ...     volume_size="100m",
            ...     delete_after_compression=DeleteMode.USE_TRASH,
            ... )
        """
        # Validate mode
        if self.mode != "w":
            raise RuntimeError(
                "Archive not opened in write mode. "
                "Please initialize with mode='w' to compress files."
            )

        # Validate compression level
        compression_level_value = self._validate_compression_level(compression_level)

        # Validate volume size
        volume_size = self._validate_volume_size(volume_size)

        archive_path = self._resolve_path(self.file)

        # Build base 7z command
        command = ["a", str(archive_path)]
        command.append(f"-mx={compression_level_value}")

        # Add compression method if specified
        if compression_method:
            method_value = (
                compression_method.value
                if isinstance(compression_method, CompressionMethod)
                else compression_method
            )
            command.append(f"-m0={method_value}")

        # Add archive format if specified
        if format:
            command.append(f"-t{format}")

        # Add volume size for multi-volume archives
        if volume_size:
            command.append(f"-v{volume_size}")

        # Add password and encryption settings
        if self._password:
            command.append(f"-p{self._password}")

        if encrypt_headers:
            command.append("-mhe=on")

        # Resolve source paths
        resolved_sources = [self._resolve_path(source) for source in sources]

        # Apply pattern filtering if patterns are specified
        if include_patterns or exclude_patterns:
            filter_result = filter_paths_by_patterns(
                resolved_sources,
                include_patterns,
                exclude_patterns,
            )

            exclusions, filtered_sources = prepare_sources_and_exclusions(
                resolved_sources, filter_result
            )

            if not filtered_sources:
                if self.completion_callback:
                    self.completion_callback(
                        archive_path.name,
                        "No files to compress. Operation skipped.",
                    )
                return

            # Add exclusion patterns to command
            for exclusion in exclusions:
                command.append(f"-x!{exclusion}")

            # Add filtered source paths
            for source in filtered_sources:
                command.append(str(source))

            resolved_sources = filter_result[0]

        else:
            # No filtering - add all sources directly
            for source in resolved_sources:
                command.append(str(source))

        # Execute compression command
        result = execute_7z_command(
            command,
            archive_path.name,
            progress_callback=self.progress_callback,
        )

        if result == 0 and delete_after_compression != DeleteMode.NONE:
            use_trash = delete_after_compression == DeleteMode.USE_TRASH
            for source in resolved_sources:
                try:
                    delete_path(source, use_trash=use_trash)
                except Exception as e:
                    print(
                        f"Warning: Failed to delete source '{source}': {e}",
                        file=sys.stderr,
                    )

        # Trigger completion callback if set
        if self.completion_callback:
            status = "successfully" if result == 0 else "with errors"
            self.completion_callback(
                archive_path.name, f"Compression completed {status}."
            )

    # -------------------------------------------------------------------------
    # Extraction
    # -------------------------------------------------------------------------

    def extract(
        self,
        destination: PathLike = ".",
        exclude_patterns: Optional[List[str]] = None,
        exclude_recursive_patterns: bool = True,
        include_patterns: Optional[List[str]] = None,
        include_recursive_patterns: bool = True,
        specific_files_or_dirs: Optional[List[str]] = None,
        recursive: bool = True,
        delete_after_extraction: DeleteMode = DeleteMode.NONE,
        overwrite_mode: OverwriteMode = OverwriteMode.OVERWRITE_ALL,
        preserve_paths: bool = True,
    ) -> Optional[List[str]]:
        """
        Extract files from an archive.

        Extracts the archive contents to the specified destination with support
        for pattern filtering, selective extraction, and various extraction modes.

        Args:
            destination: Directory to extract files to (created if doesn't exist)
            exclude_patterns: Optional list of patterns for files to skip
            exclude_recursive_patterns: If True, exclude patterns apply recursively
            include_patterns: Optional list of patterns for files to extract
            include_recursive_patterns: If True, include patterns apply recursively
            specific_files_or_dirs: Optional list of specific archive paths to extract
            recursive: If True, extract subdirectories when using specific_files_or_dirs
            delete_after_extraction: Whether to delete archive after extraction
            overwrite_mode: How to handle existing files (overwrite/skip/rename)
            preserve_paths: If True, preserve directory structure; if False, extract flat

        Returns:
            List of files that failed CRC check, or None if all files extracted successfully

        Raises:
            FileNotFoundError: If the archive file doesn't exist
            RuntimeError: If archive is not opened in read mode
            InvalidPasswordError: If the provided password is incorrect
            CannotOpenArchiveError: If the archive cannot be opened (e.g., due to corruption)
            SevenZipExecutionError: For other errors during extraction

        Example:
            >>> archive = SevenZipArchive("backup.7z", mode="r")
            >>> archive.set_password("secret")
            >>> failed = archive.extract(
            ...     destination="restore/",
            ...     include_patterns=["*.pdf"],
            ...     overwrite_mode=OverwriteMode.SKIP_EXISTING,
            ...     delete_after_extraction=DeleteMode.USE_TRASH
            ... )
            >>> if failed:
            ...     print(f"CRC errors: {failed}")
        """
        # Validate mode
        if self.mode != "r":
            raise RuntimeError(
                "Archive not opened in read mode. "
                "Please initialize with mode='r' to extract files."
            )

        archive_path = self._resolve_path(self.file)
        destination_path = self._resolve_path(destination)

        # Validate archive exists
        if not archive_path.exists():
            raise FileNotFoundError(
                f"Archive not found: {archive_path}. "
                "Please verify the archive path is correct."
            )

        # Build extraction command
        # 'x' preserves paths, 'e' extracts flat
        extraction_mode = "x" if preserve_paths else "e"
        command = [extraction_mode, str(archive_path)]
        command.append(f"-o{destination_path}")  # No space after -o

        # Add password (empty -p prevents interactive prompt)
        if self._password:
            command.append(f"-p{self._password}")
        else:
            command.append("-p")

        # Set overwrite behavior
        overwrite_value = (
            overwrite_mode.value
            if isinstance(overwrite_mode, OverwriteMode)
            else overwrite_mode
        )
        command.append(f"-ao{overwrite_value}")

        # Add include patterns
        if include_patterns:
            for pattern in include_patterns:
                recursive_flag = "r" if include_recursive_patterns else ""
                command.append(f"-i{recursive_flag}!{pattern}")

        # Add exclude patterns
        if exclude_patterns:
            for pattern in exclude_patterns:
                recursive_flag = "r" if exclude_recursive_patterns else ""
                command.append(f"-x{recursive_flag}!{pattern}")

        # Add specific files/directories to extract
        if specific_files_or_dirs:
            command.extend(specific_files_or_dirs)
            if recursive:
                command.append("-r")

        # Execute extraction
        failed_files: Optional[List[str]] = None
        try:
            execute_7z_command(
                command,
                archive_path.name,
                progress_callback=self.progress_callback,
            )
        except CRCFailedError as e:
            failed_files = e.failed_files

        # Handle post-extraction archive deletion
        if delete_after_extraction != DeleteMode.NONE and failed_files is None:
            use_trash = delete_after_extraction == DeleteMode.USE_TRASH
            try:
                delete_path(archive_path, use_trash=use_trash)
            except Exception as e:
                print(
                    f"Warning: Failed to delete archive '{archive_path}': {e}",
                    file=sys.stderr,
                )

        # Trigger completion callback
        if self.completion_callback:
            status = "with CRC errors" if failed_files else "successfully"
            self.completion_callback(
                archive_path.name, f"Extraction completed {status}."
            )

        return failed_files

    # -------------------------------------------------------------------------
    # Integrity Testing
    # -------------------------------------------------------------------------

    def test_integrity(self) -> Optional[List[str]]:
        """
        Test the integrity of the archive without extracting.

        Verifies that all files in the archive can be read and that their
        CRC checksums are valid. This is useful for detecting corruption
        without performing a full extraction.

        Returns:
            List of files that failed CRC check, or None if all files are valid

        Raises:
            FileNotFoundError: If the archive file doesn't exist
            RuntimeError: If archive is not opened in read mode
            InvalidPasswordError: If the provided password is incorrect
            CannotOpenArchiveError: If the archive cannot be opened (e.g., due to corruption)
            SevenZipExecutionError: For other errors during testing

        Example:
            >>> archive = SevenZipArchive("backup.7z", mode="r")
            >>> archive.set_password("secret")
            >>> failed_files = archive.test_integrity()
            >>> if failed_files:
            ...     print(f"Corrupted files detected: {failed_files}")
            ... else:
            ...     print("Archive integrity verified successfully")
        """
        # Validate mode
        if self.mode != "r":
            raise RuntimeError(
                "Archive not opened in read mode. "
                "Please initialize with mode='r' to test integrity."
            )

        archive_path = self._resolve_path(self.file)

        # Validate archive exists
        if not archive_path.exists():
            raise FileNotFoundError(
                f"Archive not found: {archive_path}. "
                "Please verify the archive path is correct."
            )

        # Build test command
        command = ["t", str(archive_path)]

        # Add password (empty -p prevents interactive prompt)
        if self._password:
            command.append(f"-p{self._password}")
        else:
            command.append("-p")

        # Execute test command
        failed_files: Optional[List[str]] = None
        try:
            execute_7z_command(
                command,
                archive_path.name,
                progress_callback=self.progress_callback,
            )
        except CRCFailedError as e:
            failed_files = e.failed_files

        # Trigger completion callback
        if self.completion_callback:
            status = "with CRC errors" if failed_files else "successfully"
            self.completion_callback(
                archive_path.name, f"Integrity test completed {status}."
            )

        return failed_files

    def list_contents(self) -> List[str]:
        """
        List the contents of the archive.

        Returns:
            List of files contained in the archive

        Raises:
            FileNotFoundError: If the archive file doesn't exist
            RuntimeError: If archive is not opened in read mode
            InvalidPasswordError: If the provided password is incorrect
            CannotOpenArchiveError: If the archive cannot be opened (e.g., due to corruption)
            SevenZipExecutionError: For other errors during listing

        Example:
            >>> archive = SevenZipArchive("backup.7z", mode="r")
            >>> contents = archive.list_contents()
            >>> for item in contents:
            ...     print(item)
        """
        # Validate mode
        if self.mode != "r":
            raise RuntimeError(
                "Archive not opened in read mode. "
                "Please initialize with mode='r' to list contents."
            )

        archive_path = self._resolve_path(self.file)

        # Validate archive exists
        if not archive_path.exists():
            raise FileNotFoundError(
                f"Archive not found: {archive_path}. "
                "Please verify the archive path is correct."
            )

        # Build list command
        command = ["l", "-slt", str(archive_path)]

        # Add password (empty -p prevents interactive prompt)
        if self._password:
            command.append(f"-p{self._password}")
        else:
            command.append("-p")

        # Execute list command and capture output
        completed_process = execute_7z_command_with_output(command)

        # Parse output to extract file list
        output_lines = completed_process.stdout.splitlines()

        file_list: List[str] = []
        
        if completed_process.returncode == 0:
            last_file_name = ""
            for line in output_lines:
                if line.startswith("Path = "):
                    last_file_name = line[len("Path = ") :].strip()
                elif line.startswith("Attributes = "):
                    attributes = line.partition(" = ")[2].strip()
                    if "A" in attributes:
                        file_list.append(last_file_name)

        if self.completion_callback:
            status = (
                "successfully" if completed_process.returncode == 0 else "with errors"
            )
            self.completion_callback(
                archive_path.name, f"Listed archive contents {status}."
            )

        return file_list
