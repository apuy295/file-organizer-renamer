"""
Date-Based File Organizer
Organize files by date (year/month) using file modification or EXIF data
"""

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

# Try to import Pillow for EXIF data (optional)
try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


class DateOrganizer:
    """Organize files by date into year/month folders"""
    
    @staticmethod
    def get_file_date(file_path: str, use_exif: bool = True) -> Optional[datetime]:
        """
        Get the date of a file
        
        Args:
            file_path: Path to file
            use_exif: Try to read EXIF date from images (requires Pillow)
            
        Returns:
            datetime object or None if failed
        """
        # Try EXIF first (for images) if Pillow is available
        if use_exif and PILLOW_AVAILABLE:
            exif_date = DateOrganizer._get_exif_date(file_path)
            if exif_date:
                return exif_date
        
        # Fallback to file modification time
        try:
            mtime = os.path.getmtime(file_path)
            return datetime.fromtimestamp(mtime)
        except (OSError, ValueError):
            return None
    
    @staticmethod
    def _get_exif_date(file_path: str) -> Optional[datetime]:
        """
        Extract date from EXIF data (images only)
        
        Args:
            file_path: Path to image file
            
        Returns:
            datetime object or None if no EXIF date found
        """
        if not PILLOW_AVAILABLE:
            return None
        
        try:
            image = Image.open(file_path)
            exif_data = image._getexif()
            
            if not exif_data:
                return None
            
            # Look for DateTimeOriginal (when photo was taken)
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)
                
                if tag_name == 'DateTimeOriginal':
                    # Parse EXIF date format: "2024:01:15 14:30:22"
                    try:
                        return datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                    except ValueError:
                        pass
            
            return None
            
        except Exception:
            return None
    
    @staticmethod
    def get_date_folder_path(base_dir: str, file_date: datetime, 
                            format_style: str = 'year_month') -> str:
        """
        Generate date-based folder path
        
        Args:
            base_dir: Base directory
            file_date: Date of file
            format_style: Folder structure style
                - 'year_month': 2024/01_January/
                - 'year_only': 2024/
                - 'year_month_simple': 2024/01/
                
        Returns:
            Full path to date folder
        """
        year = str(file_date.year)
        month_num = f"{file_date.month:02d}"
        month_name = file_date.strftime('%B')  # Full month name
        
        if format_style == 'year_month':
            return os.path.join(base_dir, year, f"{month_num}_{month_name}")
        elif format_style == 'year_only':
            return os.path.join(base_dir, year)
        elif format_style == 'year_month_simple':
            return os.path.join(base_dir, year, month_num)
        else:
            return os.path.join(base_dir, year, f"{month_num}_{month_name}")
    
    @staticmethod
    def is_pillow_available() -> bool:
        """Check if Pillow is available for EXIF reading"""
        return PILLOW_AVAILABLE
