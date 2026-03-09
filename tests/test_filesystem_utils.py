"""
Unit tests for the filesystem_utils module.

This module tests filesystem utilities including multi-volume archive
detection and path deletion functionality.
"""

from unittest.mock import patch

import pytest

from p7zip.filesystem_utils import (
    delete_path,
    _detect_archive_volumes,
    _find_rar_classic_volumes,
    _find_rar_part_volumes,
    _find_sequential_volumes,
)


# =============================================================================
# Sequential Volume Detection Tests
# =============================================================================


class TestFindSequentialVolumes:
    """Test suite for _find_sequential_volumes() function."""
    
    @pytest.mark.unit
    def test_detect_consecutive_volumes(self, temp_dir):
        """
        Test detection of consecutive numbered volumes.
        
        Verifies finding of .001, .002, .003 format volumes.
        """
        # Create sequential volume files
        base_name = "archive.7z"
        for i in range(1, 4):
            volume = temp_dir / f"{base_name}.{i:03d}"
            volume.write_bytes(b"volume data")
        
        volumes = _find_sequential_volumes(
            str(temp_dir),
            base_name,
            ".001"
        )
        
        assert len(volumes) == 3
        assert str(temp_dir / f"{base_name}.001") in volumes
        assert str(temp_dir / f"{base_name}.002") in volumes
        assert str(temp_dir / f"{base_name}.003") in volumes
    
    @pytest.mark.unit
    def test_detect_single_volume(self, temp_dir):
        """
        Test detection with only first volume present.
        
        Verifies behavior when only .001 exists.
        """
        base_name = "archive.7z"
        volume = temp_dir / f"{base_name}.001"
        volume.write_bytes(b"volume data")
        
        volumes = _find_sequential_volumes(
            str(temp_dir),
            base_name,
            ".001"
        )
        
        assert len(volumes) == 1
        assert str(volume) in volumes
    
    @pytest.mark.unit
    def test_detect_with_gaps(self, temp_dir):
        """
        Test detection stops at first gap.
        
        Verifies that missing volumes stop the search.
        """
        base_name = "archive.7z"
        (temp_dir / f"{base_name}.001").write_bytes(b"v1")
        (temp_dir / f"{base_name}.002").write_bytes(b"v2")
        # Skip .003
        (temp_dir / f"{base_name}.004").write_bytes(b"v4")
        
        volumes = _find_sequential_volumes(
            str(temp_dir),
            base_name,
            ".001"
        )
        
        # Should only find .001 and .002, then stop
        assert len(volumes) == 2
    
    @pytest.mark.unit
    def test_starting_from_different_index(self, temp_dir):
        """
        Test detection starting from volume other than .001.
        
        Verifies detection from arbitrary starting point.
        """
        base_name = "archive.7z"
        (temp_dir / f"{base_name}.005").write_bytes(b"v5")
        (temp_dir / f"{base_name}.006").write_bytes(b"v6")
        
        volumes = _find_sequential_volumes(
            str(temp_dir),
            base_name,
            ".005"
        )
        
        assert len(volumes) == 2


# =============================================================================
# RAR Classic Volume Detection Tests
# =============================================================================


