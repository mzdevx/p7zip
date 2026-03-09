"""
Filesystem utilities for archive operations.

This module provides filesystem-related utilities including multi-volume
archive deletion and path manipulation helpers.
"""

import os
import re
import shutil

from send2trash import send2trash

from .types import PathLike


def delete_path(path: PathLike, use_trash: bool = True) -> None:
    """
    Delete a file or directory, with support for multi-volume archives.

    This function intelligently handles deletion of:
    - Single files
    - Directories (recursively)
    - Multi-volume archives (all volumes are detected and deleted together)

    Args:
        path: Path to the file or directory to delete
        use_trash: If True, move to system trash/recycle bin (recoverable).
                  If False, permanently delete (not recoverable).

    Raises:
        FileNotFoundError: If the specified path does not exist

    Multi-Volume Archive Support:
        Automatically detects and deletes all volumes for:
        - Sequential numeric extensions (.001, .002, .003, ...)
        - RAR classic format (.rar, .r00, .r01, ...)
        - RAR part naming (.part1.rar, .part2.rar, ...)

    Example:
        >>> delete_path("backup.7z.001")  # Deletes .001, .002, .003, etc.
        >>> delete_path("archive.rar")    # Deletes .rar, .r00, .r01, etc.
        >>> delete_path("data/", use_trash=False)  # Permanently deletes directory
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Path does not exist: {path}")

    # Handle directory deletion
    if os.path.isdir(path):
        if use_trash:
            send2trash(str(path))
        else:
            shutil.rmtree(path)
        return

    # Handle file deletion (with multi-volume detection)
    files_to_delete = _detect_archive_volumes(path)

    # Delete all detected files in sorted order
    for file_path in sorted(files_to_delete):
        if use_trash:
            send2trash(file_path)
        else:
            os.remove(file_path)


def _detect_archive_volumes(file_path: PathLike) -> set:
    """
    Detect all volumes belonging to a multi-volume archive.

    This function analyzes the filename to determine if it's part of a
    multi-volume archive and finds all related volume files.

    Args:
        file_path: Path to a file that may be part of a multi-volume archive

    Returns:
        Set of file paths for all detected volumes (includes the input file)

    Supported Formats:
        - Sequential numeric: file.7z.001, file.7z.002, ...
        - RAR classic: file.rar, file.r00, file.r01, ...
        - RAR parts: file.part1.rar, file.part2.rar, ...
    """
    file_path_str = str(file_path)
    files_to_delete: set = {file_path_str}

    directory = os.path.dirname(file_path_str)
    filename = os.path.basename(file_path_str)
    base_name, extension = os.path.splitext(filename)

    # Pattern 1: Sequential numeric extensions (.001, .002, .003, ...)
    if extension[1:].isdigit() and len(extension) == 4:
        volumes = _find_sequential_volumes(directory, base_name, extension)
        files_to_delete.update(volumes)

    # Pattern 2: RAR classic extensions (.r00, .r01, .r02, ...)
    elif (
        extension.lower().startswith(".r")
        and len(extension) == 4
        and extension[2:].isdigit()
    ):
        volumes = _find_rar_classic_volumes(directory, base_name, extension)
        files_to_delete.update(volumes)

    # Pattern 3: RAR part naming (.part1.rar, .part2.rar, ...)
    else:
        rar_part_match = re.match(r"(.+)\.part(\d+)\.rar$", filename, re.IGNORECASE)
        if rar_part_match:
            volumes = _find_rar_part_volumes(directory, rar_part_match.group(1))
            files_to_delete.update(volumes)

    return files_to_delete


def _find_sequential_volumes(
    directory: str, base_name: str, first_extension: str
) -> set:
    """
    Find all volumes in sequential numeric format (.001, .002, ...).

    Args:
        directory: Directory containing the archive
        base_name: Base name of the archive (without extension)
        first_extension: First extension encountered (e.g., ".001")

    Returns:
        Set of paths to all sequential volumes found
    """
    volumes = set()
    base_path = os.path.join(directory, base_name)
    volume_index = int(first_extension[1:])

    # Search for consecutive volumes
    while True:
        volume_path = f"{base_path}.{volume_index:03d}"
        if os.path.exists(volume_path):
            volumes.add(volume_path)
            volume_index += 1
        else:
            break

    return volumes


def _find_rar_classic_volumes(
    directory: str, base_name: str, first_extension: str
) -> set:
    """
    Find all volumes in RAR classic format (.rar, .r00, .r01, ...).

    Args:
        directory: Directory containing the archive
        base_name: Base name of the archive (without extension)
        first_extension: First extension encountered (e.g., ".r00")

    Returns:
        Set of paths to all RAR classic volumes found
    """
    volumes = set()
    base_path = os.path.join(directory, base_name)
    volume_index = int(first_extension[2:])

    # Search for consecutive .rNN volumes
    while True:
        volume_path = f"{base_path}.r{volume_index:02d}"
        if os.path.exists(volume_path):
            volumes.add(volume_path)
            volume_index += 1
        else:
            break

    # Also include the main .rar header file if present
    rar_header_path = f"{base_path}.rar"
    if os.path.exists(rar_header_path):
        volumes.add(rar_header_path)

    return volumes


def _find_rar_part_volumes(directory: str, base_name: str) -> set:
    """
    Find all volumes in RAR part format (.part1.rar, .part2.rar, ...).

    Args:
        directory: Directory containing the archive
        base_name: Base name of the archive (without .partN.rar suffix)

    Returns:
        Set of paths to all RAR part volumes found
    """
    volumes = set()
    volume_index = 1

    # Search for consecutive .partN.rar volumes
    while True:
        volume_path = os.path.join(directory, f"{base_name}.part{volume_index}.rar")
        if os.path.exists(volume_path):
            volumes.add(volume_path)
            volume_index += 1
        else:
            break

    return volumes
