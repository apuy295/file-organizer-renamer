"""
File Categorizer Module
Handles file categorization based on extensions
"""

import os
from typing import Dict, List
from pathlib import Path
from config import FILE_CATEGORIES, DEFAULT_CATEGORY


class FileCategorizer:
    """Categorizes files based on their extensions"""
    
    def __init__(self, custom_categories: Dict[str, List[str]] = None):
        """
        Initialize the categorizer
        
        Args:
            custom_categories: Optional custom category mappings (overrides defaults)
        """
        self.categories = custom_categories if custom_categories else FILE_CATEGORIES
    
    def get_category(self, file_path: str) -> str:
        """
        Determine the category of a file based on its extension
        
        Args:
            file_path: Path to the file
            
        Returns:
            Category name (e.g., 'images', 'videos', 'others')
        """
        ext = Path(file_path).suffix.lower()
        
        # Search for matching category
        for category, extensions in self.categories.items():
            if ext in extensions:
                return category
        
        return DEFAULT_CATEGORY
    
    def scan_directory(self, directory: str, recursive: bool = False) -> Dict[str, List[str]]:
        """
        Scan a directory and categorize all files
        
        Args:
            directory: Path to the directory to scan
            recursive: If True, scan subdirectories recursively (default: False)
            
        Returns:
            Dictionary mapping categories to lists of file paths
        """
        if not os.path.isdir(directory):
            raise ValueError(f"'{directory}' is not a valid directory")
        
        categorized_files = {}
        
        try:
            if recursive:
                # Recursive scanning with os.walk
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        file_path = os.path.join(root, file)
                        category = self.get_category(file_path)
                        
                        if category not in categorized_files:
                            categorized_files[category] = []
                        
                        categorized_files[category].append(file_path)
            else:
                # Non-recursive: only scan top level
                for item in os.listdir(directory):
                    item_path = os.path.join(directory, item)
                    
                    # Only process files, not directories
                    if os.path.isfile(item_path):
                        category = self.get_category(item_path)
                        
                        if category not in categorized_files:
                            categorized_files[category] = []
                        
                        categorized_files[category].append(item_path)
        
        except PermissionError as e:
            raise PermissionError(f"Permission denied accessing '{directory}': {e}")
        except Exception as e:
            raise Exception(f"Error scanning directory '{directory}': {e}")
        
        return categorized_files
    
    def get_category_count(self, directory: str, recursive: bool = False) -> Dict[str, int]:
        """
        Get count of files in each category
        
        Args:
            directory: Path to the directory to scan
            recursive: If True, scan subdirectories recursively (default: False)
            
        Returns:
            Dictionary mapping categories to file counts
        """
        categorized = self.scan_directory(directory, recursive=recursive)
        return {category: len(files) for category, files in categorized.items()}
