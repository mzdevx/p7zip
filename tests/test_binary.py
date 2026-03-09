"""
Unit tests for the binary module.

This module tests binary path discovery, configuration, and validation
functionality for the 7-Zip executable.
"""

import os
import platform
from pathlib import Path
from unittest.mock import patch

import pytest

from p7zip.binary import (
    auto_detect_binary,
    get_binary_path,
    set_binary_path,
)
from p7zip.exceptions import BinaryNotFoundError

# =============================================================================
# Binary Path Configuration Tests
# =============================================================================


class TestSetBinaryPath:
    """Test suite for set_binary_path() function."""
    
    @pytest.mark.unit
    def test_set_valid_binary_path(self, fake_executable_binary):
        """
        Test setting a valid binary path.
        
        Verifies that a valid executable path is accepted and stored.
        Works on Windows, macOS, and Linux.
        """
        # Set the binary path
        set_binary_path(fake_executable_binary)
        
        # Verify it was set correctly
        result = get_binary_path()
        assert result == str(fake_executable_binary)
    
    @pytest.mark.unit
    def test_set_binary_path_with_expansion(self, temp_dir, monkeypatch, fake_executable_binary):
        """
        Test setting binary path with environment variable expansion.
        
        Verifies that paths with $VAR and ~ are properly expanded.
        """
        # Set up environment variable
        monkeypatch.setenv("TEST_DIR", str(temp_dir))
        
        # Set binary using environment variable
        is_windows = platform.system().lower() == "windows"
        set_binary_path(f"$TEST_DIR/7z{'.exe' if is_windows else ''}")
        
        # Verify expansion occurred
        result = get_binary_path()
        assert result == str(fake_executable_binary)
    
    @pytest.mark.unit
    def test_set_binary_path_nonexistent_file(self):
        """
        Test setting path to a non-existent file.
        
        Verifies that BinaryNotFoundError is raised for missing files.
        """
        with pytest.raises(BinaryNotFoundError) as exc_info:
            set_binary_path("/nonexistent/path/to/7z")
        
        assert "not found at specified path" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_set_binary_path_not_executable(self, temp_dir):
        """
        Test setting path to a non-executable file.
        
        Verifies that BinaryNotFoundError is raised when file exists
        but lacks execute permissions.
        """
        # Create a non-executable file
        non_executable = temp_dir / "7z"
        non_executable.write_text("not executable")
        if not platform.system().lower() == "windows":
            non_executable.chmod(0o644)  # No execute permission
        
        with pytest.raises(BinaryNotFoundError) as exc_info:
            set_binary_path(non_executable)
        
        assert "not executable" in str(exc_info.value)
        assert "permissions" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_set_binary_path_as_string(self, fake_executable_binary):
        """
        Test setting binary path using string instead of Path object.
        
        Verifies that both string and Path objects are accepted.
        """
        # Pass as string
        set_binary_path(str(fake_executable_binary))
        
        result = get_binary_path()
        assert result == str(fake_executable_binary)
    
    @pytest.mark.unit
    def test_set_binary_path_absolute_path(self, temp_dir, fake_executable_binary):
        """
        Test that set_binary_path stores absolute paths.
        
        Verifies that relative paths are converted to absolute.
        """
        # Change to temp directory and use relative path
        original_cwd = Path.cwd()
        try:
            os.chdir(temp_dir)
            is_windows = platform.system().lower() == "windows"
            set_binary_path(f".{os.sep}7z{'.exe' if is_windows else ''}")
            
            result = get_binary_path()
            assert result is not None
            assert Path(result).is_absolute()
            is_windows = platform.system().lower() == "windows"
            fake_executable_path = str(fake_executable_binary if is_windows else fake_executable_binary.resolve())
            assert result == fake_executable_path
        finally:
            os.chdir(original_cwd)


# =============================================================================
# Binary Path Retrieval Tests
# =============================================================================


class TestGetBinaryPath:
    """Test suite for get_binary_path() function."""
    
    @pytest.mark.unit
    def test_get_binary_path_when_not_set(self):
        """
        Test retrieving binary path when not configured.
        
        Verifies that None is returned when no path is set.
        """
        # The reset_binary_state fixture ensures clean state
        result = get_binary_path()
        assert result is None
    
    @pytest.mark.unit
    def test_get_binary_path_after_setting(self, fake_executable_binary):
        """
        Test retrieving binary path after configuration.
        
        Verifies that the set path is correctly retrieved.
        """
        set_binary_path(fake_executable_binary)
        result = get_binary_path()
        
        assert result is not None
        assert result == str(fake_executable_binary)


