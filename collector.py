"""
PC-Wide File Collector
Safely search and collect files from multiple locations
"""

import os
from pathlib import Path
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass


@dataclass
class FoundFile:
    """Represents a found file during scanning"""
    path: str
    category: str
    extension: str
    size: int
    modified_time: float
    source_folder: str  # Which search location it came from


class FileCollector:
    """Search PC for files and collect them to one location"""
    
    # System folders to always skip (safety)
    SYSTEM_FOLDERS = {
        'windows', 'program files', 'program files (x86)', 
        'programdata', 'appdata', '$recycle.bin', 'system volume information',
        'perflogs', '$windows.~bt', '$windows.~ws'
    }
    
    # Default safe search locations (Windows user folders)
    DEFAULT_SEARCH_PATHS = [
        os.path.expanduser('~/Desktop'),
        os.path.expanduser('~/Downloads'),
        os.path.expanduser('~/Documents'),
        os.path.expanduser('~/Videos'),
        os.path.expanduser('~/Music'),
    ]
    
    # File type definitions
    FILE_TYPES = {
        'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico', '.tiff', '.tif'],
        'videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg'],
        'documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx'],
        'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'],
        'archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
    }
    
    def __init__(self, search_paths: List[str] = None, min_file_size: int = 5120):
        """
        Initialize file collector
        
        Args:
            search_paths: List of paths to search (uses defaults if None)
            min_file_size: Minimum file size in bytes (default 5KB to skip icons)
        """
        self.search_paths = search_paths if search_paths else self.DEFAULT_SEARCH_PATHS
        self.min_file_size = min_file_size
        self.found_files: List[FoundFile] = []
    
    def is_safe_path(self, path: str) -> bool:
        """
        Check if path is safe to scan (not a system folder)
        
        Args:
            path: Path to check
            
        Returns:
            True if safe to scan
        """
        path_lower = path.lower()
        
        # Check if path contains any system folder
        for sys_folder in self.SYSTEM_FOLDERS:
            if f'\\{sys_folder}\\' in path_lower or path_lower.endswith(f'\\{sys_folder}'):
                return False
        
        return True
    
    def get_category(self, file_path: str) -> str:
        """
        Get category for a file
        
        Args:
            file_path: Path to file
            
        Returns:
            Category name or None
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        for category, extensions in self.FILE_TYPES.items():
            if ext in extensions:
                return category
        
        return None
    
    def scan(self, file_types: List[str] = None, progress_callback=None) -> Dict[str, List[FoundFile]]:
        """
        Scan search paths for files
        
        Args:
            file_types: List of file types to find (e.g., ['images', 'videos']). None = all types
            progress_callback: Optional function to call with progress updates
            
        Returns:
            Dictionary of {category: [FoundFile, ...]}
        """
        self.found_files = []
        results = {ft: [] for ft in (file_types or self.FILE_TYPES.keys())}
        
        for search_path in self.search_paths:
            if not os.path.exists(search_path):
                continue
            
            if progress_callback:
                progress_callback(f"Scanning {search_path}...")
            
            try:
                for root, dirs, files in os.walk(search_path):
                    # Safety check - skip system folders
                    if not self.is_safe_path(root):
                        dirs.clear()  # Don't descend into this directory
                        continue
                    
                    for filename in files:
                        file_path = os.path.join(root, filename)
                        
                        # Get category
                        category = self.get_category(file_path)
                        
                        # Skip if not in requested types
                        if file_types and category not in file_types:
                            continue
                        
                        if not category:
                            continue
                        
                        try:
                            # Get file stats
                            stat = os.stat(file_path)
                            
                            # Skip tiny files (likely icons/thumbnails)
                            if stat.st_size < self.min_file_size:
                                continue
                            
                            # Create FoundFile object
                            ext = os.path.splitext(file_path)[1].lower().lstrip('.')
                            found_file = FoundFile(
                                path=file_path,
                                category=category,
                                extension=ext,
                                size=stat.st_size,
                                modified_time=stat.st_mtime,
                                source_folder=os.path.basename(search_path)
                            )
                            
                            results[category].append(found_file)
                            self.found_files.append(found_file)
                            
                        except (PermissionError, OSError):
                            # Skip files we can't access
                            continue
                            
            except (PermissionError, OSError):
                # Skip folders we can't access
                continue
        
        return results
    
    def get_summary(self) -> Dict[str, any]:
        """
        Get summary of found files
        
        Returns:
            Dictionary with statistics
        """
        if not self.found_files:
            return {'total': 0, 'by_category': {}, 'by_source': {}, 'total_size': 0}
        
        by_category = {}
        by_source = {}
        total_size = 0
        
        for f in self.found_files:
            # Count by category
            if f.category not in by_category:
                by_category[f.category] = 0
            by_category[f.category] += 1
            
            # Count by source
            if f.source_folder not in by_source:
                by_source[f.source_folder] = 0
            by_source[f.source_folder] += 1
            
            total_size += f.size
        
        return {
            'total': len(self.found_files),
            'by_category': by_category,
            'by_source': by_source,
            'total_size': total_size
        }
