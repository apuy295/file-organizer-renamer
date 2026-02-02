"""
Version information for File Organizer + Renamer
"""

__version__ = '1.0.0'
__author__ = 'File Organizer + Renamer Project'
__description__ = 'A safety-first file organization tool'
__license__ = 'MIT'

# Version history
VERSION_INFO = {
    '1.0.0': {
        'release_date': '2026-02-01',
        'features': [
            'File categorization by extension',
            'Smart file renaming (lowercase, underscores)',
            'Preview mode for safe planning',
            'Apply mode with user confirmation',
            'Undo functionality with JSON logging',
            'No-overwrite conflict resolution',
            'Comprehensive error handling',
            'CLI interface with multiple modes',
            'Offline operation (no external services)',
            'Cross-platform support (Windows optimized)'
        ]
    }
}

def get_version():
    """Get current version string"""
    return __version__

def get_version_info():
    """Get detailed version information"""
    return VERSION_INFO.get(__version__, {})