# =============================================================================
# Auto-Detection Tests
# =============================================================================


class TestAutoDetectBinary:
    """Test suite for auto_detect_binary() function."""
    
    @pytest.mark.unit
    @patch("shutil.which")
    @patch("platform.system")
    def test_auto_detect_on_linux(self, mock_platform, mock_which):
        """
        Test auto-detection on Linux systems.
        
        Verifies that Linux binary names (7zz) are searched.
        """
        mock_platform.return_value = "Linux"
        mock_which.return_value = "/usr/bin/7zz"
        
        auto_detect_binary()
        
        # Verify 7zz was searched for first
        assert mock_which.call_args_list[0][0][0] == "7zz"
        assert get_binary_path() == "/usr/bin/7zz"
    
    @pytest.mark.unit
    @patch("shutil.which")
    @patch("platform.system")
    def test_auto_detect_on_windows(self, mock_platform, mock_which):
        """
        Test auto-detection on Windows systems.
        
        Verifies that Windows binary names (7z.exe) are searched.
        """
        mock_platform.return_value = "Windows"
        mock_which.return_value = "C:\\Program Files\\7-Zip\\7z.exe"
        
        auto_detect_binary()
        
        # Verify 7z.exe was searched for
        assert mock_which.call_args_list[0][0][0] == "7z.exe"
    
    @pytest.mark.unit
    @patch("shutil.which")
    @patch("platform.system")
    def test_auto_detect_fallback_to_legacy(self, mock_platform, mock_which):
        """
        Test auto-detection fallback to legacy binaries.
        
        Verifies that 7za is used when newer binaries aren't found.
        """
        mock_platform.return_value = "Linux"
        
        # Mock which() to return None for 7zz, but path for 7za
        def which_side_effect(name):
            if name == "7za":
                return "/usr/bin/7za"
            return None
        
        mock_which.side_effect = which_side_effect
        
        auto_detect_binary()
        
        # Should have tried 7zz first, then 7za
        assert get_binary_path() == "/usr/bin/7za"
    
    @pytest.mark.unit
    @patch("p7zip.binary._is_executable")
    @patch("shutil.which")
    @patch("platform.system")
    def test_auto_detect_windows_common_paths(
        self, mock_platform, mock_which, mock_is_executable
    ):
        """
        Test auto-detection using Windows common installation paths.
        
        Verifies that standard Windows installation directories are checked
        when binary is not in PATH.
        """
        mock_platform.return_value = "Windows"
        mock_which.return_value = None  # Not in PATH
        
        # Mock _is_executable to return True only for the first common path
        def is_executable_side_effect(path):
            return str(path) == r"C:\Program Files\7-Zip\7z.exe"
        
        mock_is_executable.side_effect = is_executable_side_effect
        
        auto_detect_binary()
        
        # Should have found the binary in common paths
        assert get_binary_path() == r"C:\Program Files\7-Zip\7z.exe"
    
    @pytest.mark.unit
    @patch("shutil.which")
    @patch("platform.system")
    def test_auto_detect_binary_not_found(self, mock_platform, mock_which):
        """
        Test auto-detection when no binary is found.
        
        Verifies that BinaryNotFoundError is raised with helpful message.
        """
        mock_platform.return_value = "Linux"
        mock_which.return_value = None
        
        with pytest.raises(BinaryNotFoundError) as exc_info:
            auto_detect_binary()
        
        error_msg = str(exc_info.value)
        assert "not found in PATH" in error_msg
        assert "install 7-Zip" in error_msg or "set_binary_path()" in error_msg
    
    @pytest.mark.unit
    @patch("shutil.which")
    @patch("platform.system")
    def test_auto_detect_sets_global_path(self, mock_platform, mock_which):
        """
        Test that auto-detection sets the global binary path.
        
        Verifies that the detected path is stored and retrievable.
        """
        mock_platform.return_value = "Darwin"  # macOS
        mock_which.return_value = "/opt/homebrew/bin/7zz"
        
        auto_detect_binary()
        
        result = get_binary_path()
        assert result == "/opt/homebrew/bin/7zz"
    
    @pytest.mark.unit
    @patch("shutil.which")
    @patch("platform.system")
    def test_auto_detect_case_insensitive_platform(self, mock_platform, mock_which):
        """
        Test auto-detection with mixed-case platform names.
        
        Verifies that platform detection is case-insensitive.
        """
        mock_platform.return_value = "WINDOWS"  # All caps
        mock_which.return_value = "C:\\7z.exe"
        
        # Should not raise exception
        auto_detect_binary()
        
        assert get_binary_path() is not None