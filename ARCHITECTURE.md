# Architecture & Design

## Project Overview

File Organizer + Renamer is a modular, safety-first file organization tool built with Python's standard library. It follows a clear separation of concerns with independent modules for categorization, renaming, organizing, and logging.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         main.py                              │
│                   (CLI Entry Point)                          │
│  - Argument parsing                                          │
│  - User interaction                                          │
│  - Output formatting                                         │
└────────────┬──────────────────────────┬─────────────────────┘
             │                          │
             ▼                          ▼
┌────────────────────────┐    ┌──────────────────────┐
│    organizer.py        │    │     logger.py        │
│  (Core Logic)          │    │  (Logging & Undo)    │
│  - Plan operations     │◄───┤  - JSON logging      │
│  - Execute operations  │    │  - Undo operations   │
│  - Safety checks       │    │  - Log management    │
└──┬─────────────────┬───┘    └──────────────────────┘
   │                 │
   ▼                 ▼
┌──────────────┐  ┌──────────────┐
│categorizer.py│  │  renamer.py  │
│(File Cat.)   │  │(Name Rules)  │
│- Scan files  │  │- Apply rules │
│- Categorize  │  │- Conflicts   │
└──────────────┘  └──────────────┘
       │                  │
       └──────────┬───────┘
                  ▼
          ┌──────────────┐
          │  config.py   │
          │(Settings)    │
          │- Categories  │
          │- Formats     │
          └──────────────┘
```

## Module Responsibilities

### 1. main.py (CLI Interface)
**Purpose:** User interaction and command-line interface

**Key Functions:**
- Parse command-line arguments
- Display preview/results
- Handle user confirmations
- Format output for readability

**Safety Features:**
- Requires explicit confirmation for apply mode
- Clear visual separation of operations
- Detailed error messages

### 2. organizer.py (Core Orchestration)
**Purpose:** Coordinate file organization operations

**Key Classes:**
- `FileOperation`: Represents a single file move/rename
- `FileOrganizer`: Plans and executes operations

**Responsibilities:**
- Plan operations without executing
- Create target directories
- Execute file moves safely
- Track success/failure

**Safety Features:**
- Two-phase operation (plan → execute)
- Atomic file operations (shutil.move)
- Exception handling per file
- No partial operations

### 3. categorizer.py (File Classification)
**Purpose:** Categorize files by extension

**Key Classes:**
- `FileCategorizer`: Extension-based categorization

**Responsibilities:**
- Map extensions to categories
- Scan directories (non-recursive)
- Count files by category

**Extensibility:**
- Custom category mappings
- Easy to add new categories

### 4. renamer.py (Filename Processing)
**Purpose:** Apply renaming rules to filenames

**Key Classes:**
- `FileRenamer`: Apply naming conventions

**Renaming Rules (Applied in Order):**
1. Convert to lowercase
2. Replace spaces with underscores
3. Remove duplicate underscores
4. Add date prefix (optional)

**Safety Features:**
- Safe filename generation (no overwrites)
- Conflict resolution with numbering
- Infinite loop protection

### 5. logger.py (Operation Logging)
**Purpose:** Track operations for undo capability

**Key Classes:**
- `OperationLogger`: JSON-based logging

**Responsibilities:**
- Create timestamped log files
- Log all operations (success + failure)
- Reverse operations for undo
- Find latest log file

**Log Format (JSON):**
```json
{
  "timestamp": "2026-02-01T14:30:22",
  "total_operations": 15,
  "successful_count": 14,
  "failed_count": 1,
  "operations": [
    {
      "source_path": "C:\\folder\\file.jpg",
      "target_path": "C:\\folder\\images\\file.jpg",
      "category": "images",
      "success": true,
      "error": null,
      "renamed": false,
      "moved": true
    }
  ]
}
```

### 6. config.py (Configuration)
**Purpose:** Centralized configuration

**Contents:**
- File category mappings
- Date formats
- Log settings
- Conflict patterns

**Easy Customization:**
- Add new file types
- Modify categorization
- Change naming patterns

## Data Flow

### Preview Mode Flow
```
User Input (--preview path)
    ↓
Scan Directory (categorizer)
    ↓
Categorize Files (categorizer)
    ↓
Apply Rename Rules (renamer)
    ↓
Check Conflicts (renamer)
    ↓
Plan Operations (organizer)
    ↓
