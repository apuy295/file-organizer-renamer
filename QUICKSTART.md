# Quick Start Guide

## First Time Setup

1. **Check Python Installation**
   ```bash
   python --version
   ```
   Should show Python 3.6 or higher.

2. **Navigate to Project Folder**
   ```bash
   cd "d:\File Organizer + Renamer"
   ```

3. **Create Test Environment** (Recommended for first-time users)
   ```bash
   python test_setup.py
   ```
   This creates a test folder on your Desktop with sample files.

## Basic Usage

### 🔍 Preview (Safe - No Changes Made)
```bash
python main.py --preview "C:\Path\To\Your\Folder"
```

### ✅ Apply (Makes Changes)
```bash
python main.py --apply "C:\Path\To\Your\Folder"
```

### ↩️ Undo
```bash
python main.py --undo
```

## Common Commands

| Task | Command |
|------|---------|
| Preview Downloads folder | `python main.py --preview "C:\Users\YourName\Downloads"` |
| Organize Downloads | `python main.py --apply "C:\Users\YourName\Downloads"` |
| Preview with date prefix | `python main.py --preview "C:\Path" --date-prefix` |
| Undo last operation | `python main.py --undo` |
| Show help | `python main.py --help` |

## Safety Tips

✅ **DO:**
- Always use `--preview` first
- Test on a small folder first
- Keep important files backed up
- Review the preview output carefully

❌ **DON'T:**
- Use on system folders without backing up
- Skip the preview step
- Organize folders with files currently in use

## Troubleshooting

**Problem:** "python is not recognized"
- **Solution:** Make sure Python is installed and in your PATH

**Problem:** "Permission denied"
- **Solution:** Close programs using the files, or run as administrator

**Problem:** "No files found"
- **Solution:** Make sure you're pointing to a folder with files (not a folder with only subfolders)

## Getting Help

1. Read the full [README.md](README.md)
2. Run `python examples.py` to see usage examples
3. Check log files in the `logs/` folder for operation details

---

**Remember:** This tool is designed to be safe. It won't modify anything without your confirmation! 🔒
