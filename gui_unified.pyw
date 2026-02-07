#!/usr/bin/env python3
"""
File Organizer + Renamer - UNIFIED GUI
One tool with two modes: Organize a folder OR Collect files from across PC
"""

import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from threading import Thread
from organizer import FileOrganizer, cleanup_empty_folders
from collector import FileCollector
from logger import OperationLogger
from duplicate_detector import DuplicateDetector
from date_organizer import DateOrganizer
import sys
import subprocess

# Windows taskbar icon fix
if sys.platform == 'win32':
    try:
        import ctypes
        myappid = 'fileorganizer.app.1.0'  # Arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except:
        pass


def copy_file_safe(source, target_dir, base_filename):
    """
    Safely copy a file with conflict resolution
    Avoids TOCTOU bugs by checking existence close to the copy operation
    
    Args:
        source: Source file path
        target_dir: Target directory
        base_filename: Desired filename
        
    Returns:
        Final destination path or None if failed
    """
    counter = 0
    while counter <= 10000:
        # Generate filename
        if counter == 0:
            filename = base_filename
        else:
            base_name, ext = os.path.splitext(base_filename)
            filename = f"{base_name}_{counter}{ext}"
        
        dest_path = os.path.join(target_dir, filename)
        
        # Check if exists (still a small TOCTOU window, but much smaller)
        if os.path.exists(dest_path):
            counter += 1
            continue
        
        try:
            shutil.copy2(source, dest_path)
            return dest_path
        except FileExistsError:
            # File was created between our check and copy - try next counter
            counter += 1
            continue
    
    return None  # Failed after max attempts


class UnifiedGUI:
    """All-in-one file organization tool"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("File Organizer + Renamer")
        self.root.geometry("900x750")
        self.root.state('zoomed')
        self.root.configure(bg="#1e1e1e")  # Dark background
        
        # Set icon if available (check multiple locations)
        try:
            # Try current working directory first (set by VBS launcher)
            icon_path = "icon.ico"
            if not os.path.exists(icon_path):
                # Try script directory
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
            
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            # Debug: print error if icon fails (will show in console if run directly)
            print(f"Icon load failed: {e}")
            pass
        
        self.collector = FileCollector(min_file_size=51200)  # 50KB minimum
        self.scan_results = {}
        self.duplicate_groups = {}  # Store duplicate groups from scan (collect mode)
        self.org_duplicate_groups = {}  # Store duplicate groups from organize mode
        
        self.setup_ui()
    
    def setup_ui(self):
        """Create unified interface"""
        
        # Title area - minimal and clean
        title_frame = tk.Frame(self.root, bg="#0d1117", height=80)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        # Shortcut button in corner
        shortcut_btn = tk.Button(
            title_frame,
            text="🔗 Shortcut",
            command=self.create_desktop_shortcut,
            font=("Segoe UI", 8),
            bg="#238636",
            fg="white",
            padx=12,
            pady=4,
            cursor="hand2",
            relief=tk.FLAT,
            borderwidth=0
        )
        shortcut_btn.place(relx=1.0, x=-130, y=15, anchor="ne")
        
        # Help button in corner
        help_btn = tk.Button(
            title_frame,
            text="Help",
            command=self.show_help,
            font=("Segoe UI", 8),
            bg="#da3633",
            fg="white",
            padx=12,
            pady=4,
            cursor="hand2",
            relief=tk.FLAT,
            borderwidth=0
        )
        help_btn.place(relx=1.0, x=-20, y=15, anchor="ne")
        
        title = tk.Label(
            title_frame,
            text="File Organizer",
            font=("Segoe UI", 22, "bold"),
            bg="#0d1117",
            fg="#c9d1d9"
        )
        title.pack(pady=25)
        
        # Mode selector - clean tabs
        mode_frame = tk.Frame(self.root, bg="#1e1e1e", padx=40, pady=20)
        mode_frame.pack(fill=tk.X)
        
        self.mode = tk.StringVar(value="collect")
        
        # Collect mode button
        self.collect_btn = tk.Button(
            mode_frame,
            text="Find Scattered Files",
            command=lambda: self.switch_mode("collect"),
            font=("Segoe UI", 12, "bold"),
            bg="#238636",
            fg="white",
            activebackground="#2ea043",
            activeforeground="white",
            padx=50,
            pady=15,
            cursor="hand2",
            relief=tk.FLAT,
            borderwidth=0
        )
        self.collect_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10))
        
        # Organize mode button
        self.organize_btn = tk.Button(
            mode_frame,
            text="Organize Folder",
            command=lambda: self.switch_mode("organize"),
            font=("Segoe UI", 12, "bold"),
            bg="#30363d",
            fg="#8b949e",
            activebackground="#3d444d",
            activeforeground="#c9d1d9",
            padx=50,
            pady=15,
            cursor="hand2",
            relief=tk.FLAT,
            borderwidth=0
        )
        self.organize_btn.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        # Content area (will swap between modes)
        self.content_frame = tk.Frame(self.root, padx=60, pady=10, bg="#1e1e1e")
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create both mode panels
        self.tab_organize = tk.Frame(self.content_frame, bg="#1e1e1e")
        self.create_organize_tab()
        
        self.tab_collect = tk.Frame(self.content_frame, bg="#1e1e1e")
        self.create_collect_tab()
        
        # Status bar (dark modern)
        self.status = tk.Label(
            self.root,
            text="Choose a mode above",
            font=("Segoe UI", 9),
            bg="#0d1117",
            fg="#8b949e",
            anchor=tk.W,
            padx=25,
            pady=10
        )
        self.status.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Show collect mode by default
        self.switch_mode()
    
    def switch_mode(self, new_mode=None):
        """Switch between collect and organize modes"""
        if new_mode:
            self.mode.set(new_mode)
        
        # Hide both
        self.tab_organize.pack_forget()
        self.tab_collect.pack_forget()
        
        # Update button colors (dark theme)
        if self.mode.get() == "collect":
            # Left GREEN (selected), right DARK
            self.collect_btn.config(bg="#238636", fg="white")
            self.organize_btn.config(bg="#30363d", fg="#8b949e")
            self.tab_collect.pack(fill=tk.BOTH, expand=True)
            self.status.config(text="Find Mode Active")
            # Rebind mousewheel to collect canvas
            self.bind_collect_scroll()
        else:
            # Left DARK, right GREEN (selected)
            self.collect_btn.config(bg="#30363d", fg="#8b949e")
            self.organize_btn.config(bg="#238636", fg="white")
            self.tab_organize.pack(fill=tk.BOTH, expand=True)
            self.status.config(text="Organize Mode Active")
            # Rebind mousewheel to organize canvas
            self.bind_organize_scroll()
    
    def show_help(self):
        """Show help popup"""
        help_text = r"""
═══════════════════════════════════════════════════════════════════════
📁 FILE ORGANIZER + RENAMER - COMPLETE GUIDE
═══════════════════════════════════════════════════════════════════════

🔍 MODE 1: FIND SCATTERED FILES (Left Blue Button)
═══════════════════════════════════════════════════════════════════════

WHEN TO USE:
• Photos are scattered everywhere (Desktop, Downloads, Documents, etc.)
• Want to collect ALL photos/videos from multiple locations into one place
• Need to consolidate files from across your entire PC

EXAMPLE SCENARIO:
You have screenshots on Desktop, vacation photos in Downloads, project images
in Documents, and videos in random folders. This mode finds them ALL and
organizes them in one location automatically.

WHAT IT DOES:
✓ Searches these safe locations:
  - Desktop
  - Downloads
  - Documents
  - Videos
  - Music
  
✓ Skips these dangerous locations (for safety):
  - C:\Windows
  - C:\Program Files
  - C:\Program Files (x86)
  - AppData folders
  - System folders

✓ Skips tiny files under 50 KB (thumbnails, icons, cache files)

✓ Creates organized folders like:
  images/png/     ← All your PNG files
  images/jpg/     ← All your JPG files
  images/gif/     ← All your GIF files
  videos/mp4/     ← All your MP4 videos
  documents/pdf/  ← All your PDF files

STEP-BY-STEP INSTRUCTIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. CHECK WHAT TO FIND
   ✓ Images - finds jpg, png, gif, bmp, webp, svg, etc.
   ✓ Videos - finds mp4, avi, mkv, mov, wmv, etc.
   ✓ Documents - finds pdf, docx, txt, xlsx, pptx, etc.
   ✓ Audio - finds mp3, wav, flac, aac, etc.
   ✓ Archives - finds zip, rar, 7z, tar, etc.

2. CLICK "SCAN FOR FILES"
   • Searches all safe locations on your PC
   • Shows you what was found
   • Displays count by category (e.g., "images: 342 files")
   • May take 1-2 minutes for first scan

3. REVIEW RESULTS
   • Read the scan results in the text box
   • See how many files were found
   • See where they came from (Desktop, Downloads, etc.)

4. CLICK "CHOOSE" TO PICK DESTINATION
   • Example: C:\MyPhotos
   • Example: D:\Collected Files
   • Pick anywhere you want to collect files

