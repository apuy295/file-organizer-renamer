# Frequently Asked Questions (FAQ)

## General Questions

### Q: What does this tool do?
**A:** File Organizer + Renamer automatically categorizes files in a folder by their extension (images, documents, videos, etc.) and optionally renames them according to predefined rules. It's designed to help you organize messy folders like Downloads.

### Q: Is it safe to use?
**A:** Yes! Safety is the primary design goal:
- Preview mode shows all changes before applying
- No files are overwritten (conflicts get numbered)
- All operations are logged and reversible
- Works completely offline
- Requires your confirmation before making changes

### Q: Does it modify file contents?
**A:** No, it only moves and renames files. The actual file content is never modified.

### Q: Can I undo operations?
**A:** Yes! Every operation creates a log file that can be used to undo the changes:
```bash
python main.py --undo
```

## Installation & Setup

### Q: What do I need to install?
**A:** Only Python 3.6 or higher. No additional packages are required.

### Q: How do I check if Python is installed?
**A:** Run this in a terminal:
```bash
python --version
```

### Q: Do I need to install any packages?
**A:** No! The tool uses only Python's standard library. No pip install needed.

### Q: How do I test the tool safely?
**A:** Run the test setup script to create a test folder:
```bash
python test_setup.py
```

## Usage Questions

### Q: What's the difference between --preview and --apply?
**A:** 
- `--preview`: Shows what would happen WITHOUT making any changes
- `--apply`: Actually executes the file operations (after confirmation)

Always use `--preview` first to see what will happen.

### Q: What does --dry-run do?
**A:** It's the same as `--preview`. Just alternative naming for users who prefer that term.

### Q: How do I organize my Downloads folder?
**A:**
```bash
# Step 1: Preview
python main.py --preview "C:\Users\YourName\Downloads"

# Step 2: Review the output, then apply
python main.py --apply "C:\Users\YourName\Downloads"
```

### Q: What does the --date-prefix flag do?
**A:** It adds the current date (YYYYMMDD_) to the beginning of filenames:
- `photo.jpg` → `20260201_photo.jpg`
- `document.pdf` → `20260201_document.pdf`

### Q: Can I organize multiple folders?
**A:** The tool processes one folder at a time. Run it separately for each folder you want to organize.

### Q: Does it organize subfolders?
**A:** No, it only processes files in the specified folder. Subfolders are not scanned.

## File Operations

### Q: What happens if two files have the same name?
**A:** The tool automatically adds numbers to avoid conflicts:
- First file: `photo.jpg`
- Second file: `photo(1).jpg`
- Third file: `photo(2).jpg`

### Q: What categories are files organized into?
**A:**
- **images**: jpg, png, gif, bmp, svg, webp, etc.
- **videos**: mp4, avi, mkv, mov, wmv, etc.
- **documents**: pdf, doc, docx, txt, xls, ppt, csv, etc.
- **installers**: exe, msi, dmg, pkg, deb, rpm, etc.
- **archives**: zip, rar, 7z, tar, gz, etc.
- **audio**: mp3, wav, flac, aac, ogg, etc.
- **code**: py, js, java, cpp, html, css, etc.
- **others**: everything that doesn't match above

### Q: Can I add custom categories?
**A:** Yes! Edit [config.py](config.py) and add your category:
```python
FILE_CATEGORIES = {
    'my_category': ['.custom', '.special'],
}
```

### Q: What renaming rules are applied?
**A:**
1. Convert to lowercase
2. Replace spaces with underscores
3. Remove duplicate underscores
4. Optionally add date prefix

Example: `My Photo.JPG` → `my_photo.jpg`

### Q: Can I customize the renaming rules?
**A:** Yes! Edit the `apply_rules()` method in [renamer.py](renamer.py).

## Undo & Logging

### Q: Where are log files stored?
**A:** In the `logs/` folder in the project directory.

### Q: What format are log files in?
**A:** JSON format, which is human-readable and machine-parseable.

### Q: How do I undo a specific operation?
**A:** Provide the log file path:
```bash
python main.py --undo "logs\file_organizer_20260201_143022.json"
```

### Q: What if I can't undo?
**A:** Undo might fail if:
- Files were deleted after organization
- Files were moved manually after organization
- You don't have permissions to the original location

### Q: Can I undo multiple operations?
**A:** Currently, you can only undo one operation at a time. Run `--undo` multiple times for multiple operations.

## Error Handling

### Q: What if I get "Permission denied"?
**A:** This means:
- A file is in use by another program (close it)
- You don't have permission (try running as administrator)
- The file/folder is protected by Windows

