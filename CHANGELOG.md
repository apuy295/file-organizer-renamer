# Changelog

All notable changes to File Organizer + Renamer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-01

### Added
- **Core Features**
  - File categorization by extension (images, videos, documents, etc.)
  - Smart file renaming with customizable rules
  - Preview mode to see changes before applying
  - Apply mode with user confirmation requirement
  - Dry-run mode (alias for preview)
  
- **Safety Features**
  - No-overwrite policy with automatic conflict resolution
  - Numbered suffixes for duplicate filenames (1), (2), etc.
  - Comprehensive operation logging to JSON files
  - Undo functionality to reverse operations
  - Atomic file operations (no partial moves)
  - Per-file error handling (one failure doesn't stop others)

- **Renaming Rules (v1)**
  - Convert filenames to lowercase
  - Replace spaces with underscores
  - Remove duplicate underscores
  - Optional date prefix (YYYYMMDD_)

- **Error Handling**
  - Permission denied errors
  - File in use errors
  - File not found errors
  - Invalid directory paths
  - Clear error messages for all failure modes

- **CLI Interface**
  - `--preview` mode for safe planning
  - `--apply` mode for execution
  - `--undo` mode for reversing operations
  - `--dry-run` mode (preview alias)
  - `--date-prefix` flag for adding date prefixes
  - Help text with examples

- **File Categories**
  - images: jpg, png, gif, bmp, svg, webp, ico, tiff, raw
  - videos: mp4, avi, mkv, mov, wmv, flv, webm, m4v, mpg, mpeg
  - documents: pdf, doc, docx, txt, rtf, odt, xls, xlsx, ppt, pptx, csv
  - installers: exe, msi, dmg, pkg, deb, rpm, appimage
  - archives: zip, rar, 7z, tar, gz, bz2, xz
  - audio: mp3, wav, flac, aac, ogg, wma, m4a
  - code: py, js, java, cpp, c, h, cs, php, rb, go, rs, html, css
  - others: everything else

- **Documentation**
  - Comprehensive README.md with examples
  - Quick Start Guide (QUICKSTART.md)
  - Architecture documentation (ARCHITECTURE.md)
  - Usage examples (examples.py)
  - Test setup script (test_setup.py)
  - MIT License

- **Logging**
  - JSON-based operation logs
  - Timestamped log files
  - Success/failure tracking
  - Error message logging
  - Undo capability from logs

### Technical Details
- **Language:** Python 3.6+
- **Dependencies:** None (standard library only)
- **Platform:** Windows (cross-platform compatible)
- **Operation:** Fully offline
- **Telemetry:** None

### Known Limitations
- Single directory level only (no recursive scanning)
- Windows path handling optimized
- 10,000 conflict limit per filename

## [Unreleased]

### Planned Features
- Interactive mode with per-file confirmation
- Custom renaming templates
- Regex-based categorization rules
- Batch undo (multiple operations)
- GUI interface option
- Configuration file support (.ini or .yaml)
- Progress bars for large operations
- Parallel file operations for performance

### Under Consideration
- Multiple directory scanning
- Custom category creation via CLI
- File content-based categorization
- Duplicate file detection
- Recursive undo
- Export operation reports to CSV

---

## Version History

- **1.0.0** (2026-02-01) - Initial release

## Contributing

When contributing, please:
1. Update this CHANGELOG.md with your changes
2. Follow the format: Added/Changed/Deprecated/Removed/Fixed/Security
3. Link to relevant issues or pull requests
4. Maintain chronological order (newest first)

---

**Note:** This project follows semantic versioning:
- MAJOR: Incompatible API changes
- MINOR: Backwards-compatible functionality
- PATCH: Backwards-compatible bug fixes
