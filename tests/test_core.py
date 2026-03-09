""" """

import pytest

from p7zip.core import SevenZipArchive, DeleteMode


class TestFileListRetrieval:
    @pytest.mark.integration
    def test_file_list_retrieval(
        self,
        configure_binary_once,
        archive_path,
        sample_files,
        completion_callback
    ):
        """
        Test retrieving the list of files from a 7z archive.

        Verifies that the files added to the archive can be correctly listed.
        7z must be properly configured before running this test.
        """
        with SevenZipArchive(archive_path, "w") as arch:
            arch.compress(sample_files)

        with SevenZipArchive(archive_path, "r", completion_callback=completion_callback) as arch:
            file_list = arch.list_contents()

        expected_files = [f.name for f in sample_files]

        assert set(file_list) == set(expected_files)
        
    def test_invalid_mode(self, archive_path):
        with SevenZipArchive(archive_path, "w") as arch:
            with pytest.raises(RuntimeError, match="Archive not opened in read mode"):
                arch.list_contents()

    def test_invalid_archive(self):
        with SevenZipArchive("invalid.7z", "r") as arch:
            with pytest.raises(FileNotFoundError):
                arch.list_contents()
        
class TestIntegrity:
    @pytest.mark.integration
    def test_integrity(
        self,
        configure_binary_once,
        archive_path,
        sample_files,
        temp_dir,
        completion_callback,
    ):
        with SevenZipArchive(archive_path, "w") as arch:
            arch.compress(sample_files)
            
        with SevenZipArchive(archive_path, "r", completion_callback=completion_callback) as arch:
            arch.test_integrity()
            
        assert "successfully" in completion_callback.call_args[0][1].lower()
        
    def test_invalid_mode(self, archive_path):
        with SevenZipArchive(archive_path, "w") as arch:
            with pytest.raises(RuntimeError, match="Archive not opened in read mode"):
                arch.test_integrity()

    def test_invalid_archive(self):
        with SevenZipArchive("invalid.7z", "r") as arch:
            with pytest.raises(FileNotFoundError):
                arch.test_integrity()

class TestCompressionAndExtraction:
    @pytest.mark.integration
    def test_simple_compression_and_extraction(
        self, configure_binary_once, archive_path, sample_files, temp_dir
    ):
        """
        Test compressing files into a 7z archive and extracting them back.

        Verifies that files can be compressed and then extracted correctly.
        7z must be properly configured before running this test.
        """
        with SevenZipArchive(archive_path, "w") as arch:
            arch.compress(sample_files)

        with SevenZipArchive(archive_path, "r") as arch:
            arch.extract(temp_dir)

        for original_file in sample_files:
            extracted_file = temp_dir / original_file.name
            assert extracted_file.exists()
            assert extracted_file.read_bytes() == original_file.read_bytes()

    @pytest.mark.integration
    def test_advance_compression_and_extraction(
        self,
        configure_binary_once,
        archive_path,
        sample_files,
        temp_dir,
        progress_callback,
        completion_callback,
    ):
        """
        Test advanced compression with encryption, patterns, and callbacks.
        """
        with SevenZipArchive(
            archive_path, "w", progress_callback=progress_callback, completion_callback=completion_callback
        ) as arch:
            arch.set_password("1234")
            arch.set_working_directory(temp_dir)
            arch.compress(
                sample_files,
                include_patterns=["*.txt"],
                format="7z",
                compression_method="deflate",
                encrypt_headers=True,
                delete_after_compression=DeleteMode.PERMANENT,
            )

        # Verify compress callback was called
        assert completion_callback.called, "Completion callback was not called"
        completion_callback.reset_mock()

        with SevenZipArchive(
            archive_path, "r", completion_callback=completion_callback
        ) as arch:
            arch.set_password("1234")
            arch.set_working_directory(temp_dir)
            arch.extract(
                include_patterns=["*.txt"],
                exclude_patterns=["*.bin"],
                delete_after_extraction=DeleteMode.PERMANENT,
            )

        # Verify extract callback was called
        assert completion_callback.called, "Completion callback was not called"
        assert "successfully" in completion_callback.call_args[0][1].lower()

        for original_file in [sample_files[0], sample_files[3]]:
            extracted_file = temp_dir / original_file.name
            assert extracted_file.exists()


class TestCompressInvalidParams:
    @pytest.mark.parametrize("volume_size", ["invalid_size", "20n", "20"])
    def test_invalid_volume_size(self, archive_path, volume_size):
        """
        Test that an error is raised when an invalid volume size is specified.

        Verifies that the SevenZipArchive raises a ValueError for invalid volume sizes.
        7z must be properly configured before running this test.
        """
        with SevenZipArchive(archive_path, "w") as arch:
            with pytest.raises(ValueError, match="Invalid volume size"):
                arch.compress([], volume_size=volume_size)

    @pytest.mark.parametrize("compression_level", [-1, 10])
    def test_invalid_compression_level(self, archive_path, compression_level):
        """
        Test that an error is raised when an invalid compression level is specified.

        Verifies that the SevenZipArchive raises a ValueError for invalid compression levels.
        7z must be properly configured before running this test.
        """
        with SevenZipArchive(archive_path, "w") as arch:
            with pytest.raises(ValueError, match="Invalid compression level"):
                arch.compress([], compression_level=compression_level)

    def test_invalid_mode(self, archive_path):
        with SevenZipArchive(archive_path, "r") as arch:
            with pytest.raises(RuntimeError, match="Archive not opened in write mode"):
                arch.compress([])


class TestExtractInvalidParams:
    def test_invalid_mode(self, archive_path):
        with SevenZipArchive(archive_path, "w") as arch:
            with pytest.raises(RuntimeError, match="Archive not opened in read mode"):
                arch.extract()

    def test_invalid_archive(self):
        with SevenZipArchive("invalid.7z", "r") as arch:
            with pytest.raises(FileNotFoundError):
                arch.extract()
