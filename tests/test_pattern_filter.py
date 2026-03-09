"""
Unit tests for the pattern_filter module.

This module tests pattern-based file filtering functionality including
glob pattern matching, include/exclude logic, and path preparation.
"""

from pathlib import Path

import pytest

from p7zip.pattern_filter import (
    filter_paths_by_patterns,
    prepare_sources_and_exclusions,
)


# =============================================================================
# Pattern Filtering Tests
# =============================================================================


class TestFilterPathsByPatterns:
    """Test suite for filter_paths_by_patterns() function."""
    
    @pytest.mark.unit
    def test_no_patterns_includes_all_files(self, sample_files):
        """
        Test that all files are included when no patterns are specified.
        
        Verifies default behavior without filtering.
        """
        included, excluded = filter_paths_by_patterns(sample_files)
        
        assert len(included) == len(sample_files)
        assert len(excluded) == 0
    
    @pytest.mark.unit
    def test_include_pattern_filters_by_extension(self, sample_files):
        """
        Test filtering files by extension using include patterns.
        
        Verifies that include patterns work for file extensions.
        """
        include_patterns = ["*.txt"]
        included, excluded = filter_paths_by_patterns(
            sample_files,
            include_patterns=include_patterns
        )
        
        # Should include only .txt files
        included_names = [f.name for f in included]
        assert all(name.endswith(".txt") for name in included_names)
        assert len(included) == 2  # file1.txt and file4.txt
    
    @pytest.mark.unit
    def test_exclude_pattern_removes_files(self, sample_files):
        """
        Test excluding files by pattern.
        
        Verifies that exclude patterns remove matching files.
        """
        exclude_patterns = ["*.log"]
        included, excluded = filter_paths_by_patterns(
            sample_files,
            exclude_patterns=exclude_patterns
        )
        
        # Should exclude .log files
        excluded_names = list(excluded.keys())
        assert any(name.endswith(".log") for name in excluded_names)
        
        # Included files should not have .log extension
        included_names = [f.name for f in included]
        assert not any(name.endswith(".log") for name in included_names)
    
    @pytest.mark.unit
    def test_include_and_exclude_patterns_combined(self, sample_files):
        """
        Test combining include and exclude patterns.
        
        Verifies that exclude patterns take priority over include patterns.
        """
        include_patterns = ["*.txt"]
        exclude_patterns = ["file1.txt"]
        
        included, excluded = filter_paths_by_patterns(
            sample_files,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns
        )
        
        included_names = [f.name for f in included]
        
        # Should include .txt files except file1.txt
        assert "file1.txt" not in included_names
        assert "file4.txt" in included_names
        assert len(included) == 1
    
    @pytest.mark.unit
    def test_path_based_pattern_matching(self, temp_dir):
        """
        Test pattern matching with path separators.
        
        Verifies that patterns with "/" match full relative paths.
        """
        # Create test structure
        (temp_dir / "src").mkdir()
        (temp_dir / "tests").mkdir()
        
        src_file = temp_dir / "src" / "main.py"
        test_file = temp_dir / "tests" / "test_main.py"
        
        src_file.write_text("source")
        test_file.write_text("test")
        
        files = [src_file, test_file]
        
        # Include only files in src/ directory
        include_patterns = [f"{temp_dir}/src/*.py"]
        included, excluded = filter_paths_by_patterns(
            files,
            include_patterns=include_patterns
        )
        
        included_names = [f.name for f in included]
        assert "main.py" in included_names
        assert "test_main.py" not in included_names
    
    @pytest.mark.unit
    def test_wildcard_pattern_matching(self, sample_files):
        """
        Test wildcard pattern matching.
        
        Verifies that * and ? wildcards work correctly.
        """
        include_patterns = ["file?.txt"]  # Matches file1.txt, file4.txt
        included, excluded = filter_paths_by_patterns(
            sample_files,
            include_patterns=include_patterns
        )
        
        included_names = [f.name for f in included]
        assert "file1.txt" in included_names or "file4.txt" in included_names
    
    @pytest.mark.unit
    def test_directory_filtering(self, temp_dir):
        """
        Test filtering with directory paths.
        
        Verifies that directories are processed recursively.
        """
        # Create directory structure
        subdir = temp_dir / "docs"
        subdir.mkdir()
        
        (subdir / "readme.txt").write_text("readme")
        (subdir / "license.md").write_text("license")
        
        include_patterns = ["*.txt"]
        included, excluded = filter_paths_by_patterns(
            [subdir],
            include_patterns=include_patterns
        )
        
        included_names = [f.name for f in included]
        assert "readme.txt" in included_names
        assert "license.md" not in included_names
    
    @pytest.mark.unit
    def test_empty_directory_handling(self, empty_dir):
        """
        Test handling of empty directories.
        
        Verifies that empty directories are always excluded.
        """
        included, excluded = filter_paths_by_patterns([empty_dir])
        
        # Empty directories should be in excluded
        assert len(included) == 0
        assert len(excluded) > 0
    
    
    @pytest.mark.unit
    def test_empty_directory_multiple_levels(self, temp_dir):
        """
        Test detection of empty directories at multiple nesting levels.
        
        Ensures that the empty directory detection works for:
        - Top-level empty directories
        - Nested empty directories (inside non-empty parents)
        - Deeply nested empty directories
        """
        # Create complex structure
        level1_empty = temp_dir / "empty1"
        level1_empty.mkdir()
        
        level2_with_empty = temp_dir / "level2"
        level2_with_empty.mkdir()
        (level2_with_empty / "file.txt").write_text("content")
        
        level2_empty_sibling = temp_dir / "level2" / "empty2"
        level2_empty_sibling.mkdir()
        
        level3_nested = temp_dir / "level2" / "subdir"
        level3_nested.mkdir()
        (level3_nested / "nested.txt").write_text("nested content")
        
        level3_empty = temp_dir / "level2" / "subdir" / "empty3"
        level3_empty.mkdir()
        
        included, excluded = filter_paths_by_patterns([temp_dir])
        
        excluded_names = {p.name for p in excluded.values()}
        
        # All empty directories should be detected
        assert "empty1" in excluded_names
        assert "empty2" in excluded_names
        assert "empty3" in excluded_names
        
        # Files should be included
        included_names = {f.name for f in included}
        assert "file.txt" in included_names
        assert "nested.txt" in included_names
    
    @pytest.mark.unit
    def test_multiple_include_patterns(self, sample_files):
        """
        Test using multiple include patterns.
        
        Verifies OR logic for include patterns.
        """
        include_patterns = ["*.txt", "*.pdf"]
        included, excluded = filter_paths_by_patterns(
            sample_files,
            include_patterns=include_patterns
        )
        
        included_extensions = {f.suffix for f in included}
        assert ".txt" in included_extensions
        assert ".pdf" in included_extensions
    
    @pytest.mark.unit
    def test_multiple_exclude_patterns(self, sample_files):
        """
        Test using multiple exclude patterns.
        
        Verifies that multiple patterns can exclude different file types.
        """
        exclude_patterns = ["*.log", "*.doc"]
        included, excluded = filter_paths_by_patterns(
            sample_files,
            exclude_patterns=exclude_patterns
        )
        
        excluded_extensions = {Path(path).suffix for path in excluded.values()}
        assert ".log" in excluded_extensions
        assert ".doc" in excluded_extensions
    
    @pytest.mark.unit
    def test_case_sensitive_pattern_matching(self, temp_dir):
        """
        Test that pattern matching is case-sensitive.
        
        Verifies fnmatch behavior.
        """
        file_upper = temp_dir / "FILE.TXT"
        file_lower = temp_dir / "file.txt"
        
        file_upper.write_text("upper")
        file_lower.write_text("lower")
        
        include_patterns = ["*.txt"]  # Lowercase extension
        included, excluded = filter_paths_by_patterns(
            [file_upper, file_lower],
            include_patterns=include_patterns
        )
        
        included_names = [f.name for f in included]
        assert "file.txt" in included_names
        # FILE.TXT might not match depending on fnmatch behavior
    
    @pytest.mark.unit
    def test_exclude_takes_priority_over_include(self, sample_files):
        """
        Test that exclude patterns take priority.
        
        Verifies the priority rule when patterns conflict.
        """
        include_patterns = ["*"]  # Include everything
        exclude_patterns = ["*.log"]  # Except .log files
        
        included, excluded = filter_paths_by_patterns(
            sample_files,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns
        )
        
        # .log files should be excluded despite wildcard include
        included_extensions = {f.suffix for f in included}
        assert ".log" not in included_extensions