5. CHOOSE ORGANIZATION STYLE
   • By file type (RECOMMENDED) - images/png/, images/jpg/, videos/mp4/
   • By category only - images/, videos/, documents/
   • By source - from_desktop/, from_downloads/, from_documents/

6. CLICK "COLLECT FILES"
   • Copies (NOT moves) files to destination
   • Your originals stay where they are (safe!)
   • Creates organized folder structure automatically
   • Shows progress and results


📂 MODE 2: ORGANIZE ONE FOLDER (Right Blue Button)
═══════════════════════════════════════════════════════════════════════

WHEN TO USE:
• One specific folder is messy (like Downloads, Pictures, or Desktop)
• Files are all in one place but mixed up
• Want to organize an existing folder quickly

EXAMPLE SCENARIO:
Your Downloads folder has 500 files - PDFs, photos, installers, videos all
mixed together. This mode sorts them into neat categories in that same folder.

WHAT IT DOES:
✓ Takes ONE folder you point it at
✓ Scans all files in that folder
✓ Creates category folders: images/, videos/, documents/, installers/, etc.
✓ Creates sub-folders by type: images/png/, images/jpg/, images/gif/
✓ Moves files into the right folders
✓ Can delete empty folders after organizing (optional)

STEP-BY-STEP INSTRUCTIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. CLICK "BROWSE"
   • Pick the messy folder
   • Examples:
     - C:\Users\YourName\Downloads
     - C:\Users\YourName\Pictures
     - C:\Users\YourName\Desktop

2. CHECK OPTIONS (all recommended by default)
   ✓ Create sub-folders by file type
     • Creates images/png/, images/jpg/, images/gif/
     • Keeps things super organized
   
   ✓ Scan all subfolders (recursive)
     • Finds files in nested folders too
     • Example: Downloads\OldStuff\Photos
   
   ✓ Delete empty folders after organizing
     • Cleans up empty folders left behind
     • Makes folder structure cleaner

3. CLICK "PREVIEW" (OPTIONAL BUT RECOMMENDED)
   • Shows exactly what will happen
   • No changes made yet
   • See where each file will go
   • Perfect for checking before committing

4. CLICK "ORGANIZE"
   • Confirms with you first
   • Moves all files into organized folders
   • Shows progress and results
   • Logs everything for undo

5. IF YOU DON'T LIKE IT, CLICK "UNDO"
   • Reverses ALL changes
   • Puts files back where they were
   • Uses the log file to restore everything


⚠️ SAFETY FEATURES - YOU'RE PROTECTED!
═══════════════════════════════════════════════════════════════════════

✓ NEVER OVERWRITES FILES
  If photo.jpg already exists, it saves as photo_1.jpg, photo_2.jpg, etc.
  Your files are NEVER lost or replaced!

✓ FULL UNDO CAPABILITY
  Every operation is logged in: logs/file_organizer_YYYYMMDD_HHMMSS.json
  Click "Undo" to reverse everything - files go back to exact original spots

✓ SYSTEM FOLDER PROTECTION
  Automatically skips: Windows, Program Files, AppData, System folders
  Won't touch important system files

✓ PREVIEW MODE
  See exactly what will happen before committing
  No surprises!

✓ SIZE FILTERING
  Skips files under 50 KB to avoid moving thumbnails, cache, icons

✓ ERROR HANDLING
  If a file can't be moved (in use, permission denied), it's skipped
  Other files continue processing
  Failed operations are logged and reported


❓ COMMON QUESTIONS & ANSWERS
═══════════════════════════════════════════════════════════════════════

Q: Which mode should I use?
A: • Use FIND SCATTERED FILES if: Photos/files are all over your PC
   • Use ORGANIZE FOLDER if: One folder is messy and needs sorting

Q: Will it delete my files?
A: NO! It only MOVES or COPIES them. Nothing is ever deleted.
   (Except empty folders if you check that option)

Q: What if I organize the wrong folder?
A: Click "Undo" button immediately! It reverses everything.
   The undo log is saved, so you can undo even days later.

Q: Can I organize my Pictures folder that already has some organized files?
A: YES! Point it at Pictures, click Organize. It will:
   • Find loose files and organize them
   • Skip files already in category folders
   • Create sub-folders (images/png/, images/jpg/)

Q: What happens to files already in an "images" folder?
A: If sub-folders are enabled, they get moved to images/png/, images/jpg/, etc.
   If disabled, they stay in images/

Q: Does "Find Scattered Files" delete the originals?
A: NO! It COPIES files. Your originals stay where they are.
   This is safer - you can delete originals manually after verifying.

Q: I have 10,000 photos - will this work?
A: YES! The tool handles large collections. It might take a few minutes,
   but it will process all files. Progress is shown in the results area.

Q: What file types are supported?
A: Images: jpg, jpeg, png, gif, bmp, webp, svg, ico, tiff
   Videos: mp4, avi, mkv, mov, wmv, flv, webm, m4v, mpg
   Documents: pdf, doc, docx, txt, rtf, xls, xlsx, ppt, pptx
   Audio: mp3, wav, flac, aac, ogg, m4a, wma
   Archives: zip, rar, 7z, tar, gz, bz2
   Installers: exe, msi
   Code: py, js, html, css, java, cpp, etc.

Q: Can I customize the file categories?
A: Not in the GUI yet, but you can edit config.py to add/change categories

Q: Where are the log files saved?
A: In the "logs" folder where this program is installed.
   Example: D:\File Organizer + Renamer\logs\

Q: Can I run this on an external hard drive?
A: YES! Just browse to the external drive folder when selecting.

Q: Will this work on Mac or Linux?
A: The code is cross-platform, but this version is optimized for Windows.
   It should work on Mac/Linux with minor adjustments.


💡 PRO TIPS
═══════════════════════════════════════════════════════════════════════

• START WITH PREVIEW - Always preview first to see what will happen

• BACKUP IMPORTANT FILES - While the tool is safe, backups are always smart

• USE DESCRIPTIVE FOLDER NAMES - When collecting files, create a clear
  destination like "C:\All My Photos" instead of "C:\New Folder"

• ORGANIZE REGULARLY - Don't let Downloads get to 5000 files!
  Run this weekly to stay organized

• CHECK UNDO LOGS - Look in the logs/ folder to see history of operations

• TRY SMALL FIRST - Test on a small folder before doing your entire PC

• CLOSE OTHER PROGRAMS - If files are "in use", close programs accessing them

• USE BOTH MODES - Collect scattered files first, then organize the result!


🆘 TROUBLESHOOTING
═══════════════════════════════════════════════════════════════════════

PROBLEM: "Permission denied" errors
SOLUTION: Run as Administrator, or move files from user folders only

PROBLEM: Some files not found in scan
SOLUTION: They might be in system folders (skipped for safety) or under 50 KB

PROBLEM: Undo doesn't work
SOLUTION: Check that log file still exists in logs/ folder

PROBLEM: Program is slow
SOLUTION: Normal for large folders. Let it run - it will finish!

PROBLEM: Can't see bottom buttons
SOLUTION: Maximize window or use scrollbar on the left side

PROBLEM: Files weren't organized
SOLUTION: Check Results area for error messages