### Q: What if the tool says "No files found"?
**A:** This means:
- The folder is empty
- The folder only contains subfolders (no direct files)
- You may have specified the wrong path

### Q: What happens if the tool crashes mid-operation?
**A:** The tool processes files one by one. Already-processed files won't be rolled back automatically, but you can:
1. Check the log file to see what succeeded
2. Use `--undo` to reverse successful operations
3. Manually fix any issues

### Q: What if a file is in use?
**A:** The tool will:
- Skip that file
- Mark it as failed in the log
- Continue with other files
- Report the error at the end

## Safety & Privacy

### Q: Does this tool send data anywhere?
**A:** No! It works completely offline. No network calls, no telemetry, no external services.

### Q: What data is collected?
**A:** Nothing! No usage statistics, no analytics, no tracking.

### Q: Is my data private?
**A:** Yes! Everything happens locally on your computer. The tool never accesses the internet.

### Q: Can I use this on sensitive files?
**A:** Yes, since it works offline and doesn't modify file contents. However, always backup important files first.

### Q: Does it need internet access?
**A:** No, it works completely offline.

## Troubleshooting

### Q: The tool won't run
**A:** Check:
1. Python is installed: `python --version`
2. You're in the correct directory: `cd "d:\File Organizer + Renamer"`
3. You're running the correct command: `python main.py --help`

### Q: I see "python is not recognized"
**A:** Python is not in your system PATH. Either:
- Reinstall Python and check "Add to PATH" during installation
- Use the full path: `C:\Python39\python.exe main.py --preview ...`

### Q: The preview shows no changes
**A:** This could mean:
- All files are already named correctly
- The folder has no files (only subdirectories)
- Files don't match any categories (they'll go to "others")

### Q: Files aren't being renamed
**A:** Check if the filenames already match the rules:
- Already lowercase
- Already using underscores
- No duplicate underscores

### Q: Undo isn't working
**A:** Possible reasons:
- No log files exist (never ran with `--apply`)
- Files were moved/deleted after organization
- Permissions have changed
- Log file is corrupted

### Q: I want to organize system folders
**A:** **Not recommended!** Only organize user folders like:
- Downloads
- Desktop
- Documents
- Pictures

Never organize:
- C:\Windows
- C:\Program Files
- System directories

## Advanced Usage

### Q: Can I automate this tool?
**A:** Yes! You can:
1. Create a batch script (.bat) with your common commands
2. Schedule it with Windows Task Scheduler
3. Run it from other Python scripts

**Important:** Don't use `--apply` in automated scripts without careful consideration!

### Q: Can I use this in a script?
**A:** Yes! Import the modules:
```python
from organizer import FileOrganizer
org = FileOrganizer("C:\\path\\to\\folder")
ops = org.plan_operations()
```

### Q: How do I show help?
**A:**
```bash
python main.py --help
```

### Q: Can I see examples?
**A:**
```bash
python examples.py
```

## Performance

### Q: How many files can it handle?
**A:** Tested with up to 10,000 files. Should work with more, but performance will depend on your system.

### Q: Is it fast?
**A:** Yes! File operations are atomic and efficient. The bottleneck is typically disk I/O, not the tool.

### Q: Does it use a lot of memory?
**A:** No, memory usage is proportional to the number of files (O(n)). Each file operation is stored in memory for logging.

## Contributing & Customization

### Q: Can I contribute to this project?
**A:** Yes! The project is open source under MIT license.

### Q: How do I modify the categories?
**A:** Edit [config.py](config.py) and modify `FILE_CATEGORIES`.

### Q: How do I change the renaming rules?
**A:** Edit [renamer.py](renamer.py) and modify the `apply_rules()` method.

### Q: Can I add a GUI?
**A:** Yes! The core logic is separate from the CLI. You can build a GUI that uses the same modules.

## Getting Help

### Q: Where can I find more documentation?
**A:**
- [README.md](README.md) - Main documentation
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical details
- [examples.py](examples.py) - Usage examples

### Q: How do I report a bug?
**A:** Check the log files in the `logs/` folder for error details.

### Q: I have a feature request
**A:** The project is designed to be simple and safe. Complex features may conflict with the safety-first philosophy.

---

## Quick Command Reference

| What I want to do | Command |
|-------------------|---------|
| See what would happen | `python main.py --preview "path"` |
| Organize files | `python main.py --apply "path"` |
| Add date to filenames | `python main.py --preview "path" --date-prefix` |
| Undo last operation | `python main.py --undo` |
| Get help | `python main.py --help` |
| See examples | `python examples.py` |
| Create test folder | `python test_setup.py` |

---

**Still have questions?** Check the full documentation in [README.md](README.md) or review the code - it's well-commented!