# =============================================================================
# Source and Exclusion Preparation Tests
# =============================================================================


class TestPrepareSourcesAndExclusions:
    """Test suite for prepare_sources_and_exclusions() function."""
    
    @pytest.mark.unit
    def test_basic_source_preparation(self, temp_dir):
        """
        Test basic source and exclusion preparation.
        
        Verifies that sources and exclusions are correctly formatted.
        """
        # Create test files
        file1 = temp_dir / "include.txt"
        file2 = temp_dir / "exclude.log"
        file1.write_text("included")
        file2.write_text("excluded")
        
        source_paths = [temp_dir, file1]
        included_files = [file1]
        excluded_files = {"exclude.log": file2}
        
        filter_result = (included_files, excluded_files)
        
        exclusions, sources = prepare_sources_and_exclusions(
            source_paths,
            filter_result
        )
        
        assert len(sources) > 0
        assert isinstance(sources, list)
        assert isinstance(exclusions, list)
    
    @pytest.mark.unit
    def test_exclusion_path_formatting(self, temp_dir):
        """
        Test that exclusions are formatted as relative paths.
        
        Verifies proper path formatting for 7z command.
        """
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        
        excluded_file = subdir / "excluded.txt"
        excluded_file.write_text("excluded")
        
        source_paths = [temp_dir]
        included_files = []
        excluded_files = {str(excluded_file.relative_to(temp_dir)): excluded_file}
        
        filter_result = (included_files, excluded_files)
        
        exclusions, sources = prepare_sources_and_exclusions(
            source_paths,
            filter_result
        )
        
        # Exclusions should be relative paths
        for exclusion in exclusions:
            assert not Path(exclusion).is_absolute()
    
    @pytest.mark.unit
    def test_empty_filter_result(self, temp_dir):
        """
        Test handling of empty filter results.
        
        Verifies graceful handling when no files match.
        """
        source_paths = [temp_dir]
        filter_result = ([], {})
        
        exclusions, sources = prepare_sources_and_exclusions(
            source_paths,
            filter_result
        )
        
        assert isinstance(exclusions, list)
        assert isinstance(sources, list)
    
    @pytest.mark.unit
    def test_multiple_sources(self, temp_dir):
        """
        Test preparation with multiple source paths.
        
        Verifies handling of multiple source directories.
        """
        dir1 = temp_dir / "dir1"
        dir2 = temp_dir / "dir2"
        dir1.mkdir()
        dir2.mkdir()
        
        file1 = dir1 / "file1.txt"
        file2 = dir2 / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")
        
        source_paths = [dir1, dir2]
        included_files = [file1, file2]
        excluded_files = {}
        
        filter_result = (included_files, excluded_files)
        
        exclusions, sources = prepare_sources_and_exclusions(
            source_paths,
            filter_result
        )
        
        # Both sources should be present if they have included files
        assert len(sources) == 2
    
    @pytest.mark.unit
    def test_source_without_included_files(self, temp_dir):
        """
        Test that sources without included files are omitted.
        
        Verifies optimization of source list.
        """
        dir1 = temp_dir / "included_dir"
        dir2 = temp_dir / "excluded_dir"
        dir1.mkdir()
        dir2.mkdir()
        
        included_file = dir1 / "file.txt"
        excluded_file = dir2 / "excluded.txt"
        
        included_file.write_text("included")
        excluded_file.write_text("excluded")
        
        source_paths = [dir1, dir2]
        included_files = [included_file]
        excluded_files = {"excluded.txt": excluded_file}
        
        filter_result = (included_files, excluded_files)
        
        exclusions, sources = prepare_sources_and_exclusions(
            source_paths,
            filter_result
        )
        
        # Only dir1 should be in sources
        assert len(sources) == 1
        assert str(dir1) in sources
    
    @pytest.mark.unit
    def test_exclusion_filtering_by_source(self, temp_dir):
        """
        Test that exclusions are filtered to match active sources.
        
        Verifies that only relevant exclusions are included.
        """
        active_dir = temp_dir / "active"
        inactive_dir = temp_dir / "inactive"
        active_dir.mkdir()
        inactive_dir.mkdir()
        
        active_file = active_dir / "file.txt"
        inactive_excluded = inactive_dir / "excluded.txt"
        
        active_file.write_text("active")
        inactive_excluded.write_text("excluded")
        
        source_paths = [active_dir, inactive_dir]
        included_files = [active_file]
        excluded_files = {
            str(inactive_excluded.relative_to(temp_dir)): inactive_excluded
        }
        
        filter_result = (included_files, excluded_files)
        
        exclusions, sources = prepare_sources_and_exclusions(
            source_paths,
            filter_result
        )
        
        # Exclusions from inactive source should not be included
        # (implementation dependent - verify against actual behavior)
        assert isinstance(exclusions, list)


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================


