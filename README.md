<div align="center">

# 🗜️ p7zip

### Python wrapper for 7-Zip

[![Tests](https://github.com/mzdevx/p7zip/actions/workflows/test.yml/badge.svg)](https://github.com/mzdevx/p7zip/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/mzdevx/p7zip/branch/main/graph/badge.svg)](https://codecov.io/gh/mzdevx/p7zip)
[![PyPI version](https://img.shields.io/pypi/v/p7zip.svg)](https://pypi.org/project/p7zip/)
[![Python](https://img.shields.io/pypi/pyversions/p7zip.svg)](https://pypi.org/project/p7zip/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Python interface for 7-Zip archive operations**  
With real-time progress tracking, encryption support, and pattern-based filtering

[Installation](#-installation) • [Quick Start](#-quick-start) • [Features](#-features) • [Examples](#-examples)

</div>

---

## ✨ Features

- 🎯 **Simple API** - Simple functions for archive operations
- 📊 **Real-time Progress** - Track compression/extraction with callbacks
- 🔐 **Encryption** - Encryption with header protection
- 🎯 **Smart Filtering** - Include/exclude files with glob patterns
- 💻 **Cross-Platform** - Works on Windows, macOS, and Linux
- 🔧 **Advanced Control** - Custom compression levels and methods

---

## 📦 Installation

### 1. Install p7zip package

```bash
pip install p7zip
```

### 2. Install 7-Zip binary

**p7zip requires the 7-Zip command-line tool:**

<details>
<summary><b>🪟 Windows Installation</b></summary>

**Option 1: 7-Zip installer for Windows and Automatic Detection (Recommended)**
1. Download and install **7-Zip installer for Windows** from [7-zip.org/download.html](https://www.7-zip.org/download.html)
2. Use auto-detection in your code:
    ```python
    from p7zip.binary import auto_detect_binary
    auto_detect_binary()  # Automatically finds 7z in PATH or Program Files
    ```
3. In the case that auto-detection fails, you can manually set the path:
    ```python
    from p7zip.binary import set_binary_path
    set_binary_path(r"C:\Program Files\7-Zip\7z.exe")
    ``` 

**Option 2: 7-Zip Extra and Manual Configuration**
1. Download **7-Zip Extra** from [7-zip.org/download.html](https://www.7-zip.org/download.html)
2. Extract to a location (e.g., `C:\Tools\`)
3. Register in your code:
   ```python
   from p7zip.binary import set_binary_path
   set_binary_path(r"C:\Tools\7za.exe")
   ```

</details>

<details>
<summary><b>🍎 macOS Installation</b></summary>

**Option 1: Homebrew (Recommended)**
```bash
brew install p7zip
```

Then use auto-detection:
```python
from p7zip.binary import auto_detect_binary
auto_detect_binary()
```

**Option 2: Manual**
1. Download from [7-zip.org](https://www.7-zip.org/download.html)
2. Install and configure:
   ```python
   from p7zip.binary import set_binary_path
   set_binary_path("/usr/local/bin/7zz")
   ```

</details>

<details>
<summary><b>🐧 Linux Installation</b></summary>

**Option 1: Package Manager (Recommended)**
```bash
# Ubuntu/Debian
sudo apt install p7zip-full

# Fedora
sudo dnf install p7zip-full

# Arch Linux
sudo pacman -S p7zip
```

Then use auto-detection:
```python
from p7zip.binary import auto_detect_binary
auto_detect_binary()
```

**Option 2: Simple use auto_detect_binary**
Most Linux distros include 7za binary after installation. Just call:
```python
from p7zip.binary import auto_detect_binary
auto_detect_binary()
```

**Option 3: Manual Installation**
1. Download from [7-zip.org](https://www.7-zip.org/download.html)
2. Extract and configure:
   ```python
   from p7zip.binary import set_binary_path
   set_binary_path("/usr/bin/7zz")
   ```

</details>

---

## 🚀 Quick Start

### 1️⃣ Configure the Binary

```python
from p7zip.binary import auto_detect_binary

# Auto-detect 7-Zip in system PATH or common locations
auto_detect_binary()
```

Or manually set it:
```python
from p7zip.binary import set_binary_path

set_binary_path("/usr/bin/7zz")  # Linux
# set_binary_path(r"C:\Program Files\7-Zip\7z.exe")  # Windows
# set_binary_path("/usr/local/bin/7zz")  # macOS
```

### 2️⃣ Use the Simple API

```python
from p7zip.api import (
    extract_all, compress, compress_as_7z,
    list_archive_contents, verify_archive_integrity
)

# Create an archive
compress("backup.7z", ["documents/", "photos/", "config.ini"])

# Extract an archive
extract_all("backup.7z", destination="restored/")

# List contents
files = list_archive_contents("backup.7z")
print(f"Archive contains {len(files)} files")

# Verify integrity
is_valid = verify_archive_integrity("backup.7z")
if is_valid:
    print("✓ Archive is OK")
else:
    print(f"✗ Archive is corrupted")
```

### 3️⃣ With Encryption & Progress

```python
def show_progress(archivename, percentage, filename):
    print(f"[{percentage:3d}%] {archivename}")

# Create encrypted archive
compress_as_7z(
    "secure.7z",
    ["sensitive_data/"],
    password="mypassword",
    compression_level=9,
    encrypt_headers=True,
    progress_callback=show_progress
)

# Extract encrypted archive
extract_all(
    "secure.7z",
    destination="output/",
    password="mypassword",
    progress_callback=show_progress
)
```

### 4️⃣ Advanced Features

```python
from p7zip.core import SevenZipArchive
from p7zip.enums import CompressionLevel, OverwriteMode

# Full control with SevenZipArchive
with SevenZipArchive("advanced.7z", mode="w") as archive:
    archive.set_password("secret123")
    archive.compress(
        sources=["documents/", "photos/"],
        include_patterns=["*.pdf", "*.jpg", "*.png"],  # Only these
        exclude_patterns=["*.tmp", "*/__pycache__/*"],  # Except these
        compression_level=CompressionLevel.MAXIMUM,
        encrypt_headers=True,
        compression_method="deflate"
    )

# Extract with pattern filtering
with SevenZipArchive("archive.7z", mode="r") as archive:
    archive.set_password("secret123")
    failed = archive.extract(
        destination="output/",
        include_patterns=["*.pdf"],  # Only PDFs
        overwrite_mode=OverwriteMode.SKIP_EXISTING
    )
    if failed:
        print(f"CRC errors in: {failed}")
```

---

## 🎓 API Overview

### Simple API Functions

The `p7zip.api` module provides high-level functions for common tasks:

```python
from p7zip.api import (
    extract_all,              # Extract entire archive
    extract_files,            # Extract specific files
    extract_by_pattern,       # Extract with glob patterns
    compress,                 # Create compressed file
    compress_as_7z,           # Create 7z archive
    compress_as_zip,          # Create ZIP archive
    list_archive_contents,    # List all files
    verify_archive_integrity, # Test archive integrity
)
```

### Advanced Class

For complete control, use `SevenZipArchive`:

```python
from p7zip.core import SevenZipArchive
from p7zip.enums import CompressionLevel, OverwriteMode, DeleteMode

# Write mode (create/compress)
with SevenZipArchive("archive.7z", mode="w") as archive:
    archive.set_password("secret")
    archive.compress(
        sources=["file1.txt", "directory/"],
        compression_level=CompressionLevel.MAXIMUM,
        include_patterns=["*.py", "*.txt"],
        exclude_patterns=["__pycache__/*"],
        encrypt_headers=True,
        delete_after_compression=DeleteMode.USE_TRASH
    )

# Read mode (extract)
with SevenZipArchive("archive.7z", mode="r") as archive:
    archive.set_password("secret")
    failed_files = archive.extract(
        destination="output/",
        specific_files_or_dirs=["file1.txt"],
        overwrite_mode=OverwriteMode.SKIP_EXISTING
    )
```

### Progress Callbacks

Track operations in real-time:

```python
def progress_callback(archivename: str, percentage: int, filename: str) -> None:
    """Called during compression/extraction."""
    print(f"[{percentage:3d}%] {archivename}")

def completion_callback(archivename: str, message: str) -> None:
    """Called when operation completes."""
    print(f"✓ {message}")

with SevenZipArchive("archive.7z", mode="w",
                    progress_callback=progress_callback,
                    completion_callback=completion_callback) as archive:
    archive.compress(["data/"])
```

---

## 🎯 Compression Levels

Supports compression levels 0-9:

```python
from p7zip.api import compress_as_7z
from p7zip.enums import CompressionLevel

# Quick backup
# CompressionLevel.FASTEST = 1
compress_as_7z("fast.7z", ["data/"], compression_level=CompressionLevel.FASTEST)

# Archive backup (small size)
# CompressionLevel.MAXIMUM = 7
compress_as_7z("compact.7z", ["data/"], compression_level=CompressionLevel.MAXIMUM)
```

---

## 💡 Examples

### Example 1: Selective Extraction with Progress

```python
from p7zip.api import extract_by_pattern

def show_progress(archivename, percentage, filename):
    print(f"[{percentage:3d}%] Extracting: {archivename}")

# Extract only PDF files
failed = extract_by_pattern(
    "archive.7z",
    destination="docs/",
    include_patterns=["*.pdf", "*.txt"],
    progress_callback=show_progress
)

if failed:
    print(f"⚠️ CRC errors: {failed}")
else:
    print("✓ All files extracted successfully")
```

### Example 2: Encrypted Backup with Verification

```python
from p7zip.api import compress_as_7z, verify_archive_integrity

def backup_with_verification(source_dir, backup_file, password):
    """Create and verify an encrypted backup."""
    
    print("Creating backup...")
    compress_as_7z(
        backup_file,
        [source_dir],
        password=password,
        compression_level=9,
        encrypt_headers=True
    )
    
    print("Verifying backup...")
    is_valid = verify_archive_integrity(backup_file, password)
    
    if is_valid:
        print(f"✓ Backup verified: {backup_file}")
        return True
    else:
        print(f"✗ Backup corrupted.")
        return False

# Create secure backup
backup_with_verification("important_data/", "backup.7z", "secure_password_123")
```

### Example 3: Multi-Format Compression

```python
from p7zip.api import compress_as_7z, compress_as_zip

# Create both 7z and zip versions
sources = ["documents/", "images/"]

# Maximum compression (7z)
compress_as_7z(
    "archive.7z",
    sources,
    compression_level=9,
    exclude_patterns=["*.tmp", "__pycache__/*"]
)

# Standard zip (for compatibility)
compress_as_zip(
    "archive.zip",
    sources,
    compression_level=6,
    exclude_patterns=["*.tmp", "__pycache__/*"]
)

print("✓ Created archive.7z and archive.zip")
```

### Example 4: Progress Bar Integration

```python
from p7zip.api import extract_all
try:
    from tqdm import tqdm
except ImportError:
    print("Install tqdm: pip install tqdm")
    exit(1)

pbar = None

def progress_callback(archivename, percentage, filename):
    global pbar
    if pbar is None:
        pbar = tqdm(total=100, desc="Extracting", unit="%")
    pbar.n = percentage
    pbar.set_postfix_str(archivename[:40])
    pbar.refresh()

def completion_callback(archivename, message):
    global pbar
    if pbar:
        pbar.close()
    print(f"✓ {message}")

extract_all(
    "large_archive.7z",
    destination="output/",
    progress_callback=progress_callback
)
```

---

## 🚨 Error Handling

```python
from p7zip.api import extract_all
from p7zip.exceptions import (
    BinaryNotFoundError,
    CRCFailedError,
    InvalidPasswordError,
    CannotOpenArchiveError
)

try:
    extract_all("backup.7z", destination="output/", password="secret")
    
except BinaryNotFoundError as e:
    print(f"✗ 7-Zip not found: {e}")
    print("Install 7-Zip first!")
    
except InvalidPasswordError as e:
    print(f"✗ Wrong password: {e}")
    
except CannotOpenArchiveError as e:
    print(f"✗ Invalid archive: {e}")
    
except CRCFailedError as e:
    print(f"✗ Archive corrupted. Failed files: {e.failed_files}")
```

### Exception Types

- `BinaryNotFoundError` - 7-Zip binary not found
- `InvalidPasswordError` - Wrong password for encrypted archive
- `CannotOpenArchiveError` - Archive is invalid or corrupted
- `CRCFailedError` - CRC check failed (contains list of failed files)
- `SevenZipExecutionError` - General execution error

---

## 🧪 Testing

```bash
# Run all tests (7-Zip auto-detected automatically)
pytest tests/

# Run with coverage
pytest --cov=p7zip tests/

# Run specific test file
pytest tests/test_core.py -v

# Run integration tests only
pytest -m integration

# Run unit tests only
pytest -m unit
```

**Note:** The test suite automatically detects and configures the 7-Zip binary using `auto_detect_binary()`.

---

## 📁 Project Structure

```
p7zip/
├── src/
│   └── p7zip/
│       ├── __init__.py              # Public API exports
│       ├── api.py                   # High-level convenience functions
│       ├── binary.py                # Binary detection & management
│       ├── core.py                  # SevenZipArchive class
│       ├── command_executor.py      # 7z command execution
│       ├── pattern_filter.py        # File pattern matching
│       ├── filesystem_utils.py      # File system utilities
│       ├── exceptions.py            # Custom exceptions
│       ├── enums.py                 # Enumerations
│       ├── types.py                 # Type definitions
│       └── py.typed                 # PEP 561 marker
├── tests/
│   ├── conftest.py                  # Test configuration & fixtures
|   ├── test_binary.py               # Binary detection tests
│   ├── test_core.py                 # Core functionality tests
│   ├── test_pattern_filter.py       # Pattern matching tests
│   └── test_command_executor.py     # Command execution tests
├── README.md
├── LICENSE
└── pyproject.toml
```

---

## ❓ FAQ

<details>
<summary><b>How do I set up the 7-Zip binary?</b></summary>

**Option 1: Auto-detection (Recommended)**
```python
from p7zip.binary import auto_detect_binary
auto_detect_binary()  # Finds 7z automatically
```

**Option 2: Manual configuration**
```python
from p7zip.binary import set_binary_path
set_binary_path("/usr/bin/7zz")
```

Auto-detection works great on Windows (checks Program Files), macOS (uses Homebrew), and Linux (searches PATH).

</details>

<details>
<summary><b>Does p7zip support multiple archive formats?</b></summary>

Yes! Since p7zip uses 7-Zip CLI, it supports:
- **7z** - 7-Zip format (default)
- **zip** - ZIP format
- **tar** - Tar archives
- **gzip** - GZIP compression
- **bzip2** - BZIP2 compression
- **xz** - XZ compression
- And many more formats supported by 7-Zip

```python
from p7zip.api import compress_as_7z, compress_as_zip

compress_as_7z("archive.7z", ["data/"])    # 7z format
compress_as_zip("archive.zip", ["data/"])   # ZIP format

# You can also specify format in SevenZipArchive

# Simple pass extension for establishing format (7-Zip autodetect format to compress)
with SevenZipArchive("archive.tar", mode="w") as archive:
    archive.compress(["data/"])

# Or use format for more control (In case you want to use a name with a different extension than the format you want to compress in, for example: archive.bin)
from p7zip.core import SevenZipArchive
with SevenZipArchive("archive.bin", mode="w") as archive:
    archive.compress(["data/"], format="tar")
```

</details>

<details>
<summary><b>How accurate are progress callbacks?</b></summary>

Very accurate! Progress callbacks parse 7-Zip's native output in real-time, providing:
- Actual percentage completion
- Current file being processed
- Immediate updates during operation

```python
def show_progress(archivename, percentage, filename):
    print(f"[{percentage}%] {archivename}")

extract_all("archive.7z", progress_callback=show_progress)
```

</details>

<details>
<summary><b>Can I use pattern matching for selective operations?</b></summary>

Yes! Use `include_patterns` and `exclude_patterns`:

```python
from p7zip.core import SevenZipArchive

with SevenZipArchive("archive.7z", mode="w") as archive:
    archive.compress(
        sources=["data/"],
        include_patterns=["*.py", "*.txt"],  # Only Python and text files
        exclude_patterns=["__pycache__/*", "*.pyc"]  # Skip these
    )
```

Patterns support glob syntax:
- `*.ext` - Match by extension
- `dir/*` - Match in directory
- `**/file` - Match anywhere in tree

</details>

<details>
<summary><b>Why doesn't p7zip include 7-Zip binary?</b></summary>

For several reasons:
- **Lightweight package** - No large binary bloat
- **User control** - Use your preferred 7-Zip version
- **License clarity** - p7zip (MIT) and 7-Zip (LGPL) stay separate
- **Platform flexibility** - Use system-installed versions

p7zip just needs the 7z CLI tool, which is easy to install:
- **Windows**: Download from 7-zip.org or use installer
- **macOS**: `brew install p7zip`
- **Linux**: `sudo apt install p7zip-full` (or equivalent)

</details>

---

## 📄 License

**p7zip** is licensed under the [MIT License](LICENSE).

### Third-Party Dependencies

> ⚠️ **Important:** This library requires 7-Zip but does NOT distribute it.

- **send2trash** - Licensed under BSD 3-Clause license
- **Website:** [github.com/arsenetar/send2trash](https://github.com/arsenetar/send2trash/)

- **7-Zip** - Licensed under GNU LGPL with unRAR restriction
- **Website:** [7-zip.org](https://www.7-zip.org/)
- **Copyright:** © 1999-2024 Igor Pavlov
- **License:** [7-zip.org/license.txt](https://www.7-zip.org/license.txt)

Users must download and install 7-Zip separately. p7zip is merely a Python wrapper for the 7-Zip CLI tool.

---

<div align="center">

[🐛 Report Bug](https://github.com/mzdevx/p7zip/issues) · [💡 Request Feature](https://github.com/mzdevx/p7zip/issues) · [⭐ Star on GitHub](https://github.com/mzdevx/p7zip)

</div>
