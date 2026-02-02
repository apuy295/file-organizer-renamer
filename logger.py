"""
Logging Module
Handles operation logging and undo functionality
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Tuple
from pathlib import Path
from config import LOG_DIRECTORY, LOG_FILE_PREFIX, LOG_FILE_EXTENSION


class OperationLogger:
    """Logs file operations for undo capability"""
    
    def __init__(self, log_directory: str = None):
        """
        Initialize the logger
        
        Args:
            log_directory: Directory to store log files (defaults to 'logs' in current dir)
        """
        if log_directory is None:
            log_directory = LOG_DIRECTORY
        
        self.log_directory = log_directory
        self.current_log_file: str = None
    
    def create_log_file(self) -> str:
        """
        Create a new log file with timestamp
        
        Returns:
            Path to the created log file
        """
        # Create log directory if it doesn't exist
        os.makedirs(self.log_directory, exist_ok=True)
        
        # Generate log filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = f"{LOG_FILE_PREFIX}{timestamp}{LOG_FILE_EXTENSION}"
        log_path = os.path.join(self.log_directory, log_filename)
        
        self.current_log_file = log_path
        return log_path
    
    def log_operations(self, operations: List, log_file: str = None) -> str:
        """
        Log file operations to a JSON file
        
        Args:
            operations: List of FileOperation objects
            log_file: Path to log file (creates new if None)
            
        Returns:
            Path to the log file
        """
        if log_file is None:
            log_file = self.create_log_file()
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'total_operations': len(operations),
            'successful_count': sum(1 for op in operations if op.success),
            'failed_count': sum(1 for op in operations if not op.success),
            'operations': []
        }
        
        for op in operations:
            operation_data = {
                'source_path': op.source_path,
                'target_path': op.target_path,
                'category': op.category,
                'success': op.success,
                'error': op.error,
                'renamed': op.is_renamed(),
                'moved': op.is_moved()
            }
            log_data['operations'].append(operation_data)
        
        # Write to log file
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        self.current_log_file = log_file
        return log_file
    
    def get_latest_log(self) -> str:
        """
        Get the path to the most recent log file
        
        Returns:
            Path to latest log file, or None if no logs exist
        """
        if not os.path.isdir(self.log_directory):
            return None
        
        log_files = [
            os.path.join(self.log_directory, f)
            for f in os.listdir(self.log_directory)
            if f.startswith(LOG_FILE_PREFIX) and f.endswith(LOG_FILE_EXTENSION)
        ]
        
        if not log_files:
            return None
        
        # Sort by modification time (most recent first)
        log_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return log_files[0]
    
    def load_log(self, log_file: str) -> Dict:
        """
        Load a log file
        
        Args:
            log_file: Path to log file
            
        Returns:
            Dictionary with log data
        """
        if not os.path.exists(log_file):
            raise FileNotFoundError(f"Log file not found: {log_file}")
        
        with open(log_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def undo_operations(self, log_file: str = None) -> Tuple[List[Dict], List[Dict]]:
        """
        Undo operations from a log file
        
        Args:
            log_file: Path to log file (uses latest if None)
            
        Returns:
            Tuple of (successful_undos, failed_undos)
        """
        if log_file is None:
            log_file = self.get_latest_log()
            if log_file is None:
                raise FileNotFoundError("No log files found to undo")
        
        log_data = self.load_log(log_file)
        
        successful_undos = []
        failed_undos = []
        
        # Process operations in reverse order
        operations = log_data['operations']
        for op_data in reversed(operations):
            # Only undo successful operations
            if not op_data['success']:
                continue
            
            source = op_data['source_path']
            target = op_data['target_path']
            
            try:
                # Check if target file still exists
                if not os.path.exists(target):
                    failed_undos.append({
                        **op_data,
                        'undo_error': f"Target file not found: {target}"
                    })
                    continue
                
                # Create source directory if needed
                source_dir = os.path.dirname(source)
                if source_dir and not os.path.exists(source_dir):
                    os.makedirs(source_dir, exist_ok=True)
                
                # Move file back to original location
                import shutil
                shutil.move(target, source)
                
                successful_undos.append(op_data)
                
            except PermissionError as e:
                failed_undos.append({
                    **op_data,
                    'undo_error': f"Permission denied: {e}"
                })
            except Exception as e:
                failed_undos.append({
                    **op_data,
                    'undo_error': f"Error: {e}"
                })
        
        return successful_undos, failed_undos
    
    def get_log_summary(self, log_file: str = None) -> Dict:
        """
        Get summary of a log file
        
        Args:
            log_file: Path to log file (uses latest if None)
            
        Returns:
            Dictionary with summary information
        """
        if log_file is None:
            log_file = self.get_latest_log()
            if log_file is None:
                return None
        
        log_data = self.load_log(log_file)
        
        return {
            'log_file': log_file,
            'timestamp': log_data['timestamp'],
            'total_operations': log_data['total_operations'],
            'successful_count': log_data['successful_count'],
            'failed_count': log_data['failed_count']
        }