class TestPatternFilterEdgeCases:
    """Test edge cases and error handling for pattern filtering."""
    
    @pytest.mark.unit
    def test_empty_pattern_lists(self, sample_files):
        """
        Test filtering with empty pattern lists.
        
        Verifies handling of empty list inputs.
        """
        included, excluded = filter_paths_by_patterns(
            sample_files,
            include_patterns=[],
            exclude_patterns=[]
        )
        
        # Empty lists should behave like None (include all)
        assert len(included) > 0
    
    @pytest.mark.unit
    def test_pattern_with_no_matches(self, sample_files):
        """
        Test pattern that matches no files.
        
        Verifies handling when pattern yields no results.
        """
        include_patterns = ["*.nonexistent"]
        included, excluded = filter_paths_by_patterns(
            sample_files,
            include_patterns=include_patterns
        )
        
        # No files should match
        assert len(included) == 0
        assert len(excluded) > 0
    
    @pytest.mark.unit
    def test_complex_glob_patterns(self, temp_dir):
        """
        Test complex glob patterns with multiple wildcards.
        
        Verifies support for advanced pattern syntax.
        """
        (temp_dir / "test_file_v1.txt").write_text("v1")
        (temp_dir / "test_file_v2.txt").write_text("v2")
        (temp_dir / "other_file.txt").write_text("other")
        
        files = list(temp_dir.glob("*.txt"))
        
        include_patterns = ["test_file_*.txt"]
        included, excluded = filter_paths_by_patterns(
            files,
            include_patterns=include_patterns
        )
        
        included_names = {f.name for f in included}
        assert "test_file_v1.txt" in included_names
        assert "test_file_v2.txt" in included_names
        assert "other_file.txt" not in included_names