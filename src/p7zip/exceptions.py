"""
Exception classes for 7-Zip archive operations.

This module defines all exception types that can be raised during archive
operations, providing clear error messages and structured error information.
"""

from typing import List


class SevenZipException(Exception):
    """
    Base exception for all 7-Zip related errors.

    All specific exceptions in this module inherit from this base class,
    allowing for broad exception handling when needed.
    """

    pass


class BinaryNotFoundError(SevenZipException):
    """
    Raised when the 7-Zip binary executable is not found.

    This exception occurs when:
    - The 7z binary is not in the system PATH
    - The specified binary path does not exist
    - The binary exists but is not executable
    """

    pass


class CannotOpenArchiveError(SevenZipException):
    """
    Raised when an archive file cannot be opened.

    This exception occurs when:
    - The archive file is corrupted
    - The file is not a valid archive format
    - The file format is not supported by 7-Zip
    """

    pass


class InvalidPasswordError(SevenZipException):
    """
    Raised when the provided password for an encrypted archive is incorrect.

    This exception occurs during extraction or testing operations when the
    archive is password-protected and the supplied password does not match.
    """

    pass


class CRCFailedError(SevenZipException):
    """
    Raised when CRC (Cyclic Redundancy Check) verification fails.

    This indicates data corruption or integrity issues with one or more
    files in the archive. The exception includes a list of all files
    that failed CRC verification.

    Attributes:
        failed_files: List of file paths that failed CRC verification
    """

    def __init__(self, failed_files: List[str]):
        """
        Initialize CRC failure exception.

        Args:
            failed_files: List of file paths that failed CRC verification
        """
        self.failed_files = failed_files
        files_str = "\n  - ".join(failed_files) if failed_files else "unknown"
        super().__init__(f"CRC check failed for files:\n  - {files_str}")


class SevenZipExecutionError(SevenZipException):
    """
    Raised when 7-Zip command execution fails with an unknown error.

    This is a catch-all exception for 7z process failures that don't match
    other specific exception types. It includes the exit code and error output
    for debugging purposes.

    Attributes:
        return_code: Exit code returned by the 7z process
        stderr_output: Standard error output from the 7z process
    """

    def __init__(self, return_code: int, stderr_output: str):
        """
        Initialize execution error exception.

        Args:
            return_code: Exit code from the 7z process
            stderr_output: Standard error output from 7z
        """
        self.return_code = return_code
        self.stderr_output = stderr_output
        super().__init__(
            f"7z execution failed with code {return_code}\n"
            f"Error output: {stderr_output}"
        )
