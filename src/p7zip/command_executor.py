"""
7-Zip command execution and progress monitoring.

This module handles the execution of 7-Zip commands, including real-time
progress monitoring, error handling, and output parsing.
"""

import re
import subprocess
from typing import List, Optional

from .exceptions import (
    BinaryNotFoundError,
    CannotOpenArchiveError,
    CRCFailedError,
    InvalidPasswordError,
    SevenZipExecutionError,
)
from .types import PathLike, ProgressCallback


def execute_7z_command_with_output(
    command_args: List[str],
    working_directory: Optional[PathLike] = None,
) -> subprocess.CompletedProcess:
    """
    Execute a 7-Zip command and capture its output.

    This function runs a 7z command and captures both stdout and stderr
    outputs, returning them in a CompletedProcess object.

    Args:
        command_args: List of command arguments to pass to 7z (e.g., ["l", "archive.7z"])
        working_directory: Optional working directory for command execution
    Returns:
        CompletedProcess: Contains return code, stdout, and stderr
    Raises:
        BinaryNotFoundError: If 7z binary path is not configured
        CannotOpenArchiveError: If the archive cannot be opened
        InvalidPasswordError: If the password is incorrect
        CRCFailedError: If CRC verification fails
        SevenZipExecutionError: For other execution errors
    """
    from .binary import _BINARY_PATH

    if not _BINARY_PATH:
        raise BinaryNotFoundError(
            "7-Zip binary path is not set. "
            "Call set_binary_path() or auto_detect_binary() first."
        )

    full_command = [_BINARY_PATH] + command_args

    # print("Executing command:", " ".join(full_command))

    try:
        completed_process = subprocess.run(
            full_command,
            cwd=working_directory,
            capture_output=True,
            text=True,
            check=False,  # Don't raise automatically, we handle errors manually
        )
        
        # Handle non-zero exit codes
        if completed_process.returncode != 0:
            _handle_execution_error(completed_process.returncode, completed_process.stderr)
        
        return completed_process
    except (CannotOpenArchiveError, InvalidPasswordError, CRCFailedError):
        # Re-raise specific exceptions unchanged
        raise
    except Exception as e:
        # Wrap unexpected exceptions
        raise SevenZipExecutionError(-1, str(e)) from e


def execute_7z_command(
    command_args: List[str],
    archivename: str,
    working_directory: Optional[PathLike] = None,
    progress_callback: Optional[ProgressCallback] = None,
) -> int:
    """
    Execute a 7-Zip command with progress monitoring and error handling.

    This function runs a 7z command, optionally reports progress updates via
    a callback, and translates 7z error codes into specific Python exceptions.

    Args:
        command_args: List of command arguments to pass to 7z (e.g., ["a", "archive.7z", "file.txt"])
        archivename: Name of compressed file
        working_directory: Optional working directory for command execution
        progress_callback: Optional callback for progress updates

    Returns:
        Exit code from the 7z process (0 indicates success)

    Raises:
        BinaryNotFoundError: If 7z binary path is not configured
        CannotOpenArchiveError: If the archive cannot be opened
        InvalidPasswordError: If the password is incorrect
        CRCFailedError: If CRC verification fails
        SevenZipExecutionError: For other execution errors

    Example:
        >>> execute_7z_command(["a", "backup.7z", "data/"], progress_callback=my_callback)
        0
    """
    from .binary import _BINARY_PATH

    if not _BINARY_PATH:
        raise BinaryNotFoundError(
            "7-Zip binary path is not set. "
            "Call set_binary_path() or auto_detect_binary() first."
        )

    try:
        # Configure 7z to output progress to stdout and suppress normal output
        progress_flags = ["-bsp1", "-bso0"]
        full_command = [_BINARY_PATH] + command_args + progress_flags

        # print("Executing command:", " ".join(full_command))

        # Start the 7z process
        process = subprocess.Popen(
            full_command,
            cwd=working_directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,  # Unbuffered - required for real-time progress updates
        )

        # Monitor and report progress if callback provided
        if progress_callback:
            _monitor_progress(archivename, process, progress_callback)

        # Wait for process to complete
        return_code = process.wait()

        # Handle non-zero exit codes
        if return_code != 0:
            stderr_text = process.stderr.read().decode("utf-8", errors="ignore")  # type: ignore
            _handle_execution_error(return_code, stderr_text)

        return return_code

    except (CannotOpenArchiveError, InvalidPasswordError, CRCFailedError):
        # Re-raise specific exceptions unchanged
        raise
    except Exception as e:
        # Wrap unexpected exceptions
        raise SevenZipExecutionError(-1, str(e)) from e


