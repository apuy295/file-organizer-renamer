"""
File Organizer + Renamer - One-Time Setup
Runs once after downloading to set up desktop shortcut and dependencies.
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox
import subprocess

def create_desktop_shortcut():
    """Create desktop shortcut (Windows)"""
    try:
        if sys.platform != 'win32':
            return False, "Desktop shortcuts are only supported on Windows"
        
        # Get paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        pyw_path = os.path.join(script_dir, "gui_unified.pyw")
        icon_path = os.path.join(script_dir, "icon.ico")
        
        # Verify .pyw file exists
        if not os.path.exists(pyw_path):
            return False, f"gui_unified.pyw not found in {script_dir}"
        
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
            return True, "Desktop shortcut created successfully!"
        else:
            return False, f"Failed to create shortcut: {result.stderr}"
            
    except Exception as e:
        return False, f"Error creating shortcut: {e}"

def install_dependencies():
    """Check and optionally install Pillow"""
    try:
        import PIL
        return True, "Pillow already installed"
    except ImportError:
        return False, "Pillow not installed (optional - enables EXIF date reading)"

class SetupGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("File Organizer + Renamer - Setup")
        self.root.geometry("550x400")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e1e")
        
        # Set icon if available
        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
        
        self.create_widgets()
        
    def create_widgets(self):
        # Title
        title_frame = tk.Frame(self.root, bg="#0d1117", height=80)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        tk.Label(
            title_frame,
            text="Welcome to File Organizer + Renamer",
            font=("Segoe UI", 16, "bold"),
            bg="#0d1117",
            fg="#c9d1d9"
        ).pack(pady=25)
        
        # Content
        content = tk.Frame(self.root, bg="#1e1e1e", padx=40, pady=30)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Welcome message
        tk.Label(
            content,
            text="First-time setup - this only needs to be run once!",
            font=("Segoe UI", 11),
            bg="#1e1e1e",
            fg="#c9d1d9"
        ).pack(pady=(0, 20))
        
        # Dependency status
        dep_frame = tk.LabelFrame(
            content,
            text="Dependencies",
            font=("Segoe UI", 9),
            bg="#161b22",
            fg="#8b949e",
            padx=20,
            pady=15
        )
        dep_frame.pack(fill=tk.X, pady=(0, 20))
        
        pillow_installed, pillow_msg = install_dependencies()
        pillow_color = "#238636" if pillow_installed else "#8b949e"
        pillow_icon = "✓" if pillow_installed else "ⓘ"
        
        tk.Label(
            dep_frame,
            text=f"{pillow_icon} {pillow_msg}",
            font=("Segoe UI", 9),
            bg="#161b22",
            fg=pillow_color
        ).pack(anchor=tk.W)
        
        if not pillow_installed:
            install_btn = tk.Button(
                dep_frame,
                text="Install Pillow (Recommended)",
                command=self.install_pillow,
                font=("Segoe UI", 9),
                bg="#238636",
                fg="white",
                padx=15,
                pady=5,
                cursor="hand2",
                relief=tk.FLAT
            )
            install_btn.pack(anchor=tk.W, pady=(10, 0))
        
        # Shortcut question
        shortcut_frame = tk.LabelFrame(
            content,
            text="Desktop Shortcut",
            font=("Segoe UI", 9),
            bg="#161b22",
            fg="#8b949e",
            padx=20,
            pady=15
        )
        shortcut_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(
            shortcut_frame,
            text="Would you like to create a desktop shortcut for easy access?",
            font=("Segoe UI", 9),
            bg="#161b22",
            fg="#c9d1d9"
        ).pack(anchor=tk.W)
        
        btn_frame = tk.Frame(shortcut_frame, bg="#161b22")
        btn_frame.pack(fill=tk.X, pady=(15, 0))
        
        tk.Button(
            btn_frame,
            text="Yes, create shortcut",
            command=self.create_shortcut_and_finish,
            font=("Segoe UI", 10, "bold"),
            bg="#238636",
            fg="white",
            padx=20,
            pady=10,
            cursor="hand2",
            relief=tk.FLAT
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(
            btn_frame,
            text="No, skip",
            command=self.finish_without_shortcut,
            font=("Segoe UI", 10),
            bg="#6e7681",
            fg="white",
            padx=20,
            pady=10,
            cursor="hand2",
            relief=tk.FLAT
        ).pack(side=tk.LEFT)
        
        # Note
        tk.Label(
            content,
            text="💡 You can create a shortcut later via the app's Help menu",
            font=("Segoe UI", 8),
            bg="#1e1e1e",
            fg="#8b949e"
        ).pack(pady=(10, 0))
    
    def install_pillow(self):
        """Install Pillow via pip"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "pillow"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                messagebox.showinfo("Success", "Pillow installed successfully!\n\nThis enables EXIF date reading from photos.")
            else:
                messagebox.showerror("Error", f"Failed to install Pillow:\n{result.stderr}")
        except Exception as e:
            messagebox.showerror("Error", f"Error installing Pillow:\n{e}")
    
    def create_shortcut_and_finish(self):
        """Create shortcut and finish setup"""
        success, message = create_desktop_shortcut()
        
        if success:
            messagebox.showinfo(
                "Setup Complete!",
                "✓ Desktop shortcut created!\n\n"
                "You can now close this window and use the desktop shortcut to launch the app.\n\n"
                "You don't need to run setup.py again."
            )
        else:
            messagebox.showerror("Error", f"Could not create shortcut:\n{message}\n\nYou can create it later from the app's Help menu.")
        
        self.root.destroy()
    
    def finish_without_shortcut(self):
        """Finish without creating shortcut"""
        messagebox.showinfo(
            "Setup Complete!",
            "Setup finished!\n\n"
            "To launch the app:\n"
            "• Double-click 'gui_unified.pyw'\n"
            "• Or create a shortcut later via the Help menu\n\n"
            "You don't need to run setup.py again."
        )
        self.root.destroy()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    # Make sure we're in the right directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Run GUI setup
    app = SetupGUI()
    app.run()
