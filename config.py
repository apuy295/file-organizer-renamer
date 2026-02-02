"""
Configuration file for File Organizer + Renamer
Defines file categorization rules and settings
"""

# File categorization by extension
FILE_CATEGORIES = {
    'images': [
        # Common formats
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.ico', '.tiff', '.tif',
        # RAW camera formats (photographers)
        '.raw', '.cr2', '.cr3', '.nef', '.arw', '.dng', '.orf', '.rw2', '.pef', '.srw', '.raf',
        # iPhone/mobile
        '.heic', '.heif',
        # Professional design
        '.psd', '.ai', '.eps', '.indd', '.svg',
        # Other
        '.jfif', '.jp2', '.jpx', '.avif'
    ],
    'videos': [
        # Common formats
        '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg',
        # Professional/camera formats
        '.mts', '.m2ts', '.ts', '.vob', '.mxf', '.f4v',
        # Other
        '.3gp', '.3g2', '.ogv', '.divx', '.xvid', '.rm', '.rmvb', '.asf', '.m2v'
    ],
    'documents': [
        # Microsoft Office
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.csv',
        # Text files
        '.txt', '.rtf', '.md', '.markdown',
        # OpenOffice/LibreOffice
        '.odt', '.ods', '.odp', '.odg',
        # eBooks
        '.epub', '.mobi', '.azw', '.azw3',
        # Other
        '.wps', '.pages', '.numbers', '.key', '.ps', '.oxps', '.xps'
    ],
    'installers': ['.exe', '.msi', '.dmg', '.pkg', '.deb', '.rpm', '.appimage', '.apk'],
    'archives': [
        '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.tar.gz', '.tar.bz2',
        '.iso', '.img', '.cab', '.z', '.lz', '.lzma', '.zipx'
    ],
    'audio': [
        # Common formats
        '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a',
        # Professional/lossless
        '.ape', '.alac', '.opus', '.dts', '.ac3',
        # Other
        '.mid', '.midi', '.amr', '.aiff', '.aif', '.mka', '.oga'
    ],
    'code': [
        # Programming languages
        '.py', '.js', '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb', '.go', '.rs',
        # Web
        '.html', '.css', '.scss', '.sass', '.less', '.jsx', '.tsx', '.vue',
        # Config/data
        '.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
        # Scripts
        '.sh', '.bash', '.bat', '.ps1', '.sql',
        # Other
        '.swift', '.kt', '.scala', '.r', '.m', '.pl', '.lua'
    ],
    'fonts': ['.ttf', '.otf', '.woff', '.woff2', '.eot', '.fon'],
    'cad_3d': ['.dwg', '.dxf', '.stl', '.obj', '.fbx', '.3ds', '.blend', '.max', '.skp'],
    'subtitles': ['.srt', '.sub', '.sbv', '.ass', '.ssa', '.vtt'],
    'databases': ['.db', '.sqlite', '.sqlite3', '.mdb', '.accdb', '.dbf'],
}

# Default category for files that don't match any category
DEFAULT_CATEGORY = 'others'

# Log file settings
LOG_DIRECTORY = 'logs'
LOG_FILE_PREFIX = 'file_organizer_'
LOG_FILE_EXTENSION = '.json'

# Date format for file prefixes (YYYYMMDD)
DATE_FORMAT = '%Y%m%d'

# Conflict resolution settings
CONFLICT_PATTERN = '({})'  # Pattern for numbering conflicts: filename(1).ext