═══════════════════════════════════════════════════════════════════════
Need more help? Check the README.md file in the program folder!
═══════════════════════════════════════════════════════════════════════
"""
        
        # Create help window
        help_window = tk.Toplevel(self.root)
        help_window.title("Help - File Organizer + Renamer")
        help_window.geometry("900x700")
        help_window.grab_set()  # Make modal so it stays on top
        
        # Unbind mousewheel from main window
        try:
            self.root.unbind_all("<MouseWheel>")
        except:
            pass
        
        # Scrolled text
        text_frame = tk.Frame(help_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text = tk.Text(text_frame, font=("Consolas", 9), wrap=tk.WORD, yscrollcommand=scrollbar.set)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text.yview)
        
        text.insert(1.0, help_text)
        text.config(state=tk.DISABLED)
        
        # Close button
        close_btn = tk.Button(
            help_window,
            text="Close",
            command=lambda: self.close_help(help_window),
            font=("Segoe UI", 11, "bold"),
            bg="#3498db",
            fg="white",
            padx=30,
            pady=10,
            cursor="hand2"
        )
        close_btn.pack(pady=10)
    
    def close_help(self, window):
        """Close help window and rebind mousewheel"""
        window.destroy()
        # Rebind mousewheel for collect tab scrolling
        self.bind_collect_scroll()
    
    def create_desktop_shortcut(self):
        """Create desktop shortcut for the app"""
        try:
            if sys.platform != 'win32':
                messagebox.showinfo("Not Supported", "Desktop shortcuts are only supported on Windows")
                return
            
            # Get paths
            script_dir = os.path.dirname(os.path.abspath(__file__))
            pyw_path = os.path.join(script_dir, "gui_unified.pyw")
            icon_path = os.path.join(script_dir, "icon.ico")
            
            # Get desktop path
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            shortcut_path = os.path.join(desktop, "File Organizer.lnk")
            
            # Remove old shortcut if exists
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)
            
            # Get pythonw.exe path
            pythonw_path = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
            
            # Create shortcut using PowerShell
            ps_script = f'''
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut("{shortcut_path}")
$shortcut.TargetPath = "{pythonw_path}"
$shortcut.Arguments = '"{pyw_path}"'
$shortcut.WorkingDirectory = "{script_dir}"
$shortcut.IconLocation = "{icon_path},0"
$shortcut.Save()
'''
            
            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                messagebox.showinfo("Success", "✓ Desktop shortcut created successfully!\n\nYou can now launch the app from your desktop.")
            else:
                messagebox.showerror("Error", f"Failed to create shortcut:\n{result.stderr}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error creating shortcut:\n{e}")
    
    def bind_collect_scroll(self):
        """Bind mousewheel scrolling to collect canvas"""
        if hasattr(self, 'collect_canvas'):
            def on_mousewheel(event):
                self.collect_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            self.root.bind_all("<MouseWheel>", on_mousewheel)
    
    def bind_organize_scroll(self):
        """Bind mousewheel scrolling to organize canvas"""
        if hasattr(self, 'organize_canvas'):
            def on_mousewheel(event):
                self.organize_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            self.root.bind_all("<MouseWheel>", on_mousewheel)
    
    def create_organize_tab(self):
        """Tab 1: Organize a single folder"""
        
        # Variables
        self.org_folder = tk.StringVar()
        self.org_subfolder_ext = tk.BooleanVar(value=True)
        self.org_recursive = tk.BooleanVar(value=True)
        self.org_clean_empty = tk.BooleanVar(value=True)
        self.org_use_date = tk.BooleanVar(value=False)
        self.org_date_style = tk.StringVar(value='year_month')
        self.org_find_dupes = tk.BooleanVar(value=False)
        self.org_min_size = tk.IntVar(value=0)
        self.org_max_size = tk.IntVar(value=0)
        
        # Create canvas with scrollbar (like collect tab)
        self.organize_canvas = tk.Canvas(self.tab_organize, highlightthickness=0, bg="#1e1e1e")
        scrollbar = tk.Scrollbar(self.tab_organize, orient="vertical", command=self.organize_canvas.yview, bg="#0d1117")
        scrollable_frame = tk.Frame(self.organize_canvas, bg="#1e1e1e")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: self.organize_canvas.configure(scrollregion=self.organize_canvas.bbox("all"))
        )
        
        canvas_frame = self.organize_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Make canvas content expand to fill width
        def on_canvas_configure(event):
            self.organize_canvas.itemconfig(canvas_frame, width=event.width)
        self.organize_canvas.bind("<Configure>", on_canvas_configure)
        
        self.organize_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Enable mousewheel scrolling using method
        self.bind_organize_scroll()
        
        self.organize_canvas.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        scrollbar.pack(side="right", fill="y", padx=(0, 20), pady=20)
        
        # All content goes in scrollable_frame now
        
        # Subtle hint
        hint = tk.Label(
            scrollable_frame,
            text="Select a folder to organize, choose options, then click Organize",
            font=("Segoe UI", 9),
            fg="#6e7681",
            bg="#1e1e1e"
        )
        hint.pack(pady=(0, 20))
        
        # Folder selection
        folder_frame = tk.LabelFrame(scrollable_frame, text="Select Folder", font=("Segoe UI", 9), padx=25, pady=18, bg="#161b22", fg="#8b949e")
        folder_frame.pack(fill=tk.X, pady=(0, 25))
        
        tk.Entry(folder_frame, textvariable=self.org_folder, font=("Segoe UI", 9), state="readonly", bg="#0d1117", fg="#c9d1d9", readonlybackground="#0d1117", insertbackground="#c9d1d9").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        tk.Button(folder_frame, text="Browse...", command=self.browse_organize_folder, font=("Segoe UI", 9), bg="#238636", fg="white", padx=15, pady=6, cursor="hand2", relief=tk.FLAT, borderwidth=0).pack(side=tk.RIGHT)
        
        # Options
        options_frame = tk.LabelFrame(scrollable_frame, text="Options", font=("Segoe UI", 9), padx=25, pady=18, bg="#161b22", fg="#8b949e")
        options_frame.pack(fill=tk.X, pady=(0, 12))
        
        tk.Checkbutton(options_frame, text="Create sub-folders by file type (images/png/, images/jpg/)", variable=self.org_subfolder_ext, font=("Segoe UI", 9), bg="#161b22", fg="#c9d1d9", selectcolor="#0d1117", activebackground="#161b22", activeforeground="#c9d1d9").pack(anchor=tk.W, pady=5)
        tk.Checkbutton(options_frame, text="Scan all subfolders recursively", variable=self.org_recursive, font=("Segoe UI", 9), bg="#161b22", fg="#c9d1d9", selectcolor="#0d1117", activebackground="#161b22", activeforeground="#c9d1d9").pack(anchor=tk.W, pady=5)
        tk.Checkbutton(options_frame, text="Delete empty folders after organizing", variable=self.org_clean_empty, font=("Segoe UI", 9), bg="#161b22", fg="#c9d1d9", selectcolor="#0d1117", activebackground="#161b22", activeforeground="#c9d1d9").pack(anchor=tk.W, pady=5)
        
        # Advanced Options
        advanced_frame = tk.LabelFrame(scrollable_frame, text="Advanced Options", font=("Segoe UI", 9), padx=25, pady=18, bg="#161b22", fg="#8b949e")
        advanced_frame.pack(fill=tk.X, pady=(0, 12))
        
        # Duplicate detection
        dup_cb = tk.Checkbutton(advanced_frame, text="Find duplicate files (compares file content)", variable=self.org_find_dupes, font=("Segoe UI", 9), bg="#161b22", fg="#c9d1d9", selectcolor="#0d1117", activebackground="#161b22", activeforeground="#c9d1d9")
        dup_cb.pack(anchor=tk.W, pady=5)
        
        # Date-based organization
        date_frame = tk.Frame(advanced_frame, bg="#161b22")
        date_frame.pack(anchor=tk.W, fill=tk.X, pady=5)
        tk.Checkbutton(date_frame, text="Organize by date:", variable=self.org_use_date, font=("Segoe UI", 9), bg="#161b22", fg="#c9d1d9", selectcolor="#0d1117", activebackground="#161b22", activeforeground="#c9d1d9").pack(side=tk.LEFT)
        date_combo = ttk.Combobox(date_frame, textvariable=self.org_date_style, values=['year_month', 'year_only', 'year_month_simple'], state="readonly", width=15, font=("Segoe UI", 8))
        date_combo.pack(side=tk.LEFT, padx=10)
        
        # Show Pillow status
        pillow_status = "✓ EXIF dates available" if DateOrganizer.is_pillow_available() else "ⓘ Uses file dates (pip install pillow for EXIF)"
        pillow_color = "#238636" if DateOrganizer.is_pillow_available() else "#8b949e"
        tk.Label(advanced_frame, text=pillow_status, font=("Segoe UI", 7), fg=pillow_color, bg="#161b22").pack(anchor=tk.W, padx=20)
        
        # Size filters
        tk.Label(advanced_frame, text="Size filters (0 = no limit):", font=("Segoe UI", 9), bg="#161b22", fg="#c9d1d9").pack(anchor=tk.W, pady=(8, 3))
        size_frame = tk.Frame(advanced_frame, bg="#161b22")
        size_frame.pack(anchor=tk.W, fill=tk.X)
        tk.Label(size_frame, text="Min (KB):", font=("Segoe UI", 8), bg="#161b22", fg="#8b949e").pack(side=tk.LEFT)
        tk.Entry(size_frame, textvariable=self.org_min_size, font=("Segoe UI", 8), width=8, bg="#0d1117", fg="#c9d1d9", insertbackground="#c9d1d9").pack(side=tk.LEFT, padx=5)
        tk.Label(size_frame, text="Max (KB):", font=("Segoe UI", 8), bg="#161b22", fg="#8b949e").pack(side=tk.LEFT, padx=(15, 0))
        tk.Entry(size_frame, textvariable=self.org_max_size, font=("Segoe UI", 8), width=8, bg="#0d1117", fg="#c9d1d9", insertbackground="#c9d1d9").pack(side=tk.LEFT, padx=5)
        
        # Action buttons
        btn_frame = tk.Frame(scrollable_frame, bg="#1e1e1e")
        btn_frame.pack(fill=tk.X, pady=(0, 25))
        
        tk.Button(btn_frame, text="Preview", command=self.organize_preview, font=("Segoe UI", 10), bg="#6e7681", fg="white", padx=20, pady=10, cursor="hand2", relief=tk.FLAT, borderwidth=0).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 6))
        tk.Button(btn_frame, text="Organize", command=self.organize_apply, font=("Segoe UI", 10), bg="#238636", fg="white", padx=20, pady=10, cursor="hand2", relief=tk.FLAT, borderwidth=0).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)
        tk.Button(btn_frame, text="Undo Last", command=self.organize_undo, font=("Segoe UI", 10), bg="#d29922", fg="white", padx=20, pady=10, cursor="hand2", relief=tk.FLAT, borderwidth=0).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(6, 0))
        
        # Manage Duplicates button (hidden until duplicates found) - appears in same row as other actions
        self.org_manage_dupes_btn = tk.Button(btn_frame, text="📁 Duplicates", command=self.open_duplicate_manager, font=("Segoe UI", 10, "bold"), bg="#da3633", fg="white", padx=20, pady=10, cursor="hand2", relief=tk.FLAT, borderwidth=0)
        
        # Progress bar area (centered above results)
        progress_container = tk.Frame(scrollable_frame, bg="#1e1e1e", height=50)
        progress_container.pack(fill=tk.X, pady=10)
        self.org_progress = ttk.Progressbar(progress_container, mode='indeterminate', length=400)
        
        # Results
        results_frame = tk.LabelFrame(scrollable_frame, text="Results", font=("Segoe UI", 9), padx=18, pady=15, bg="#161b22", fg="#8b949e")
        results_frame.pack(fill=tk.X, pady=(0, 25))
        
        # Results header with fullscreen button
        results_header = tk.Frame(results_frame, bg="#161b22")
        results_header.pack(fill=tk.X, pady=(0, 8))
        tk.Button(results_header, text="🔍 Full Screen", command=lambda: self.show_fullscreen_results('organize'), font=("Segoe UI", 8), bg="#0969da", fg="white", padx=10, pady=4, cursor="hand2", relief=tk.FLAT, borderwidth=0).pack(side=tk.RIGHT)
        
        self.org_results = tk.Text(results_frame, font=("Consolas", 8), wrap=tk.WORD, height=5, bg="#0d1117", fg="#c9d1d9", insertbackground="#c9d1d9")
        self.org_results.pack(fill=tk.X)
    
    def create_collect_tab(self):
        """Tab 2: Collect files from across PC"""
        
        # Variables
        self.collect_dest = tk.StringVar()
        self.collect_images = tk.BooleanVar(value=True)
        self.collect_videos = tk.BooleanVar(value=False)
        self.collect_documents = tk.BooleanVar(value=False)
        self.collect_audio = tk.BooleanVar(value=False)
        self.collect_archives = tk.BooleanVar(value=False)
        self.collect_org_style = tk.StringVar(value="by_extension")
        self.collect_use_date = tk.BooleanVar(value=False)
        self.collect_date_style = tk.StringVar(value='year_month')
        self.collect_find_dupes = tk.BooleanVar(value=False)
        self.collect_min_size = tk.IntVar(value=50)  # 50 KB default
        self.collect_max_size = tk.IntVar(value=0)   # 0 = no limit
        
        # Create canvas with scrollbar
        self.collect_canvas = tk.Canvas(self.tab_collect, highlightthickness=0, bg="#1e1e1e")
        scrollbar = tk.Scrollbar(self.tab_collect, orient="vertical", command=self.collect_canvas.yview, bg="#0d1117")
        scrollable_frame = tk.Frame(self.collect_canvas, bg="#1e1e1e")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: self.collect_canvas.configure(scrollregion=self.collect_canvas.bbox("all"))
        )
        
        canvas_frame = self.collect_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Make canvas content expand to fill width
        def on_canvas_configure(event):
            self.collect_canvas.itemconfig(canvas_frame, width=event.width)
        self.collect_canvas.bind("<Configure>", on_canvas_configure)
        
        self.collect_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Enable mousewheel scrolling using method
        self.bind_collect_scroll()
        
        self.collect_canvas.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        scrollbar.pack(side="right", fill="y", padx=(0, 20), pady=20)
        
        # All content goes in scrollable_frame now
        
        # Subtle hint
        hint = tk.Label(
            scrollable_frame,
            text="Check file types to find, scan your PC, choose destination, then collect",
            font=("Segoe UI", 8),
            fg="#6e7681",
            bg="#1e1e1e"
        )
        hint.pack(pady=(0, 10))
        
        # File type selection
        step1 = tk.LabelFrame(scrollable_frame, text="File Types", font=("Segoe UI", 9), padx=15, pady=10, bg="#161b22", fg="#8b949e")
        step1.pack(fill=tk.X, pady=(0, 12))
        
        tk.Checkbutton(step1, text="Images (jpg, png, gif, etc.)", variable=self.collect_images, font=("Segoe UI", 9), bg="#161b22", fg="#c9d1d9", selectcolor="#0d1117", activebackground="#161b22", activeforeground="#c9d1d9").pack(anchor=tk.W, pady=2)
        tk.Checkbutton(step1, text="Videos (mp4, avi, mkv, etc.)", variable=self.collect_videos, font=("Segoe UI", 9), bg="#161b22", fg="#c9d1d9", selectcolor="#0d1117", activebackground="#161b22", activeforeground="#c9d1d9").pack(anchor=tk.W, pady=2)
        tk.Checkbutton(step1, text="Documents (pdf, docx, txt, etc.)", variable=self.collect_documents, font=("Segoe UI", 9), bg="#161b22", fg="#c9d1d9", selectcolor="#0d1117", activebackground="#161b22", activeforeground="#c9d1d9").pack(anchor=tk.W, pady=2)
        tk.Checkbutton(step1, text="Audio (mp3, wav, flac, etc.)", variable=self.collect_audio, font=("Segoe UI", 9), bg="#161b22", fg="#c9d1d9", selectcolor="#0d1117", activebackground="#161b22", activeforeground="#c9d1d9").pack(anchor=tk.W, pady=2)
        tk.Checkbutton(step1, text="Archives (zip, rar, 7z, etc.)", variable=self.collect_archives, font=("Segoe UI", 9), bg="#161b22", fg="#c9d1d9", selectcolor="#0d1117", activebackground="#161b22", activeforeground="#c9d1d9").pack(anchor=tk.W, pady=2)
        
        tk.Label(step1, text="Searches: Desktop, Downloads, Documents, Videos, Music", font=("Segoe UI", 8), fg="#6e7681", bg="#161b22", justify=tk.LEFT).pack(anchor=tk.W, pady=(8, 0))
        
        # Advanced options for collect
        adv_collect = tk.LabelFrame(scrollable_frame, text="Advanced Scan Options", font=("Segoe UI", 9), padx=15, pady=10, bg="#161b22", fg="#8b949e")
        adv_collect.pack(fill=tk.X, pady=(0, 12))
        
        # Size filters
        tk.Label(adv_collect, text="Size filters (KB, 0 = no limit):", font=("Segoe UI", 9), bg="#161b22", fg="#c9d1d9").pack(anchor=tk.W, pady=(0, 3))
        size_frame = tk.Frame(adv_collect, bg="#161b22")
        size_frame.pack(anchor=tk.W, fill=tk.X, pady=3)
        tk.Label(size_frame, text="Min:", font=("Segoe UI", 8), bg="#161b22", fg="#8b949e").pack(side=tk.LEFT)
        tk.Entry(size_frame, textvariable=self.collect_min_size, font=("Segoe UI", 8), width=8, bg="#0d1117", fg="#c9d1d9", insertbackground="#c9d1d9").pack(side=tk.LEFT, padx=5)
        tk.Label(size_frame, text="Max:", font=("Segoe UI", 8), bg="#161b22", fg="#8b949e").pack(side=tk.LEFT, padx=(15, 0))
        tk.Entry(size_frame, textvariable=self.collect_max_size, font=("Segoe UI", 8), width=8, bg="#0d1117", fg="#c9d1d9", insertbackground="#c9d1d9").pack(side=tk.LEFT, padx=5)
        
        # Duplicate detection
        tk.Checkbutton(adv_collect, text="Find duplicates during scan", variable=self.collect_find_dupes, font=("Segoe UI", 9), bg="#161b22", fg="#c9d1d9", selectcolor="#0d1117", activebackground="#161b22", activeforeground="#c9d1d9").pack(anchor=tk.W, pady=5)
        
        # Scan button
        scan_btn_frame = tk.Frame(scrollable_frame, bg="#1e1e1e")
        scan_btn_frame.pack(fill=tk.X, pady=(0, 12))
        
        tk.Button(scan_btn_frame, text="Scan for Files", command=self.collect_scan, font=("Segoe UI", 10), bg="#238636", fg="white", padx=25, pady=10, cursor="hand2", relief=tk.FLAT, borderwidth=0).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 6))
        
        # Manage Duplicates button (hidden until duplicates found) - appears next to Scan button
        self.manage_dupes_btn = tk.Button(scan_btn_frame, text="📁 Duplicates", command=self.open_duplicate_manager, font=("Segoe UI", 10, "bold"), bg="#da3633", fg="white", padx=25, pady=10, cursor="hand2", relief=tk.FLAT, borderwidth=0)
        
        # Progress bar area (centered above results)
        progress_container_collect = tk.Frame(scrollable_frame, bg="#1e1e1e", height=50)
        progress_container_collect.pack(fill=tk.X, pady=10)
        self.collect_progress = ttk.Progressbar(progress_container_collect, mode='indeterminate', length=400)
        
        # Results
        results_frame = tk.LabelFrame(scrollable_frame, text="Results", font=("Segoe UI", 9), padx=12, pady=8, bg="#161b22", fg="#8b949e")
        results_frame.pack(fill=tk.X, pady=(0, 12))
        
        # Results header with fullscreen button
        results_header_collect = tk.Frame(results_frame, bg="#161b22")
        results_header_collect.pack(fill=tk.X, pady=(0, 8))
        tk.Button(results_header_collect, text="🔍 Full Screen", command=lambda: self.show_fullscreen_results('collect'), font=("Segoe UI", 8), bg="#0969da", fg="white", padx=10, pady=4, cursor="hand2", relief=tk.FLAT, borderwidth=0).pack(side=tk.RIGHT)
        
        self.collect_results = tk.Text(results_frame, font=("Consolas", 8), height=4, wrap=tk.WORD, bg="#0d1117", fg="#c9d1d9", insertbackground="#c9d1d9")
        self.collect_results.pack(fill=tk.X)
        
        # Destination
        step2 = tk.LabelFrame(scrollable_frame, text="Destination", font=("Segoe UI", 9), padx=15, pady=10, bg="#161b22", fg="#8b949e")
        step2.pack(fill=tk.X, pady=(0, 12))
        
        dest_frame = tk.Frame(step2, bg="#161b22")
        dest_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Entry(dest_frame, textvariable=self.collect_dest, font=("Segoe UI", 9), state="readonly", bg="#0d1117", fg="#c9d1d9", readonlybackground="#0d1117", insertbackground="#c9d1d9").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        tk.Button(dest_frame, text="Browse...", command=self.browse_collect_dest, font=("Segoe UI", 9), bg="#238636", fg="white", padx=15, pady=6, cursor="hand2", relief=tk.FLAT, borderwidth=0).pack(side=tk.RIGHT)
        
        tk.Label(step2, text="Organization style:", font=("Segoe UI", 9), bg="#161b22", fg="#c9d1d9").pack(anchor=tk.W, pady=(0, 6))
        tk.Radiobutton(step2, text="By file type (images/png/, images/jpg/)", variable=self.collect_org_style, value="by_extension", font=("Segoe UI", 9), bg="#161b22", fg="#c9d1d9", selectcolor="#0d1117", activebackground="#161b22", activeforeground="#c9d1d9").pack(anchor=tk.W, padx=15, pady=2)
        tk.Radiobutton(step2, text="By category only (images/, videos/)", variable=self.collect_org_style, value="by_category", font=("Segoe UI", 9), bg="#161b22", fg="#c9d1d9", selectcolor="#0d1117", activebackground="#161b22", activeforeground="#c9d1d9").pack(anchor=tk.W, padx=15, pady=2)
        tk.Radiobutton(step2, text="By source folder (from_desktop/, from_downloads/)", variable=self.collect_org_style, value="by_source", font=("Segoe UI", 9), bg="#161b22", fg="#c9d1d9", selectcolor="#0d1117", activebackground="#161b22", activeforeground="#c9d1d9").pack(anchor=tk.W, padx=15, pady=2)
        
        # Date organization option
        date_frame2 = tk.Frame(step2, bg="#161b22")
        date_frame2.pack(anchor=tk.W, fill=tk.X, pady=(8, 0))
        tk.Checkbutton(date_frame2, text="Also organize by date:", variable=self.collect_use_date, font=("Segoe UI", 9), bg="#161b22", fg="#c9d1d9", selectcolor="#0d1117", activebackground="#161b22", activeforeground="#c9d1d9").pack(side=tk.LEFT)
        date_combo2 = ttk.Combobox(date_frame2, textvariable=self.collect_date_style, values=['year_month', 'year_only', 'year_month_simple'], state="readonly", width=15, font=("Segoe UI", 8))
        date_combo2.pack(side=tk.LEFT, padx=10)
        
        tk.Button(step2, text="Collect Files", command=self.collect_files, font=("Segoe UI", 10), bg="#238636", fg="white", padx=25, pady=10, cursor="hand2", relief=tk.FLAT, borderwidth=0).pack(pady=(10, 0))
    
    # ORGANIZE TAB FUNCTIONS
    
    def browse_organize_folder(self):
        folder = filedialog.askdirectory(title="Choose Folder to Organize")
        if folder:
            self.org_folder.set(folder)
            self.status.config(text=f"Ready to organize: {folder}")
    
    def org_log(self, msg):
        self.org_results.insert(tk.END, msg + "\n")
        self.org_results.see(tk.END)
        self.root.update()
    
    def org_clear(self):
        self.org_results.delete(1.0, tk.END)
    
    def organize_preview(self):
        folder = self.org_folder.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showwarning("No Folder", "Please select a valid folder first!")
            return
        
        self.org_clear()
        self.org_log("=" * 70)
        self.org_log("PREVIEW MODE - No changes will be made")
        self.org_log("=" * 70)
        
        # Show progress bar
        self.org_progress.pack(expand=True)
        self.org_progress.start(10)
        
        # Run in background thread to prevent GUI freeze
        def preview_thread():
            try:
                # Check for duplicates first if enabled
                if self.org_find_dupes.get():
                    self.org_log("\nScanning for duplicates...")
                    min_size = self.org_min_size.get() * 1024  # Convert KB to bytes
                    detector = DuplicateDetector(min_file_size=min_size)
                    duplicates = detector.scan_for_duplicates(
                        folder, 
                        recursive=self.org_recursive.get(),
                        progress_callback=lambda m: self.org_log(f"  {m}")
                    )
                    
                    if duplicates:
                        # Store for duplicate manager
                        dup_groups = {}
                        for group in duplicates:
                            # Use file size as key, store list of paths
                            if group.file_size not in dup_groups:
                                dup_groups[group.file_size] = []
                            dup_groups[group.file_size].extend(group.file_paths)
                        self.org_duplicate_groups = dup_groups
                        
                        summary = detector.get_summary()
                        self.org_log(f"\n⚠️  Found {summary['duplicate_groups']} duplicate groups:")
                        for i, group in enumerate(duplicates[:10], 1):
                            self.org_log(f"\n  Group {i}: {len(group.file_paths)} identical files ({self.format_size(group.file_size)} each)")
                            for fp in group.file_paths[:3]:
                                self.org_log(f"    - {os.path.basename(fp)}")
                            if len(group.file_paths) > 3:
                                self.org_log(f"    ... and {len(group.file_paths) - 3} more")
                        
                        if len(duplicates) > 10:
                            self.org_log(f"\n  ... and {len(duplicates) - 10} more groups")
                        
                        wasted = summary['total_wasted_space']
                        self.org_log(f"\n  Wasted space: {self.format_size(wasted)}")
                        
                        # Show Manage Duplicates button in action row
                        self.org_manage_dupes_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(6, 0))
                    else:
                        self.org_duplicate_groups = {}
                        self.org_manage_dupes_btn.pack_forget()
                        self.org_log("\n✓ No duplicates found!")
                
                organizer = FileOrganizer(
                    folder,
                    add_date_prefix=False,
                    recursive=self.org_recursive.get(),
                    sub_folders_by_extension=self.org_subfolder_ext.get()
                )
                
                operations = organizer.plan_operations()
                
                # Apply size filters
                min_size_kb = self.org_min_size.get()
                max_size_kb = self.org_max_size.get()
                if min_size_kb > 0 or max_size_kb > 0:
                    filtered_ops = []
                    for op in operations:
                        try:
                            size_kb = os.path.getsize(op.source_path) / 1024
                            if min_size_kb > 0 and size_kb < min_size_kb:
                                continue
                            if max_size_kb > 0 and size_kb > max_size_kb:
                                continue
                            filtered_ops.append(op)
                        except:
                            filtered_ops.append(op)  # Keep if size check fails
                    operations = filtered_ops
                    self.org_log(f"\n✓ Size filter applied: {len(operations)} files match")
                
                if not operations:
                    self.org_log("\nNo files found to organize.")
                    self.org_progress.stop()
                    self.org_progress.pack_forget()
                    return
                
                summary = organizer.get_preview_summary()
                self.org_log(f"\nTotal files to organize: {len(operations)}")
                self.org_log(f"\nFiles by category:")
                for category, count in summary['categories'].items():
                    self.org_log(f"  {category}: {count}")
                
                self.org_log("\nFirst 15 operations:")
                for i, op in enumerate(operations[:15], 1):
                    self.org_log(f"\n{i}. [{op.category}]")
                    self.org_log(f"   FROM: {os.path.basename(op.source_path)}")
                    self.org_log(f"   TO: {os.path.relpath(op.target_path, folder)}")
                
                if len(operations) > 15:
                    self.org_log(f"\n... and {len(operations) - 15} more files")
                
                self.org_log("\n" + "=" * 70)
                self.status.config(text=f"Preview: {len(operations)} files ready")
                
            except Exception as e:
                self.org_log(f"\n✗ Error: {e}")
                self.status.config(text="Error during preview")
            finally:
                self.org_progress.stop()
                self.org_progress.pack_forget()
        
        Thread(target=preview_thread, daemon=True).start()
    
    def organize_apply(self):
        folder = self.org_folder.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showwarning("No Folder", "Please select a valid folder first!")
            return
        
        if not messagebox.askyesno("Confirm", "This will move and rename files!\n\nContinue?"):
            return
        
        self.org_clear()
        self.org_log("=" * 70)
        self.org_log("ORGANIZING FILES...")
        self.org_log("=" * 70)
        
        try:
            organizer = FileOrganizer(
                folder,
                add_date_prefix=False,
                recursive=self.org_recursive.get(),
                sub_folders_by_extension=self.org_subfolder_ext.get()
            )
            
            operations = organizer.plan_operations()
            if not operations:
                self.org_log("\nNo files found.")
                return
            
            successful, failed = organizer.execute_operations()
            
            deleted_folders = []
            if self.org_clean_empty.get():
                summary = organizer.get_preview_summary()
                protected = list(summary['categories'].keys())
                deleted_folders = cleanup_empty_folders(folder, protected)
            
            logger = OperationLogger()
            log_file = logger.log_operations(successful + failed)
            
            self.org_log(f"\n✓ Successful: {len(successful)}")
            self.org_log(f"✗ Failed: {len(failed)}")
            if deleted_folders:
                self.org_log(f"🗑️  Empty folders deleted: {len(deleted_folders)}")
            self.org_log(f"📝 Log: {log_file}")
            
            self.status.config(text=f"✓ Organized {len(successful)} files!")
            messagebox.showinfo("Done!", f"Organized {len(successful)} files!")
            
        except Exception as e:
            self.org_log(f"\n✗ Error: {e}")
            messagebox.showerror("Error", str(e))
    
    def organize_undo(self):
        if not messagebox.askyesno("Undo?", "Restore files to original locations?"):
            return
        
        try:
            logger = OperationLogger()
            log_file = logger.get_latest_log()
            
            if not log_file:
                messagebox.showwarning("No Logs", "Nothing to undo!")
                return
            
            self.org_clear()
            self.org_log("Undoing last operation...")
            
            successful, failed = logger.undo_operations(log_file)
            
            self.org_log(f"\n✓ Restored: {len(successful)}")
            self.org_log(f"✗ Failed: {len(failed)}")
            
            messagebox.showinfo("Done!", f"Restored {len(successful)} files!")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    # COLLECT TAB FUNCTIONS
    
    def collect_log(self, msg):
        self.collect_results.insert(tk.END, msg + "\n")
        self.collect_results.see(tk.END)
        self.root.update()
    
    def collect_clear(self):
        self.collect_results.delete(1.0, tk.END)
    
    def get_collect_types(self):
        types = []
        if self.collect_images.get(): types.append('images')
        if self.collect_videos.get(): types.append('videos')
        if self.collect_documents.get(): types.append('documents')
        if self.collect_audio.get(): types.append('audio')
        if self.collect_archives.get(): types.append('archives')
        return types
    
    def collect_scan(self):
        types = self.get_collect_types()
        if not types:
            messagebox.showwarning("Nothing Selected", "Please select at least one file type!")
            return
        
        self.collect_clear()
        self.status.config(text="⏳ Scanning...")
        
        # Show progress bar
        self.collect_progress.pack(pady=10)
        self.collect_progress.start(10)
        
        def scan_thread():
            try:
                # Update collector min size from user input
                min_size_kb = self.collect_min_size.get()
                self.collector.min_file_size = max(min_size_kb * 1024, 0)
                
                self.collect_log(f"Scanning for: {', '.join(types)}...")
                self.collect_log(f"Size filter: Min {min_size_kb} KB" + (f", Max {self.collect_max_size.get()} KB" if self.collect_max_size.get() > 0 else ""))
                self.collect_log("")
                
                # Perform scan
                self.scan_results = self.collector.scan(file_types=types, progress_callback=lambda m: self.collect_log(m))
                
                # Apply max size filter if set
                max_size_kb = self.collect_max_size.get()
                if max_size_kb > 0:
                    max_size_bytes = max_size_kb * 1024
                    original_count = len(self.collector.found_files)
                    self.collector.found_files = [f for f in self.collector.found_files if f.size <= max_size_bytes]
                    filtered_count = original_count - len(self.collector.found_files)
                    if filtered_count > 0:
                        self.collect_log(f"✓ Filtered out {filtered_count} files over {max_size_kb} KB")
                
                summary = self.collector.get_summary()
                
                self.collect_log("")
                self.collect_log(f"✓ Found {summary['total']} files")
                
                if summary['total'] > 0:
                    for cat, count in summary['by_category'].items():
                        self.collect_log(f"  {cat}: {count}")
                    
                    # Check for duplicates if enabled
                    if self.collect_find_dupes.get():
                        self.collect_log("\nScanning for duplicates...")
                        # Create temp list of paths for duplicate detection
                        from duplicate_detector import DuplicateDetector
                        # We need to scan the actual found files for duplicates
                        # This is a simplified check - just count files by size
                        size_groups = {}
                        for f in self.collector.found_files:
                            if f.size not in size_groups:
                                size_groups[f.size] = []
                            size_groups[f.size].append(f.path)
                        
                        # Filter to only groups with duplicates
                        duplicate_groups = {size: paths for size, paths in size_groups.items() if len(paths) > 1}
                        potential_dupes = sum(len(paths) for paths in duplicate_groups.values())
                        
                        if potential_dupes > 0:
                            # Store for duplicate manager
                            self.duplicate_groups = duplicate_groups
                            
                            self.collect_log(f"⚠️  Found {potential_dupes} {'file' if potential_dupes == 1 else 'files'} with matching sizes (potential duplicates)")
                            self.collect_log(f"   {len(duplicate_groups)} duplicate group(s):")
                            
                            # Show first 5 groups
                            for i, (size, paths) in enumerate(list(duplicate_groups.items())[:5], 1):
                                self.collect_log(f"\n   Group {i}: {len(paths)} files ({self.format_size(size)} each)")
                                for path in paths[:5]:  # Show first 5 files per group
                                    self.collect_log(f"      • {os.path.basename(path)}")
                                    self.collect_log(f"        {os.path.dirname(path)}")
                                if len(paths) > 5:
                                    self.collect_log(f"      ... and {len(paths) - 5} more")
                            
                            if len(duplicate_groups) > 5:
                                self.collect_log(f"\n   ... and {len(duplicate_groups) - 5} more groups")
                            
                            # Show Manage Duplicates button next to Scan
                            self.manage_dupes_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(6, 0))
                        else:
                            self.duplicate_groups = {}
                            self.manage_dupes_btn.pack_forget()
                            self.collect_log("✓ No duplicate file sizes found")
                    
                    self.status.config(text=f"✓ Found {summary['total']} files - choose destination")
                else:
                    self.status.config(text="No files found")
                    
            except Exception as e:
                self.collect_log(f"✗ Error: {e}")
                self.status.config(text="Error during scan")
            finally:
                self.collect_progress.stop()
                self.collect_progress.pack_forget()
        
        Thread(target=scan_thread, daemon=True).start()
    
    def browse_collect_dest(self):
        folder = filedialog.askdirectory(title="Choose Where to Collect Files")
        if folder:
            self.collect_dest.set(folder)
            self.status.config(text=f"Will collect to: {folder}")
    
    def format_size(self, size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    def collect_files(self):
        summary = self.collector.get_summary()
        if summary['total'] == 0:
            messagebox.showwarning("No Files", "Please scan first!")
            return
        
        dest = self.collect_dest.get()
        if not dest:
            messagebox.showwarning("No Destination", "Please choose destination!")
            return
        
        if not messagebox.askyesno("Confirm", f"Collect {summary['total']} files to:\n{dest}\n\nContinue?"):
            return
        
        self.status.config(text="⏳ Collecting files...")
        self.collect_clear()
        
        # Show progress bar
        self.collect_progress.pack(expand=True)
        self.collect_progress.start(10)
        
        def collect_thread():
            try:
                self.collect_log("Collecting files...")
                
                successful = 0
                failed = 0
                org_style = self.collect_org_style.get()
                use_date_org = self.collect_use_date.get()
                date_style = self.collect_date_style.get()
                
                total = len(self.collector.found_files)
                
                for idx, found_file in enumerate(self.collector.found_files, 1):
                    try:
                        # Determine base directory based on organization style
                        if org_style == "by_extension":
                            base_dir = os.path.join(dest, found_file.category, found_file.extension)
                        elif org_style == "by_category":
                            base_dir = os.path.join(dest, found_file.category)
                        else:  # by_source
                            base_dir = os.path.join(dest, f"from_{found_file.source_folder.lower()}")
                        
                        # Add date folder if enabled
                        if use_date_org:
                            file_date = DateOrganizer.get_file_date(found_file.path, use_exif=True)
                            if file_date:
                                target_dir = DateOrganizer.get_date_folder_path(base_dir, file_date, date_style)
                            else:
                                target_dir = base_dir
                        else:
                            target_dir = base_dir
                        
                        os.makedirs(target_dir, exist_ok=True)
                        
                        filename = os.path.basename(found_file.path)
                        
                        # Safe copy with conflict resolution
                        result = copy_file_safe(found_file.path, target_dir, filename)
                        if result:
                            successful += 1
                        else:
                            failed += 1
                        
                        # Progress update every 50 files
                        if idx % 50 == 0:
                            self.collect_log(f"  Progress: {idx}/{total} files...")
                        
                    except Exception:
                        failed += 1
                
                self.collect_log("")
                self.collect_log(f"✓ Collected: {successful}")
                self.collect_log(f"✗ Failed: {failed}")
                
                self.status.config(text=f"✓ Collected {successful} files!")
                messagebox.showinfo("Done!", f"Collected {successful} files!")
                
            except Exception as e:
                self.collect_log(f"✗ Error: {e}")
                messagebox.showerror("Error", str(e))
            finally:
                self.collect_progress.stop()
                self.collect_progress.pack_forget()
        
        Thread(target=collect_thread, daemon=True).start()
    
    def open_duplicate_manager(self):
        """Open duplicate manager window"""
        # Check both collect and organize duplicate groups
        dup_groups = self.duplicate_groups if self.duplicate_groups else self.org_duplicate_groups
        
        if not dup_groups:
            messagebox.showinfo("No Duplicates", "No duplicates to manage!")
            return
        
        # Create manager window
        manager = tk.Toplevel(self.root)
        manager.title("Manage Duplicates")
        manager.geometry("1100x750")
        manager.state('zoomed')  # Start maximized
        manager.configure(bg="#1e1e1e")
        
        # Title bar
        title_bar = tk.Frame(manager, bg="#0d1117")
        title_bar.pack(fill=tk.X)
        
        title = tk.Label(title_bar, text="Duplicate Manager", font=("Segoe UI", 18, "bold"), bg="#0d1117", fg="#c9d1d9", pady=20, padx=30)
        title.pack(side=tk.LEFT)
        
        # Instructions - Clear message box
        inst_frame = tk.Frame(manager, bg="#161b22", padx=30, pady=15)
        inst_frame.pack(fill=tk.X, padx=30, pady=(20, 0))
        
        # Icon
        tk.Label(inst_frame, text="ℹ️", font=("Segoe UI", 16), bg="#161b22", fg="#58a6ff").pack(side=tk.LEFT, padx=(0, 15))
        
        # Text container
        text_container = tk.Frame(inst_frame, bg="#161b22")
        text_container.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Label(text_container, text="How to Use This Page:", font=("Segoe UI", 10, "bold"), bg="#161b22", fg="#c9d1d9", anchor=tk.W).pack(anchor=tk.W)
        tk.Label(text_container, text="1. The NEWEST file in each group is automatically kept (green box) - you can't delete it", 
                 font=("Segoe UI", 9), bg="#161b22", fg="#8b949e", anchor=tk.W).pack(anchor=tk.W, pady=(3, 0))
        tk.Label(text_container, text="2. Check the boxes next to OLDER duplicates you want to DELETE (not the ones to keep!)", 
                 font=("Segoe UI", 9), bg="#161b22", fg="#8b949e", anchor=tk.W).pack(anchor=tk.W)
        tk.Label(text_container, text="3. Click 'Delete Selected' to send checked files to Recycle Bin (safe & reversible)", 
                 font=("Segoe UI", 9), bg="#161b22", fg="#8b949e", anchor=tk.W).pack(anchor=tk.W)
        tk.Label(text_container, text="💡 Tip: Click 'Visual Review' to see images side-by-side before deleting", 
                 font=("Segoe UI", 9, "italic"), bg="#161b22", fg="#58a6ff", anchor=tk.W).pack(anchor=tk.W, pady=(3, 0))
        
        # Scrollable frame
        canvas = tk.Canvas(manager, bg="#1e1e1e", highlightthickness=0)
        scrollbar = tk.Scrollbar(manager, orient="vertical", command=canvas.yview, bg="#0d1117")
        content = tk.Frame(canvas, bg="#1e1e1e")
        
        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=30, pady=20)
        scrollbar.pack(side="right", fill="y", pady=20, padx=(0, 10))
        
        # Enable mousewheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        manager.bind_all("<MouseWheel>", on_mousewheel)
        
        # Store checkboxes
        checkboxes = []
        
        # Display each duplicate group
        for i, (size, paths) in enumerate(dup_groups.items(), 1):
            # Sort by modification time (newest first)
            paths_with_time = [(p, os.path.getmtime(p)) for p in paths]
            paths_with_time.sort(key=lambda x: x[1], reverse=True)
            
            # Group container
            group_container = tk.Frame(content, bg="#161b22", padx=20, pady=15)
            group_container.pack(fill=tk.X, pady=(0, 20))
            
            # Store checkboxes for this group
            group_checkboxes = []
            
            # Group header
            header = tk.Frame(group_container, bg="#161b22")
            header.pack(fill=tk.X, pady=(0, 15))
            
            tk.Label(header, text=f"Group {i}", font=("Segoe UI", 11, "bold"), bg="#161b22", fg="#c9d1d9").pack(side=tk.LEFT)
            tk.Label(header, text=f"{len(paths)} files  •  {self.format_size(size)} each", font=("Segoe UI", 9), bg="#161b22", fg="#8b949e").pack(side=tk.LEFT, padx=(10, 0))
            
            # KEEP: Newest file (first in sorted list)
            keep_path, keep_time = paths_with_time[0]
            keep_frame = tk.Frame(group_container, bg="#1a4d2e", padx=15, pady=10)
            keep_frame.pack(fill=tk.X, pady=(0, 12))
            
            # Top row: KEEP label, filename, modified date
            keep_top = tk.Frame(keep_frame, bg="#1a4d2e")
            keep_top.pack(fill=tk.X)
            tk.Label(keep_top, text="✓ KEEP", font=("Segoe UI", 9, "bold"), bg="#1a4d2e", fg="#4fc97b").pack(side=tk.LEFT, padx=(0, 15))
            tk.Label(keep_top, text=os.path.basename(keep_path), font=("Segoe UI", 9, "bold"), bg="#1a4d2e", fg="white").pack(side=tk.LEFT, fill=tk.X, expand=True)
            tk.Label(keep_top, text=f"{self.format_time(keep_time)}", font=("Segoe UI", 8), bg="#1a4d2e", fg="#b3d9c5").pack(side=tk.RIGHT)
            
            # Bottom row: Full path
            tk.Label(keep_frame, text=os.path.dirname(keep_path), font=("Segoe UI", 8), bg="#1a4d2e", fg="#8bc4a3").pack(anchor=tk.W, pady=(5, 0))
            
            # DUPLICATES: Other files (rest of sorted list)
            if len(paths_with_time) > 1:
                dup_header = tk.Frame(group_container, bg="#161b22")
                dup_header.pack(fill=tk.X, pady=(0, 8))
                
                tk.Label(dup_header, text=f"Duplicates ({len(paths_with_time) - 1})", font=("Segoe UI", 9, "bold"), bg="#161b22", fg="#c9d1d9").pack(side=tk.LEFT)
                
                # Select All button for this group (needs to capture group_checkboxes correctly)
                def make_select_group_func(group_cbs):
                    def select_group():
                        for var, _ in group_cbs:
                            var.set(True)
                    return select_group
                
                select_group_btn = tk.Button(dup_header, text="☑ Select All Here", 
                                            command=make_select_group_func(group_checkboxes),
                                            font=("Segoe UI", 8), bg="#238636", fg="white", padx=10, pady=4, cursor="hand2", relief=tk.FLAT, borderwidth=0)
                select_group_btn.pack(side=tk.RIGHT, padx=(0, 5))
                
                # Move to Review Folder button
                review_btn = tk.Button(dup_header, text="📁 Visual Review", 
                                      command=lambda paths=paths_with_time, grp=i: self.move_group_to_review(paths, grp, manager),
                                      font=("Segoe UI", 8), bg="#0969da", fg="white", padx=12, pady=5, cursor="hand2", relief=tk.FLAT, borderwidth=0)
                review_btn.pack(side=tk.RIGHT)
                
                for dup_path, dup_time in paths_with_time[1:]:
                    dup_frame = tk.Frame(group_container, bg="#0d1117", padx=12, pady=8)
                    dup_frame.pack(fill=tk.X, pady=3)
                    
                    # Top row: Checkbox, filename, modified date
                    dup_top = tk.Frame(dup_frame, bg="#0d1117")
                    dup_top.pack(fill=tk.X)
                    
                    var = tk.BooleanVar(value=False)
                    cb = tk.Checkbutton(dup_top, variable=var, font=("Segoe UI", 9), bg="#0d1117", fg="#c9d1d9", selectcolor="#0d1117", activebackground="#0d1117", cursor="hand2")
                    cb.pack(side=tk.LEFT, padx=(0, 8))
                    
                    tk.Label(dup_top, text=os.path.basename(dup_path), font=("Segoe UI", 9), bg="#0d1117", fg="#c9d1d9").pack(side=tk.LEFT, fill=tk.X, expand=True)
                    tk.Label(dup_top, text=self.format_time(dup_time), font=("Segoe UI", 8), bg="#0d1117", fg="#6e7681").pack(side=tk.RIGHT)
                    
                    # Bottom row: Full path
                    tk.Label(dup_frame, text=os.path.dirname(dup_path), font=("Segoe UI", 8), bg="#0d1117", fg="#484f58").pack(anchor=tk.W, padx=(28, 0), pady=(4, 0))
                    
                    checkboxes.append((var, dup_path))
                    group_checkboxes.append((var, dup_path))
        
        # Button frame
        btn_frame = tk.Frame(manager, bg="#0d1117", pady=18)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        btn_inner = tk.Frame(btn_frame, bg="#0d1117")
        btn_inner.pack(padx=30)
        
        def select_all():
            for var, _ in checkboxes:
                var.set(True)
        
        def select_none():
            for var, _ in checkboxes:
                var.set(False)
        
        def delete_selected():
            selected = [path for var, path in checkboxes if var.get()]
            if not selected:
                messagebox.showwarning("Nothing Selected", "Please select files to delete!")
                return
            
            if not messagebox.askyesno("Confirm Delete", f"Move {len(selected)} files to Recycle Bin?\n\nThis action can be undone from the Recycle Bin."):
                return
            
            try:
                deleted = 0
                failed = 0
                
                for path in selected:
                    try:
                        # Move to recycle bin on Windows
                        if sys.platform == 'win32':
                            import ctypes
                            from ctypes import windll, c_wchar_p, c_uint
                            
                            # SHFileOperation for recycle bin
                            class SHFILEOPSTRUCT(ctypes.Structure):
                                _fields_ = [
                                    ("hwnd", ctypes.c_void_p),
                                    ("wFunc", c_uint),
                                    ("pFrom", c_wchar_p),
                                    ("pTo", c_wchar_p),
                                    ("fFlags", ctypes.c_uint16),
                                    ("fAnyOperationsAborted", ctypes.c_bool),
                                    ("hNameMappings", ctypes.c_void_p),
                                    ("lpszProgressTitle", c_wchar_p)
                                ]
                            
                            FO_DELETE = 0x0003
                            FOF_ALLOWUNDO = 0x0040
                            FOF_NOCONFIRMATION = 0x0010
                            FOF_SILENT = 0x0004
                            
                            fileop = SHFILEOPSTRUCT()
                            fileop.hwnd = None
                            fileop.wFunc = FO_DELETE
                            fileop.pFrom = path + '\0'
                            fileop.pTo = None
                            fileop.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT
                            fileop.fAnyOperationsAborted = False
                            fileop.hNameMappings = None
                            fileop.lpszProgressTitle = None
                            
                            result = windll.shell32.SHFileOperationW(ctypes.byref(fileop))
                            if result == 0:
                                deleted += 1
                            else:
                                failed += 1
                        else:
                            # On other platforms, just delete
                            os.remove(path)
                            deleted += 1
                    except Exception:
                        failed += 1
                
                manager.destroy()
                messagebox.showinfo("Done", f"Moved {deleted} files to Recycle Bin!" + (f"\n{failed} failed." if failed > 0 else ""))
                
                # Rescan to update results
                if deleted > 0:
                    self.collect_scan()
                
            except Exception as e:
                messagebox.showerror("Error", f"Error deleting files: {e}")
        
        tk.Button(btn_inner, text="Select All", command=select_all, font=("Segoe UI", 9), bg="#30363d", fg="#c9d1d9", padx=18, pady=9, cursor="hand2", relief=tk.FLAT, borderwidth=0).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(btn_inner, text="Select None", command=select_none, font=("Segoe UI", 9), bg="#30363d", fg="#c9d1d9", padx=18, pady=9, cursor="hand2", relief=tk.FLAT, borderwidth=0).pack(side=tk.LEFT, padx=(0, 20))
        tk.Button(btn_inner, text="Close", command=manager.destroy, font=("Segoe UI", 9), bg="#6e7681", fg="white", padx=24, pady=9, cursor="hand2", relief=tk.FLAT, borderwidth=0).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(btn_inner, text="Delete Selected", command=delete_selected, font=("Segoe UI", 10, "bold"), bg="#da3633", fg="white", padx=28, pady=10, cursor="hand2", relief=tk.FLAT, borderwidth=0).pack(side=tk.LEFT)
    
    def format_time(self, timestamp):
        """Format timestamp to readable date"""
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M")
    
    def move_group_to_review(self, paths_with_time, group_num, parent_window):
        """Move a duplicate group to a review folder for visual comparison"""
        try:
            # Create review folder
            script_dir = os.path.dirname(os.path.abspath(__file__))
            review_base = os.path.join(script_dir, "Duplicate Review")
            group_folder = os.path.join(review_base, f"Group_{group_num}")
            
            # Delete folder if it exists (refresh on each click)
            if os.path.exists(group_folder):
                shutil.rmtree(group_folder)
            os.makedirs(group_folder)
            
            # Copy all files in the group (including the one to keep)
            copied = 0
            for path, mtime in paths_with_time:
                try:
                    filename = os.path.basename(path)
                    
                    # Safe copy with conflict resolution
                    result = copy_file_safe(path, group_folder, filename)
                    if result:
                        copied += 1
                except Exception:
                    pass
            
            if copied > 0:
                messagebox.showinfo("Moved to Review", 
                                  f"Copied {copied} files to review folder.\n\nOpening folder now...\n\n{group_folder}")
                # Open the folder in File Explorer
                if sys.platform == 'win32':
                    os.startfile(group_folder)
                else:
                    import subprocess
                    subprocess.Popen(['xdg-open', group_folder])
                
                # Bring the duplicate manager window back to the front
                parent_window.lift()
                parent_window.focus_force()
            else:
                messagebox.showerror("Error", "Failed to copy files to review folder.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error creating review folder: {e}")
    
    def show_fullscreen_results(self, mode):
        """Show fullscreen results window"""
        # Create fullscreen window
        fs_window = tk.Toplevel(self.root)
        fs_window.title(f"Full Screen Results - {mode.capitalize()} Mode")
        fs_window.geometry("1200x800")
        fs_window.state('zoomed')  # Start maximized
        fs_window.configure(bg="#1e1e1e")
        
        # Title bar
        title_bar = tk.Frame(fs_window, bg="#0d1117")
        title_bar.pack(fill=tk.X)
        
        title = tk.Label(title_bar, text=f"Results - {mode.capitalize()} Mode", font=("Segoe UI", 18, "bold"), bg="#0d1117", fg="#c9d1d9", pady=20, padx=30)
        title.pack(side=tk.LEFT)
        
        # Close button in title
        close_title_btn = tk.Button(title_bar, text="✕ Close", command=fs_window.destroy, font=("Segoe UI", 10), bg="#da3633", fg="white", padx=15, pady=10, cursor="hand2", relief=tk.FLAT, borderwidth=0)
        close_title_btn.pack(side=tk.RIGHT, padx=30)
        
        # Main content frame
        content_frame = tk.Frame(fs_window, bg="#1e1e1e", padx=40, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Info label
        info = tk.Label(content_frame, text="Live view of operation results - updates automatically", font=("Segoe UI", 9), fg="#8b949e", bg="#1e1e1e")
        info.pack(pady=(0, 10))
        
        # Text widget with scrollbar
        text_frame = tk.Frame(content_frame, bg="#161b22", padx=2, pady=2)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(text_frame, bg="#0d1117")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(text_frame, font=("Consolas", 10), wrap=tk.WORD, yscrollcommand=scrollbar.set, bg="#0d1117", fg="#c9d1d9", insertbackground="#c9d1d9", padx=15, pady=15)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)
        
        # Enable mousewheel scrolling for text widget
        def on_mousewheel(event):
            text_widget.yview_scroll(int(-1*(event.delta/120)), "units")
        text_widget.bind("<MouseWheel>", on_mousewheel)
        
        # Copy current results
        if mode == 'organize':
            current_text = self.org_results.get("1.0", tk.END)
        else:
            current_text = self.collect_results.get("1.0", tk.END)
        
        text_widget.insert("1.0", current_text)
        text_widget.config(state=tk.DISABLED)
        
        # Auto-update function
        def update_results():
            if fs_window.winfo_exists():
                try:
                    if mode == 'organize':
                        new_text = self.org_results.get("1.0", tk.END)
                    else:
                        new_text = self.collect_results.get("1.0", tk.END)
                    
                    # Save current scroll position
                    current_yview = text_widget.yview()
                    at_bottom = current_yview[1] >= 0.99  # Check if scrolled to bottom
                    
                    # Update content
                    text_widget.config(state=tk.NORMAL)
                    text_widget.delete("1.0", tk.END)
                    text_widget.insert("1.0", new_text)
                    
                    # Restore scroll position or scroll to bottom if user was there
                    if at_bottom:
                        text_widget.see(tk.END)
                    else:
                        text_widget.yview_moveto(current_yview[0])  # Restore original position
                    
                    text_widget.config(state=tk.DISABLED)
                    
                    # Schedule next update
                    fs_window.after(500, update_results)  # Update every 500ms
                except:
                    pass
        
        # Start auto-update
        fs_window.after(500, update_results)
        
        # Bottom button frame
        btn_frame = tk.Frame(fs_window, bg="#0d1117", pady=15)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        tk.Button(btn_frame, text="Close", command=fs_window.destroy, font=("Segoe UI", 11, "bold"), bg="#238636", fg="white", padx=40, pady=12, cursor="hand2", relief=tk.FLAT, borderwidth=0).pack()


def main():
    root = tk.Tk()
    app = UnifiedGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