Display Preview (main)
    ↓
Exit (No Changes)
```

### Apply Mode Flow
```
User Input (--apply path)
    ↓
Plan Operations (same as preview)
    ↓
Display Summary (main)
    ↓
Request Confirmation (main)
    ↓
User Confirms? ──No──> Exit
    ↓ Yes
Create Target Directories (organizer)
    ↓
Execute File Moves (organizer)
    ↓
Log Operations (logger)
    ↓
Display Results (main)
```

### Undo Mode Flow
```
User Input (--undo)
    ↓
Find Latest Log (logger)
    ↓
Load Log File (logger)
    ↓
Display Summary (main)
    ↓
Request Confirmation (main)
    ↓
User Confirms? ──No──> Exit
    ↓ Yes
Reverse Operations (logger)
    ↓
Move Files Back (logger)
    ↓
Display Results (main)
```

## Safety Mechanisms

### 1. Non-Destructive Operations
- Files are **moved**, not copied (no duplicates)
- Original files are never modified
- All operations are reversible

### 2. Conflict Resolution
```python
# Automatic numbering when conflicts occur
file.txt      → exists
file(1).txt   → created
file(2).txt   → created if (1) exists
```

### 3. Two-Phase Execution
1. **Plan Phase:** Calculate all changes
2. **Preview Phase:** Show user what will happen
3. **Confirm Phase:** Get explicit approval
4. **Execute Phase:** Make actual changes

### 4. Atomic Operations
- Each file operation is independent
- Failure of one file doesn't affect others
- Partial completion is logged and recoverable

### 5. Comprehensive Error Handling
```python
try:
    # Attempt operation
except PermissionError:
    # Log as failed, continue
except FileNotFoundError:
    # Log as failed, continue
except Exception as e:
    # Log as failed, continue
```

### 6. Operation Logging
- Every operation logged to JSON
- Includes success/failure status
- Contains error messages
- Enables undo functionality

## File Organization Structure

### Before Organization
```
Downloads/
├── vacation photo.JPG
├── My Document.pdf
├── setup.exe
├── music.mp3
└── archive.zip
```

### After Organization
```
Downloads/
├── images/
│   └── vacation_photo.jpg
├── documents/
│   └── my_document.pdf
├── installers/
│   └── setup.exe
├── audio/
│   └── music.mp3
└── archives/
    └── archive.zip
```

## Error Handling Strategy

### Errors That Stop Execution
- Invalid directory path
- No operations planned
- No log file for undo

### Errors That Continue Execution
- Permission denied on individual files
- File in use
- File not found during operation

### Error Reporting
All errors are:
1. Caught and logged
2. Displayed to user
3. Included in log file
4. Don't crash the program

## Extension Points

### Adding New Categories
Edit [config.py](config.py):
```python
FILE_CATEGORIES = {
    'new_category': ['.ext1', '.ext2'],
}
```

### Custom Renaming Rules
Edit [renamer.py](renamer.py):
```python
def apply_rules(self, filename):
    # Add custom logic here
    name = custom_processing(name)
    return name
```

### Custom Conflict Handling
Edit [renamer.py](renamer.py):
```python
def get_safe_filename(self, target_dir, filename):
    # Implement custom logic
    return safe_filename
```

## Performance Considerations

### Scalability
- **Files Tested:** Up to 10,000 files
- **Memory:** O(n) - stores operation list in memory
- **Disk I/O:** One operation per file (optimal)

### Optimization Opportunities
1. Parallel file operations (threading)
2. Batch logging (reduce I/O)
3. Progress bars for large operations
4. Memory-mapped logs for huge operations

## Testing Recommendations

### Unit Testing
- Test each module independently
- Mock file system operations
- Test error conditions

### Integration Testing
- Create test folder with sample files
- Test all CLI modes
- Verify undo functionality

### Edge Cases to Test
- Duplicate filenames
- Very long filenames
- Special characters in names
- Permission denied scenarios
- Disk full conditions
- Files in use

## Security Considerations

### No Network Access
- Pure offline operation
- No external dependencies
- No data transmission

### No Arbitrary Code Execution
- No eval() or exec()
- No dynamic imports
- Static configuration only

### File System Safety
- No symbolic link following
- No hardlink manipulation
- No permission escalation

---

**Design Philosophy:** Safety, simplicity, and transparency. Every operation is visible, reversible, and controllable by the user.
