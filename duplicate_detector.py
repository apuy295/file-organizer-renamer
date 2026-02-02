"""
Duplicate File Detector
Finds duplicate files by comparing content hashes
"""

import os
import hashlib
from pathlib import Path
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass


@dataclass
class DuplicateGroup:
    """Represents a group of duplicate files"""
    hash_value: str
    file_paths: List[str]
    file_size: int
    
    def get_total_wasted_space(self) -> int:
        """Calculate wasted space (size * number of duplicates - size)"""
        if len(self.file_paths) <= 1:
            return 0
        return self.file_size * (len(self.file_paths) - 1)


class DuplicateDetector:
    """Detect duplicate files by content hash"""
    
    def __init__(self, min_file_size: int = 0):
        """
        Initialize duplicate detector
        
        Args:
            min_file_size: Minimum file size to consider (bytes). Skip tiny files.
        """
        self.min_file_size = min_file_size
        self.duplicate_groups: List[DuplicateGroup] = []
    
    def _calculate_file_hash(self, file_path: str, chunk_size: int = 8192) -> str:
        """
        Calculate SHA256 hash of file content
        
        Args:
            file_path: Path to file
            chunk_size: Size of chunks to read (for large files)
            
        Returns:
            Hex string of file hash
        """
        sha256 = hashlib.sha256()
        
        try:
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    sha256.update(chunk)
            return sha256.hexdigest()
        except (PermissionError, OSError):
            return None
    
    def scan_for_duplicates(self, directory: str, recursive: bool = True, 
                           progress_callback=None) -> List[DuplicateGroup]:
        """
        Scan directory for duplicate files
        
        Args:
            directory: Directory to scan
            recursive: Scan subdirectories
            progress_callback: Optional callback function(message) for progress updates
            
        Returns:
            List of duplicate groups
        """
        self.duplicate_groups = []
        
        # First pass: Group by file size (fast pre-filter)
        size_groups: Dict[int, List[str]] = {}
        
        if progress_callback:
            progress_callback("Scanning files...")
        
        # Collect all files
        if recursive:
            for root, dirs, files in os.walk(directory):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    try:
                        file_size = os.path.getsize(file_path)
                        
                        # Skip tiny files
                        if file_size < self.min_file_size:
                            continue
                        
                        if file_size not in size_groups:
                            size_groups[file_size] = []
                        size_groups[file_size].append(file_path)
                    except (PermissionError, OSError):
                        continue
        else:
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                if os.path.isfile(file_path):
                    try:
                        file_size = os.path.getsize(file_path)
                        
                        if file_size < self.min_file_size:
                            continue
                        
                        if file_size not in size_groups:
                            size_groups[file_size] = []
                        size_groups[file_size].append(file_path)
                    except (PermissionError, OSError):
                        continue
        
        # Second pass: Check content hash for files with same size
        if progress_callback:
            progress_callback(f"Checking {len([f for files in size_groups.values() for f in files])} files for duplicates...")
        
        hash_groups: Dict[str, List[str]] = {}
        
        for file_size, file_paths in size_groups.items():
            # Only hash if there are multiple files with same size
            if len(file_paths) > 1:
                for file_path in file_paths:
                    file_hash = self._calculate_file_hash(file_path)
                    if file_hash:
                        if file_hash not in hash_groups:
                            hash_groups[file_hash] = []
                        hash_groups[file_hash].append(file_path)
        
        # Build duplicate groups (only groups with 2+ files)
        for file_hash, file_paths in hash_groups.items():
            if len(file_paths) > 1:
                # Get file size (all files in group have same size)
                file_size = os.path.getsize(file_paths[0])
                
                group = DuplicateGroup(
                    hash_value=file_hash,
                    file_paths=sorted(file_paths),
                    file_size=file_size
                )
                self.duplicate_groups.append(group)
        
        # Sort by wasted space (most wasteful first)
        self.duplicate_groups.sort(key=lambda g: g.get_total_wasted_space(), reverse=True)
        
        if progress_callback:
            total_dupes = sum(len(g.file_paths) - 1 for g in self.duplicate_groups)
            progress_callback(f"Found {len(self.duplicate_groups)} duplicate groups ({total_dupes} duplicate files)")
        
        return self.duplicate_groups
    
    def get_summary(self) -> Dict[str, any]:
        """Get summary statistics"""
        total_duplicate_files = sum(len(g.file_paths) - 1 for g in self.duplicate_groups)
        total_wasted_space = sum(g.get_total_wasted_space() for g in self.duplicate_groups)
        
        return {
            'duplicate_groups': len(self.duplicate_groups),
            'total_duplicate_files': total_duplicate_files,
            'total_wasted_space': total_wasted_space,
            'largest_group': max((len(g.file_paths) for g in self.duplicate_groups), default=0)
        }