class TestFindRarClassicVolumes:
    """Test suite for _find_rar_classic_volumes() function."""
    
    @pytest.mark.unit
    def test_detect_rar_volumes(self, temp_dir):
        """
        Test detection of RAR classic format volumes.
        
        Verifies finding of .rar, .r00, .r01 format.
        """
        base_name = "archive"
        
        # Create RAR header and volumes
        (temp_dir / f"{base_name}.rar").write_bytes(b"rar header")
        (temp_dir / f"{base_name}.r00").write_bytes(b"volume 0")
        (temp_dir / f"{base_name}.r01").write_bytes(b"volume 1")
        
        volumes = _find_rar_classic_volumes(
            str(temp_dir),
            base_name,
            ".r00"
        )
        
        assert len(volumes) >= 2  # At least .r00 and .r01
        assert str(temp_dir / f"{base_name}.r00") in volumes
        assert str(temp_dir / f"{base_name}.r01") in volumes
    
    @pytest.mark.unit
    def test_include_rar_header(self, temp_dir):
        """
        Test that .rar header file is included.
        
        Verifies that main .rar file is detected.
        """
        base_name = "archive"
        
        (temp_dir / f"{base_name}.rar").write_bytes(b"header")
        (temp_dir / f"{base_name}.r00").write_bytes(b"v0")
        
        volumes = _find_rar_classic_volumes(
            str(temp_dir),
            base_name,
            ".r00"
        )
        
        # Should include both .rar header and .r00
        assert str(temp_dir / f"{base_name}.rar") in volumes
        assert str(temp_dir / f"{base_name}.r00") in volumes
    
    @pytest.mark.unit
    def test_rar_volumes_without_header(self, temp_dir):
        """
        Test detection without .rar header file.
        
        Verifies handling when only .rNN files exist.
        """
        base_name = "archive"
        
        (temp_dir / f"{base_name}.r00").write_bytes(b"v0")
        (temp_dir / f"{base_name}.r01").write_bytes(b"v1")
        
        volumes = _find_rar_classic_volumes(
            str(temp_dir),
            base_name,
            ".r00"
        )
        
        # Should still find .rNN files
        assert len(volumes) == 2


# =============================================================================
# RAR Part Volume Detection Tests
# =============================================================================


class TestFindRarPartVolumes:
    """Test suite for _find_rar_part_volumes() function."""
    
    @pytest.mark.unit
    def test_detect_rar_part_volumes(self, temp_dir):
        """
        Test detection of RAR part format volumes.
        
        Verifies finding of .part1.rar, .part2.rar format.
        """
        base_name = "archive"
        
        (temp_dir / f"{base_name}.part1.rar").write_bytes(b"part 1")
        (temp_dir / f"{base_name}.part2.rar").write_bytes(b"part 2")
        (temp_dir / f"{base_name}.part3.rar").write_bytes(b"part 3")
        
        volumes = _find_rar_part_volumes(str(temp_dir), base_name)
        
        assert len(volumes) == 3
        assert str(temp_dir / f"{base_name}.part1.rar") in volumes
        assert str(temp_dir / f"{base_name}.part2.rar") in volumes
        assert str(temp_dir / f"{base_name}.part3.rar") in volumes
    
    @pytest.mark.unit
    def test_detect_single_part(self, temp_dir):
        """
        Test detection with single part file.
        """
        base_name = "archive"
        (temp_dir / f"{base_name}.part1.rar").write_bytes(b"part 1")
        
        volumes = _find_rar_part_volumes(str(temp_dir), base_name)
        
        assert len(volumes) == 1
    
    @pytest.mark.unit
    def test_detect_with_gap_in_parts(self, temp_dir):
        """
        Test detection stops at first gap in part numbers.
        """
        base_name = "archive"
        (temp_dir / f"{base_name}.part1.rar").write_bytes(b"p1")
        (temp_dir / f"{base_name}.part2.rar").write_bytes(b"p2")
        # Skip part3
        (temp_dir / f"{base_name}.part4.rar").write_bytes(b"p4")
        
        volumes = _find_rar_part_volumes(str(temp_dir), base_name)
        
        # Should stop at part2
        assert len(volumes) == 2


# =============================================================================
# Archive Volume Detection Tests
# =============================================================================