def _monitor_progress(
    archivename: str,
    process: subprocess.Popen,
    progress_callback: ProgressCallback,
) -> None:
    """
    Monitor 7z progress output and forward updates to callback.

    7-Zip writes progress in a proprietary format using backspace characters
    (\\x08) to overwrite lines in-place. This function reads output byte-by-byte
    to capture progress updates as soon as they're written.

    Args:
        archivename: Name of compressed file
        process: The running 7z subprocess
        progress_callback: Callback function to receive progress updates

    Progress Format:
        7z outputs progress lines like: "T filename.txt 45%"
        Where:
        - T/U/-/+/./= are operation indicators
        - filename.txt is the file being processed
        - 45% is the completion percentage
    """
    # Regex pattern to extract filename and percentage from progress output
    progress_pattern = re.compile(
        r"^(?:\d+\s*)?(?:[TU\-\.\+=]\s*)*(?P<filename>.+?)\s+(?P<percentage>\d+)%$"
    )

    buffer = b""
    last_filename = ""
    last_percentage = 0

    while True:
        # Read one byte at a time for real-time updates
        byte = process.stdout.read(1)  # type: ignore
        if not byte:
            break  # EOF - process finished

        # Skip backspace characters (7z uses these to overwrite output)
        if byte == b"\x08":
            continue

        buffer += byte

        # A '%' character signals the end of a progress line
        if byte == b"%":
            try:
                # Decode and clean the buffer
                text = buffer.decode("utf-8", errors="ignore")
                text = text.replace("\x08", "")  # Remove stray backspaces
                text = " ".join(text.split())  # Normalize whitespace

                # Only parse lines containing operation indicators
                if not "M Scan" in text and any(
                    indicator in text for indicator in ("T", "U", "-", "+", "=", ".")
                ):
                    match = progress_pattern.match(text)
                    if match:
                        last_filename = match.group("filename").strip()
                        last_percentage = int(match.group("percentage"))
                        progress_callback(archivename, last_percentage, last_filename)

            except (UnicodeDecodeError, ValueError):
                # Silently skip malformed lines
                pass
            finally:
                buffer = b""  # Reset buffer for next line

    # Ensure callback fires at 100% even if 7z didn't emit final update
    if last_percentage < 100:
        progress_callback(archivename, 100, last_filename)


def _handle_execution_error(return_code: int, stderr_output: str) -> None:
    """
    Translate 7z error output into specific Python exceptions.

    Analyzes the stderr output from a failed 7z command and raises
    the appropriate exception type with a helpful error message.

    Args:
        return_code: Exit code from the 7z process
        stderr_output: Standard error output from 7z

    Raises:
        CannotOpenArchiveError: For archive opening failures
        InvalidPasswordError: For password-related errors
        CRCFailedError: For CRC verification failures
        SevenZipExecutionError: For unknown errors
    """
    # Check for specific error patterns in stderr
    if "Wrong password" in stderr_output:
        raise InvalidPasswordError(
            "Invalid password provided for the encrypted archive."
        )
        
    if "CRC Failed" in stderr_output:
        # Extract list of files that failed CRC check
        failed_files = re.findall(r"CRC Failed\s+:\s+(.*)", stderr_output)
        raise CRCFailedError(failed_files)
    
    if "Cannot open" in stderr_output:
            raise CannotOpenArchiveError(
                "Cannot open the specified archive. "
                "It may be corrupted or not a valid archive format."
            )
            
    # Unknown error - raise generic exception with details
    raise SevenZipExecutionError(return_code, stderr_output)
