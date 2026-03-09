"""
Pattern-based file filtering utilities for archive operations.

This module provides functionality for filtering files based on include and
exclude patterns, supporting both simple glob patterns and path-based patterns.
"""

import fnmatch
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def filter_paths_by_patterns(
    staged_paths: List[Path],
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
) -> Tuple[List[Path], Dict[str, Path]]:
    """
    Filter files based on include and exclude glob patterns.

    Separates a list of paths into included and excluded groups based on
    pattern matching. Exclude patterns take priority over include patterns
    when both are specified.

    Args:
        staged_paths: List of file or directory paths to process
        include_patterns: Optional list of glob patterns for files to include.
                         Patterns containing "/" match against full relative paths,
                         others match filenames only. If None, all files are
                         considered for inclusion (subject to exclude patterns)
        exclude_patterns: Optional list of glob patterns for files to exclude.
                         These take priority over include patterns. If None,
                         no exclusion filtering is applied

    Returns:
        A tuple containing:
        - included_files: List of Path objects that should be included
        - excluded_files: Dict mapping relative path strings to Path objects
                         that should be excluded (includes empty directories)

    Pattern Matching Rules:
        - If only exclude_patterns: match → exclude, no match → include
        - If only include_patterns: match → include, no match → exclude
        - If both patterns: (include match AND NOT exclude match) → include
        - Empty directories are always excluded
        - Patterns with "/" match full relative paths
        - Patterns without "/" match only filenames

    Example:
        >>> paths = [Path("src/main.py"), Path("test.txt"), Path("build/")]
        >>> included, excluded = filter_paths_by_patterns(
        ...     paths,
        ...     include_patterns=["*.py"],
        ...     exclude_patterns=["test*"]
        ... )
        >>> # included: [Path("src/main.py")]
        >>> # excluded: {"test.txt": Path("test.txt"), "build": Path("build")}
    """

    def _matches_any_pattern(file_path: Path, patterns: List[str]) -> bool:
        """
        Check if a file path matches at least one glob pattern.

        Args:
            file_path: The file path to check against patterns
            patterns: List of glob patterns to match against

        Returns:
            True if the path matches at least one pattern, False otherwise
        """
        filename = file_path.name

        for pattern in patterns:
            if "/" in pattern:
                # Pattern contains path separator → match against full relative path
                if fnmatch.fnmatch(file_path.as_posix(), pattern):
                    return True
            else:
                # Simple glob pattern → match against filename only
                if fnmatch.fnmatch(filename, pattern):
                    return True

        return False

    def _should_include_file(file_path: Path) -> bool:
        """
        Determine if a file should be included based on pattern rules.

        Applies the pattern priority logic to decide if a file should be
        included or excluded from the operation.

        Args:
            file_path: The file path to evaluate

        Returns:
            True if the file should be included, False if excluded
        """
        # Case 1: Only exclude_patterns provided
        if (include_patterns is None or len(include_patterns) == 0) and (exclude_patterns is not None and len(exclude_patterns) > 0):
            # Exclude if matches exclude pattern, otherwise include
            return not _matches_any_pattern(file_path, exclude_patterns)

        # Case 2: Only include_patterns provided (or both are None)
        if (include_patterns is not None and len(include_patterns) > 0) and (exclude_patterns is None or len(exclude_patterns) == 0):
            # Include if matches include pattern, otherwise exclude
            return _matches_any_pattern(file_path, include_patterns)

        # Case 3: Both patterns provided
        if (include_patterns is not None and len(include_patterns) > 0) and (exclude_patterns is not None and len(exclude_patterns) > 0):
            # First check if it matches include patterns
            matches_include = _matches_any_pattern(file_path, include_patterns)

            if matches_include:
                # If matches include, check exclude (exclude has priority)
                matches_exclude = _matches_any_pattern(file_path, exclude_patterns)
                return not matches_exclude
            else:
                # Doesn't match include patterns → exclude
                return False

        # Case 4: Both are None → include everything
        return True

    # Files to include in the operation
    included_files: List[Path] = []

    # Files to exclude from the operation (including empty directories)
    excluded_files: Dict[str, Path] = {}
    
    for path in staged_paths:
        if path.is_file():
            # Process individual files
            if _should_include_file(path):
                included_files.append(path)
            else:
                excluded_files[path.name] = path

        elif path.is_dir():
            # Process directory contents recursively
            file_iterator = path.rglob("*")
            item_counter = 0
            
            for item in file_iterator:
                item_counter += 1
                
                if item.is_file():
                    # Check file against patterns
                    if _should_include_file(item):
                        included_files.append(item)
                    else:
                        relative_path_str = str(item.relative_to(path.parent))
                        excluded_files[relative_path_str] = item

                elif item.is_dir() and not any(item.iterdir()):
                    # Always add empty directories to excluded files
                    relative_path_str = str(item.relative_to(path.parent))
                    excluded_files[relative_path_str] = item
            
            if item_counter == 0:
                # Directory is empty, add to excluded files
                relative_path_str = str(path.relative_to(path.parent))
                excluded_files[relative_path_str] = path

    return included_files, excluded_files


def prepare_sources_and_exclusions(
    source_paths: List[Path],
    filter_result: Tuple[List[Path], Dict[str, Path]],
) -> Tuple[List[str], List[str]]:
    """
    Prepare source paths and exclusion patterns for 7z command execution.

    Takes the original source paths and filter results, then produces clean
    lists of sources and exclusions that are relevant to the actual files
    being compressed. This removes unnecessary exclusions and filters out
    sources that have no matching files.

    Args:
        source_paths: Original list of source paths provided by user
        filter_result: Tuple of (included_files, excluded_files_dict) from
                      filter_paths_by_patterns()

    Returns:
        A tuple containing:
        - clean_exclusions: List of relative path strings to exclude
        - clean_sources: List of source path strings that contain included files

    Example:
        >>> sources = [Path("src/"), Path("data/")]
        >>> filter_result = filter_paths_by_patterns(sources, exclude_patterns=["*.log"])
        >>> exclusions, sources = prepare_sources_and_exclusions(sources, filter_result)
    """
    included_files, excluded_files_dict = filter_result

    # Build mapping from absolute paths to relative exclusion paths
    abs_to_rel_exclusions = {
        Path(abs_path): rel_path for rel_path, abs_path in excluded_files_dict.items()
    }

    clean_sources: List[str] = []
    active_source_roots: set = set()

    # Step 1: Determine which sources contain files to include
    for source_path in source_paths:
        if source_path.is_file():
            # Single file source
            if source_path in included_files:
                clean_sources.append(str(source_path))
                active_source_roots.add(source_path)

        elif source_path.is_dir():
            # Directory source - check if it contains any included files
            has_included_files = any(
                file_path.is_relative_to(source_path) for file_path in included_files
            )
            if has_included_files:
                clean_sources.append(str(source_path))
                active_source_roots.add(source_path)

    # Step 2: Filter exclusions to only those within active sources
    clean_exclusions: List[str] = []
    for abs_path, rel_path in abs_to_rel_exclusions.items():
        # Only include exclusions that belong to an active source root
        if any(abs_path.is_relative_to(root) for root in active_source_roots):
            clean_exclusions.append(rel_path)

    return clean_exclusions, clean_sources
