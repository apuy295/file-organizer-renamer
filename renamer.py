"""
File Renamer Module
Handles file renaming according to specified rules
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from config import DATE_FORMAT


class FileRenamer:
    """Applies renaming rules to filenames"""
    
    def __init__(self, add_date_prefix: bool = False):
        """
        Initialize the renamer
        
        Args:
            add_date_prefix: Whether to add date prefix (YYYYMMDD_) to filenames
        """
        self.add_date_prefix = add_date_prefix
    
    def apply_rules(self, filename: str) -> str:
        """
        Apply all renaming rules to a filename
        
        Rules applied (in order):
        1. Lowercase the filename
        2. Replace spaces with underscores
        3. Remove duplicate underscores
        4. Add date prefix if enabled
        
        Args:
            filename: Original filename (with extension)
            
        Returns:
            Renamed filename
        """
        # Separate name and extension
        path = Path(filename)
        name = path.stem
        ext = path.suffix
        
        # Rule 1: Convert to lowercase
        name = name.lower()
        
        # Rule 2: Replace spaces with underscores
        name = name.replace(' ', '_')
        
        # Rule 3: Remove duplicate underscores
        name = re.sub(r'_+', '_', name)
        
        # Remove leading/trailing underscores
        name = name.strip('_')
        
        # Rule 4: Add date prefix if enabled
        if self.add_date_prefix:
            date_prefix = datetime.now().strftime(DATE_FORMAT)
            name = f"{date_prefix}_{name}"
        
        # Reconstruct filename with extension
        return f"{name}{ext.lower()}"
    
    def get_safe_filename(self, target_dir: str, filename: str) -> str:
        """
        Get a safe filename that doesn't conflict with existing files
        Appends (1), (2), etc. if file already exists
        
        Args:
            target_dir: Directory where the file will be placed
            filename: Desired filename
            
        Returns:
            Safe filename that doesn't exist in target_dir
        """
        target_path = os.path.join(target_dir, filename)
        
        # If no conflict, return as is
        if not os.path.exists(target_path):
            return filename
        
        # Handle conflict by adding counter
        path = Path(filename)
        name = path.stem
        ext = path.suffix
        
        counter = 1
        while True:
            new_filename = f"{name}({counter}){ext}"
            new_path = os.path.join(target_dir, new_filename)
            
            if not os.path.exists(new_path):
                return new_filename
            
            counter += 1
            
            # Safety check to prevent infinite loop
            if counter > 10000:
                raise ValueError(f"Too many conflicting files for '{filename}'")
    
    def rename_file(self, file_path: str) -> str:
        """
        Get the new name for a file (doesn't actually rename it)
        
        Args:
            file_path: Original file path
            
        Returns:
            New filename (not full path)
        """
        filename = os.path.basename(file_path)
        return self.apply_rules(filename)
    
    def needs_renaming(self, file_path: str) -> bool:
        """
        Check if a file needs to be renamed
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file needs renaming, False otherwise
        """
        original = os.path.basename(file_path)
        renamed = self.apply_rules(original)
        return original != renamed