class TestDetectArchiveVolumes:
    """Test suite for _detect_archive_volumes() function."""
    
    @pytest.mark.unit
    def test_detect_7z_sequential_volumes(self, temp_dir):
        """
        Test detection of 7z multi-volume archives.
        
        Verifies detection of .7z.001, .7z.002 format.
        """
        base_name = "backup.7z"
        for i in range(1, 4):
            (temp_dir / f"{base_name}.{i:03d}").write_bytes(b"volume")
        
        first_volume = temp_dir / f"{base_name}.001"
        volumes = _detect_archive_volumes(first_volume)
        
        assert len(volumes) == 3
    
    @pytest.mark.unit
    def test_detect_rar_classic_volumes(self, temp_dir):
        """
        Test detection of RAR classic multi-volume archives.
        """
        (temp_dir / "archive.rar").write_bytes(b"header")
        (temp_dir / "archive.r00").write_bytes(b"v0")
        (temp_dir / "archive.r01").write_bytes(b"v1")
        
        first_volume = temp_dir / "archive.r00"
        volumes = _detect_archive_volumes(first_volume)
        
        # Should detect all RAR volumes
        assert len(volumes) >= 2
    
    @pytest.mark.unit
    def test_detect_rar_part_volumes(self, temp_dir):
        """
        Test detection of RAR part multi-volume archives.
        """
        (temp_dir / "data.part1.rar").write_bytes(b"p1")
        (temp_dir / "data.part2.rar").write_bytes(b"p2")
        
        first_volume = temp_dir / "data.part1.rar"
        volumes = _detect_archive_volumes(first_volume)
        
        assert len(volumes) == 2
    
    @pytest.mark.unit
    def test_single_archive_file(self, temp_dir):
        """
        Test detection with single (non-multi-volume) archive.
        
        Verifies that single files return only themselves.
        """
        archive = temp_dir / "single.7z"
        archive.write_bytes(b"archive data")
        
        volumes = _detect_archive_volumes(archive)
        
        # Should return only the input file
        assert len(volumes) == 1
        assert str(archive) in volumes
    
    @pytest.mark.unit
    def test_non_volume_file(self, temp_dir):
        """
        Test detection with regular file (not a volume).
        """
        regular_file = temp_dir / "document.txt"
        regular_file.write_text("not an archive")
        
        volumes = _detect_archive_volumes(regular_file)
        
        # Should return only the input file
        assert len(volumes) == 1
        assert str(regular_file) in volumes


# =============================================================================
# Path Deletion Tests
# =============================================================================


class TestDeletePath:
    """Test suite for delete_path() function."""
    
    @pytest.mark.unit
    def test_delete_single_file_with_trash(self, temp_dir):
        """
        Test deleting a single file using trash.
        
        Verifies send2trash integration.
        """
        test_file = temp_dir / "delete_me.txt"
        test_file.write_text("content")
        
        with patch("p7zip.filesystem_utils.send2trash") as mock_trash:
            delete_path(test_file, use_trash=True)
            
            # Should call send2trash
            mock_trash.assert_called_once()
    
    @pytest.mark.unit
    def test_delete_single_file_permanent(self, temp_dir):
        """
        Test permanently deleting a single file.
        
        Verifies os.remove is used for permanent deletion.
        """
        test_file = temp_dir / "delete_me.txt"
        test_file.write_text("content")
        
        delete_path(test_file, use_trash=False)
        
        # File should be deleted
        assert not test_file.exists()
    
    @pytest.mark.unit
    def test_delete_directory_with_trash(self, temp_dir):
        """
        Test deleting a directory using trash.
        """
        test_dir = temp_dir / "delete_dir"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("content")
        
        with patch("p7zip.filesystem_utils.send2trash") as mock_trash:
            delete_path(test_dir, use_trash=True)
            
            mock_trash.assert_called_once()
    
    @pytest.mark.unit
    def test_delete_directory_permanent(self, temp_dir):
        """
        Test permanently deleting a directory.
        """
        test_dir = temp_dir / "delete_dir"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("content")
        
        delete_path(test_dir, use_trash=False)
        
        # Directory should be deleted
        assert not test_dir.exists()
    
    @pytest.mark.unit
    def test_delete_nonexistent_path(self):
        """
        Test deleting a non-existent path.
        
        Verifies that FileNotFoundError is raised.
        """
        with pytest.raises(FileNotFoundError):
            delete_path("/nonexistent/path/to/file")
    
    @pytest.mark.unit
    def test_delete_multi_volume_archive(self, temp_dir):
        """
        Test deleting multi-volume archive deletes all volumes.
        
        Verifies that all volumes are removed together.
        """
        # Create multi-volume archive
        base = "archive.7z"
        volumes = []
        for i in range(1, 4):
            volume = temp_dir / f"{base}.{i:03d}"
            volume.write_bytes(b"volume")
            volumes.append(volume)
        
        # Delete first volume
        delete_path(volumes[0], use_trash=False)
        
        # All volumes should be deleted
        for volume in volumes:
            assert not volume.exists()
    
    @pytest.mark.unit
    def test_delete_rar_volumes(self, temp_dir):
        """
        Test deleting RAR multi-volume archive.
        """
        (temp_dir / "archive.rar").write_bytes(b"header")
        (temp_dir / "archive.r00").write_bytes(b"v0")
        (temp_dir / "archive.r01").write_bytes(b"v1")
        
        first_volume = temp_dir / "archive.r00"
        
        delete_path(first_volume, use_trash=False)
        
        # All RAR volumes should be deleted
        assert not (temp_dir / "archive.rar").exists()
        assert not (temp_dir / "archive.r00").exists()
        assert not (temp_dir / "archive.r01").exists()
    
    @pytest.mark.unit
    def test_delete_with_string_path(self, temp_dir):
        """
        Test deleting with string path instead of Path object.
        
        Verifies PathLike support.
        """
        test_file = temp_dir / "file.txt"
        test_file.write_text("content")
        
        # Pass as string
        delete_path(str(test_file), use_trash=False)
        
        assert not test_file.exists()


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================


