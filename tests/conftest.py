"""
Pytest configuration and shared fixtures for p7zip test suite.

This module provides common fixtures, utilities, and configuration
for all p7zip tests, including mock objects, temporary file creation,
and test data generators.
"""

import platform
import shutil
import tempfile
from pathlib import Path
from typing import Callable, Generator, List
from unittest.mock import Mock

import pytest


@pytest.fixture(scope="function")
def configure_binary_once():
    """
    Configure the 7z binary for a specific test.
    
    This fixture configures the binary and prevents it from being
    reset by reset_binary_state. Use this in test files that need
    actual binary execution (like test_core.py).
    
    Usage:
        def test_something(configure_binary_once):
            # Binary is now configured and won't be reset
            pass
    """
    from p7zip import binary as binary_module
    from p7zip.binary import auto_detect_binary
    
    # Save original reset behavior
    original_binary_path = binary_module._BINARY_PATH
    
    # Configure binary
    auto_detect_binary()
    
    yield
    
    # Restore original state after test
    binary_module._BINARY_PATH = original_binary_path
    
    
# =============================================================================
# Temporary File System Fixtures
# =============================================================================


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    Provide a temporary directory that is automatically cleaned up.
    
    Yields:
        Path to a temporary directory
        
    Example:
        >>> def test_example(temp_dir):
        ...     test_file = temp_dir / "test.txt"
        ...     test_file.write_text("content")
        ...     assert test_file.exists()
    """
    tmp_path = Path(tempfile.mkdtemp())
    try:
        yield tmp_path
    finally:
        if tmp_path.exists():
            shutil.rmtree(tmp_path, ignore_errors=True)


@pytest.fixture
def sample_files(temp_dir: Path) -> List[Path]:
    """
    Create a set of sample files for testing compression operations.
    
    Args:
        temp_dir: Temporary directory fixture
        
    Returns:
        List of created file paths
        
    Structure:
        temp_dir/
        ├── file1.txt (100 bytes)
        ├── file2.pdf (200 bytes)
        ├── file3.log (50 bytes)
        └── subdir/
            ├── file4.txt (150 bytes)
            └── file5.doc (300 bytes)
    """
    files = []
    
    # Create root level files
    file1 = temp_dir / "file1.txt"
    file1.write_text("x" * 100)
    files.append(file1)
    
    file2 = temp_dir / "file2.pdf"
    file2.write_bytes(b"PDF" * 67)  # ~200 bytes
    files.append(file2)
    
    file3 = temp_dir / "file3.log"
    file3.write_text("log" * 17)  # ~50 bytes
    files.append(file3)
    
    # Create subdirectory with files
    subdir = temp_dir / "subdir"
    subdir.mkdir()
    
    file4 = subdir / "file4.txt"
    file4.write_text("y" * 150)
    files.append(file4)
    
    file5 = subdir / "file5.doc"
    file5.write_bytes(b"DOC" * 100)  # ~300 bytes
    files.append(file5)
    
    return files


@pytest.fixture
def fake_executable_binary(temp_dir: Path) -> Path:
    """
    Create a fake executable binary file for testing binary path configuration.
    
    Args:
        temp_dir: Temporary directory fixture
    Returns:
        Path to the fake executable binary
    """
    is_windows = platform.system().lower() == "windows"
    fake_binary = temp_dir / f"7z{'.exe' if is_windows else ''}"
    if is_windows:
        fake_binary.write_bytes(b"MZ\x90\x00")
    else:
        fake_binary.write_text("#!/bin/sh")
        fake_binary.chmod(0o755)
    return fake_binary


@pytest.fixture
def empty_dir(temp_dir: Path) -> Path:
    """
    Create an empty directory for testing.
    
    Args:
        temp_dir: Temporary directory fixture
        
    Returns:
        Path to an empty directory
    """
    empty = temp_dir / "empty_folder"
    empty.mkdir()
    return empty


@pytest.fixture
def archive_path(temp_dir: Path) -> Path:
    """
    Provide a path for creating test archives.
    
    Args:
        temp_dir: Temporary directory fixture
        
    Returns:
        Path where test archive should be created
    """
    return temp_dir / "test_archive.7z"


# =============================================================================
# Mock Binary and Command Execution Fixtures
# =============================================================================


@pytest.fixture
def mock_binary_path(monkeypatch) -> str:
    """
    Mock the 7z binary path to avoid requiring actual installation.
    
    Args:
        monkeypatch: Pytest monkeypatch fixture
        
    Returns:
        Mocked binary path string
    """
    fake_binary_path = "/usr/bin/7z"
    
    # Mock the binary module's _BINARY_PATH global
    import p7zip.binary as binary_module
    monkeypatch.setattr(binary_module, "_BINARY_PATH", fake_binary_path)
    
    return fake_binary_path


@pytest.fixture
def mock_subprocess_run(monkeypatch):
    """
    Mock subprocess.run to avoid executing actual 7z commands.
    
    Returns:
        Mock object for subprocess.run
    """
    mock_run = Mock()
    mock_run.return_value = Mock(
        returncode=0,
        stdout="",
        stderr="",
    )
    
    import subprocess
    monkeypatch.setattr(subprocess, "run", mock_run)
    
    return mock_run


@pytest.fixture
def mock_subprocess_popen(monkeypatch):
    """
    Mock subprocess.Popen for testing progress monitoring.
    
    Returns:
        Mock object for subprocess.Popen
    """
    mock_process = Mock()
    mock_process.stdout = Mock()
    mock_process.stdout.read = Mock(side_effect=[b"", None])
    mock_process.stderr = Mock()
    mock_process.stderr.read = Mock(return_value=b"")
    mock_process.wait = Mock(return_value=0)
    
    mock_popen = Mock(return_value=mock_process)
    
    import subprocess
    monkeypatch.setattr(subprocess, "Popen", mock_popen)
    
    return mock_popen


# =============================================================================
# Callback Function Fixtures
# =============================================================================


@pytest.fixture
def progress_callback() -> Mock:
    """
    Create a mock progress callback for testing.
    
    Returns:
        Mock callable that tracks progress updates
    """
    return Mock()


@pytest.fixture
def completion_callback() -> Mock:
    """
    Create a mock completion callback for testing.
    
    Returns:
        Mock callable that tracks completion notifications
    """
    return Mock()


# =============================================================================
# Test Data Generators
# =============================================================================


@pytest.fixture
def create_test_archive(temp_dir: Path) -> Callable[[str, List[str]], Path]:
    """
    Factory fixture for creating test archives.
    
    Args:
        temp_dir: Temporary directory fixture
        
    Returns:
        Function that creates a test archive with specified files
        
    Example:
        >>> def test_example(create_test_archive):
        ...     archive = create_test_archive("test.7z", ["file1.txt", "file2.txt"])
        ...     assert archive.exists()
    """
    def _create_archive(archive_name: str, files: List[str]) -> Path:
        """
        Create a test archive file.
        
        Args:
            archive_name: Name of the archive file
            files: List of file names to include in metadata
            
        Returns:
            Path to the created archive
        """
        archive = temp_dir / archive_name
        # Create a dummy archive file for testing
        # (Not a real 7z archive, just for path/existence testing)
        archive.write_bytes(b"7z\xbc\xaf\x27\x1c")  # 7z file signature
        return archive
    
    return _create_archive


# =============================================================================
# Environment and System Fixtures
# =============================================================================


@pytest.fixture
def clean_environment(monkeypatch):
    """
    Provide a clean environment without system-specific variables.
    
    Args:
        monkeypatch: Pytest monkeypatch fixture
    """
    # Clear potentially interfering environment variables
    vars_to_remove = ["PATH", "HOME", "TEMP", "TMP"]
    for var in vars_to_remove:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture(autouse=True)
def reset_binary_state(monkeypatch):
    """
    Reset the binary module state before each test.
    
    This ensures tests don't interfere with each other through
    global state in the binary module.
    
    Args:
        monkeypatch: Pytest monkeypatch fixture
    """
    import p7zip.binary as binary_module
    monkeypatch.setattr(binary_module, "_BINARY_PATH", None)


# =============================================================================
# Parametrization Helpers
# =============================================================================


def generate_compression_levels():
    """
    Generate test parameters for compression levels.
    
    Returns:
        List of compression level integers (0-9)
    """
    return [0, 1, 3, 5, 7, 9]


def generate_archive_formats():
    """
    Generate test parameters for archive formats.
    
    Returns:
        List of archive format strings
    """
    return ["7z", "zip"]


# =============================================================================
# Custom Assertions
# =============================================================================


def assert_archive_contains(archive_path: Path, expected_files: List[str]) -> None:
    """
    Assert that an archive contains specific files.
    
    Note: This is a placeholder. In real tests with actual archives,
    you would use 7z to list contents.
    
    Args:
        archive_path: Path to the archive
        expected_files: List of expected file paths
        
    Raises:
        AssertionError: If archive doesn't contain expected files
    """
    assert archive_path.exists(), f"Archive does not exist: {archive_path}"
    # In real implementation, would execute: 7z l -slt {archive_path}
    # and parse output to verify files


def assert_files_exist(file_paths: List[Path]) -> None:
    """
    Assert that all specified files exist.
    
    Args:
        file_paths: List of file paths to check
        
    Raises:
        AssertionError: If any file doesn't exist
    """
    for file_path in file_paths:
        assert file_path.exists(), f"File does not exist: {file_path}"


def assert_directory_empty(dir_path: Path) -> None:
    """
    Assert that a directory is empty.
    
    Args:
        dir_path: Path to the directory
        
    Raises:
        AssertionError: If directory is not empty
    """
    assert dir_path.exists(), f"Directory does not exist: {dir_path}"
    assert dir_path.is_dir(), f"Path is not a directory: {dir_path}"
    contents = list(dir_path.iterdir())
    assert len(contents) == 0, f"Directory is not empty: {contents}"