"""
File Organizer Module
Core logic for organizing files with safety checks
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from categorizer import FileCategorizer
from renamer import FileRenamer


def cleanup_empty_folders(directory: str, protected_folders: List[str] = None) -> List[str]:
    """
    Remove empty folders from a directory
    
    Args:
        directory: Root directory to clean
        protected_folders: List of folder names to never delete (e.g., category folders)
        
    Returns:
        List of deleted folder paths
    """
    if protected_folders is None:
        protected_folders = []
    
    deleted_folders = []
    
    # Walk bottom-up so we delete nested empty folders first
    for root, dirs, files in os.walk(directory, topdown=False):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            
            # Skip protected folders
            if dir_name in protected_folders:
                continue
            
            try:
                # Check if folder is empty (no files and no subdirectories)
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    deleted_folders.append(dir_path)
            except (PermissionError, OSError):
                # Skip folders we can't access or delete
                continue
    
    return deleted_folders


class FileOperation:
    """Represents a single file operation (move + optional rename)"""
    
    def __init__(self, source_path: str, target_path: str, category: str):
        """
        Initialize a file operation
        
        Args:
            source_path: Original file path
            target_path: Target file path (after move/rename)
            category: File category
        """
        self.source_path = source_path
        self.target_path = target_path
        self.category = category
        self.error: Optional[str] = None
        self.success: bool = False
    
    def get_source_name(self) -> str:
        """Get source filename"""
        return os.path.basename(self.source_path)
    
    def get_target_name(self) -> str:
        """Get target filename"""
        return os.path.basename(self.target_path)
    
    def is_renamed(self) -> bool:
        """Check if file will be renamed"""
        return self.get_source_name() != self.get_target_name()
    
    def is_moved(self) -> bool:
        """Check if file will be moved to different directory"""
        source_dir = os.path.dirname(self.source_path)
        target_dir = os.path.dirname(self.target_path)
        
        try:
            return not os.path.samefile(source_dir, target_dir)
        except (FileNotFoundError, OSError):
            # Fall back to path comparison if samefile fails
            return os.path.abspath(source_dir) != os.path.abspath(target_dir)


class FileOrganizer:
    """Main file organizer with safety features"""
    
    def __init__(self, source_directory: str, add_date_prefix: bool = False, recursive: bool = False, sub_folders_by_extension: bool = False):
        """
        Initialize the file organizer
        
        Args:
            source_directory: Directory to organize
            add_date_prefix: Whether to add date prefix to filenames
            recursive: Whether to scan subdirectories recursively (default: False)
            sub_folders_by_extension: Whether to create sub-folders by file extension (default: False)
        """
        if not os.path.isdir(source_directory):
            raise ValueError(f"'{source_directory}' is not a valid directory")
        
        self.source_directory = os.path.abspath(source_directory)
        self.categorizer = FileCategorizer()
        self.renamer = FileRenamer(add_date_prefix=add_date_prefix)
        self.recursive = recursive
        self.sub_folders_by_extension = sub_folders_by_extension
        self.operations: List[FileOperation] = []
    
    def plan_operations(self) -> List[FileOperation]:
        """
        Plan all file operations without executing them
        
        Returns:
            List of planned file operations
        """
        self.operations = []
        
        # Scan and categorize files
        categorized_files = self.categorizer.scan_directory(self.source_directory, recursive=self.recursive)
        
        for category, files in categorized_files.items():
            # Create category subdirectory path
            category_dir = os.path.join(self.source_directory, category)
            
            for file_path in files:
                # Get renamed filename
                new_filename = self.renamer.rename_file(file_path)
                
                # Determine target directory (with or without extension sub-folder)
                if self.sub_folders_by_extension:
                    # Get file extension (without dot)
                    ext = os.path.splitext(file_path)[1].lower().lstrip('.')
                    if not ext:
                        ext = 'no_extension'
                    target_dir = os.path.join(category_dir, ext)
                else:
                    target_dir = category_dir
                
                # Store the base filename for conflict resolution during execution
                # We don't check if it exists here - that happens atomically during the move
                target_path = os.path.join(target_dir, new_filename)
                
                # Create operation
                operation = FileOperation(
                    source_path=file_path,
                    target_path=target_path,
                    category=category
                )
                
                self.operations.append(operation)
        
        return self.operations
    
    def execute_operations(self, operations: List[FileOperation] = None) -> Tuple[List[FileOperation], List[FileOperation]]:
        """
        Execute the planned file operations
        
        Args:
            operations: List of operations to execute (uses planned if None)
            
        Returns:
            Tuple of (successful_operations, failed_operations)
        """
        if operations is None:
            operations = self.operations
        
        if not operations:
            raise ValueError("No operations planned. Call plan_operations() first.")
        
        successful = []
        failed = []
        
        for operation in operations:
            try:
                # Create target directory if it doesn't exist
                target_dir = os.path.dirname(operation.target_path)
                os.makedirs(target_dir, exist_ok=True)
                
                # Get the base filename from the operation's target path
                base_filename = os.path.basename(operation.target_path)
                
                # Try to move the file, handling conflicts atomically
                counter = 0
                while counter <= 10000:
                    # Generate filename with counter (0 means no suffix)
                    filename = self.renamer.generate_unique_filename(base_filename, counter)
                    final_target = os.path.join(target_dir, filename)
                    
                    # Check if target exists
                    if os.path.exists(final_target):
                        # File exists, try next counter
                        counter += 1
                        continue
                    
                    # Try to move the file
                    # If another process creates the file between our check and move,
                    # shutil.move will still succeed but might overwrite
                    # To be truly atomic, we'd need OS-specific operations
                    # For now, this is much better than the previous approach
                    shutil.move(operation.source_path, final_target)
                    
                    # Update operation with actual final path
                    operation.target_path = final_target
                    operation.success = True
                    successful.append(operation)
                    break
                else:
                    # Exceeded max counter
                    raise ValueError(f"Too many conflicting files for '{base_filename}'")
                
            except PermissionError as e:
                operation.error = f"Permission denied: {e}"
                operation.success = False
                failed.append(operation)
                
            except FileNotFoundError as e:
                operation.error = f"File not found: {e}"
                operation.success = False
                failed.append(operation)
                
            except Exception as e:
                operation.error = f"Error: {e}"
                operation.success = False
                failed.append(operation)
        
        return successful, failed
    
    def get_preview_summary(self) -> Dict[str, any]:
        """
        Get a summary of planned operations for preview
        
        Returns:
            Dictionary with summary statistics
        """
        if not self.operations:
            return {
                'total_files': 0,
                'categories': {},
                'renamed_count': 0,
                'moved_count': 0
            }
        
        categories = {}
        renamed_count = 0
        moved_count = 0
        
        for op in self.operations:
            # Count by category
            if op.category not in categories:
                categories[op.category] = 0
            categories[op.category] += 1
            
            # Count renames and moves
            if op.is_renamed():
                renamed_count += 1
            if op.is_moved():
                moved_count += 1
        
        return {
            'total_files': len(self.operations),
            'categories': categories,
            'renamed_count': renamed_count,
            'moved_count': moved_count
        }