class TestFilesystemUtilsEdgeCases:
    """Test edge cases and error handling for filesystem utilities."""
    
    @pytest.mark.unit
    def test_detect_volumes_with_similar_names(self, temp_dir):
        """
        Test volume detection doesn't confuse similar filenames.
        
        Verifies precise matching of volume patterns.
        """
        # Create files with similar names
        (temp_dir / "archive.7z").write_bytes(b"single")
        (temp_dir / "archive.7z.001").write_bytes(b"v1")
        (temp_dir / "archive.7z.002").write_bytes(b"v2")
        (temp_dir / "archive2.7z.001").write_bytes(b"other")
        
        volumes = _detect_archive_volumes(temp_dir / "archive.7z.001")
        
        # Should only detect archive.7z.00X volumes
        assert str(temp_dir / "archive.7z.001") in volumes
        assert str(temp_dir / "archive.7z.002") in volumes
        assert str(temp_dir / "archive2.7z.001") not in volumes
    
    @pytest.mark.unit
    def test_delete_path_with_permission_error(self, temp_dir):
        """
        Test deletion handles permission errors gracefully.
        
        Note: Actual permission testing depends on OS and privileges.
        """
        test_file = temp_dir / "readonly.txt"
        test_file.write_text("content")
        test_file.chmod(0o444)  # Read-only
        
        # Attempt to delete (may succeed depending on OS)
        try:
            delete_path(test_file, use_trash=False)
        except PermissionError:
            # Expected on some systems
            pass
        finally:
            # Cleanup
            if test_file.exists():
                test_file.chmod(0o644)
                test_file.unlink()
    
    @pytest.mark.unit
    def test_volume_detection_performance(self, temp_dir):
        """
        Test volume detection performance with many files.
        
        Verifies efficient detection even with many files in directory.
        """
        # Create many non-volume files
        for i in range(100):
            (temp_dir / f"file{i}.txt").write_text("data")
        
        # Create volume sequence
        for i in range(1, 11):
            (temp_dir / f"archive.7z.{i:03d}").write_bytes(b"volume")
        
        first_volume = temp_dir / "archive.7z.001"
        
        # Should efficiently find volumes despite many files
        volumes = _detect_archive_volumes(first_volume)
        
        assert len(volumes) == 10