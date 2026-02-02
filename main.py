#!/usr/bin/env python3
"""
File Organizer + Renamer
A safety-first file organization tool

Usage:
    python main.py --preview /path/to/folder
    python main.py --apply /path/to/folder
    python main.py --undo
    python main.py --dry-run /path/to/folder
"""

import sys
import os
import argparse
from pathlib import Path
from organizer import FileOrganizer
from logger import OperationLogger


def print_separator(char='=', length=80):
    """Print a separator line"""
    print(char * length)


def print_operation_details(operations):
    """Print detailed information about operations"""
    if not operations:
        print("No operations to perform.")
        return
    
    print(f"\nTotal files to process: {len(operations)}\n")
    
    for i, op in enumerate(operations, 1):
        print(f"{i}. [{op.category.upper()}]")
        print(f"   FROM: {op.source_path}")
        print(f"   TO:   {op.target_path}")
        
        if op.is_renamed():
            print(f"   RENAME: {op.get_source_name()} → {op.get_target_name()}")
        
        if op.error:
            print(f"   ERROR: {op.error}")
        
        print()


def print_summary(summary):
    """Print operation summary"""
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total files: {summary['total_files']}")
    print(f"Files to be renamed: {summary['renamed_count']}")
    print(f"Files to be moved: {summary['moved_count']}")
    print("\nFiles by category:")
    for category, count in summary['categories'].items():
        print(f"  {category}: {count}")
    print("=" * 80)


def preview_mode(directory, add_date_prefix, recursive):
    """Preview mode: Show what would happen without making changes"""
    print_separator()
    mode_text = "PREVIEW MODE - No files will be modified"
    if recursive:
        mode_text += " (RECURSIVE)"
    print(mode_text)
    print_separator()
    
    try:
        organizer = FileOrganizer(directory, add_date_prefix=add_date_prefix, recursive=recursive)
        operations = organizer.plan_operations()
        
        if not operations:
            print("\nNo files found to organize.")
            return
        
        # Show detailed operations
        print_operation_details(operations)
        
        # Show summary
        summary = organizer.get_preview_summary()
        print_summary(summary)
        
        print("\n✓ Preview complete. Use --apply to execute these changes.")
        
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


def apply_mode(directory, add_date_prefix, recursive, clean_empty):
    """Apply mode: Execute file operations"""
    print_separator()
    mode_text = "APPLY MODE - Files will be organized"
    if recursive:
        mode_text += " (RECURSIVE)"
    if clean_empty:
        mode_text += " + CLEANUP"
    print(mode_text)
    print_separator()
    
    try:
        from organizer import cleanup_empty_folders
        
        organizer = FileOrganizer(directory, add_date_prefix=add_date_prefix, recursive=recursive)
        operations = organizer.plan_operations()
        
        if not operations:
            print("\nNo files found to organize.")
            return
        
        # Show summary
        summary = organizer.get_preview_summary()
        print_summary(summary)
        
        # Ask for confirmation
        print("\n⚠ WARNING: This will move and rename files!")
        if clean_empty:
            print("⚠ WARNING: Empty folders will be deleted after organizing!")
        response = input("Continue? (yes/no): ").strip().lower()
        
        if response not in ['yes', 'y']:
            print("\n✗ Operation cancelled by user.")
            return
        
        # Execute operations
        print("\nExecuting operations...")
        successful, failed = organizer.execute_operations()
        
        # Clean up empty folders if requested
        deleted_folders = []
        if clean_empty:
            print("\nCleaning up empty folders...")
            # Get category names from summary to protect them
            protected = list(summary['categories'].keys())
            deleted_folders = cleanup_empty_folders(directory, protected)
        
        # Log operations
        logger = OperationLogger()
        log_file = logger.log_operations(successful + failed)
        
        # Show results
        print_separator()
        print("RESULTS")
        print_separator()
        print(f"✓ Successful: {len(successful)}")
        print(f"✗ Failed: {len(failed)}")
        if clean_empty and deleted_folders:
            print(f"🗑️  Empty folders deleted: {len(deleted_folders)}")
        print(f"📝 Log file: {log_file}")
        
        if failed:
            print("\nFailed operations:")
            for op in failed:
                print(f"  ✗ {op.source_path}")
                print(f"    Error: {op.error}")
        
        if deleted_folders:
            print("\nDeleted empty folders:")
            for folder in deleted_folders[:10]:  # Show first 10
                print(f"  🗑️  {folder}")
            if len(deleted_folders) > 10:
                print(f"  ... and {len(deleted_folders) - 10} more")
        
        print_separator()
        print(f"✓ Operation complete. Use --undo to reverse changes.")
        
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


def undo_mode(log_file):
    """Undo mode: Reverse the last operation"""
    print_separator()
    print("UNDO MODE - Reversing last operation")
    print_separator()
    
    try:
        logger = OperationLogger()
        
        # Get log file info
        if log_file is None:
            log_file = logger.get_latest_log()
            if log_file is None:
                print("✗ No log files found. Nothing to undo.")
                return
        
        summary = logger.get_log_summary(log_file)
        print(f"\nLog file: {summary['log_file']}")
        print(f"Timestamp: {summary['timestamp']}")
        print(f"Total operations: {summary['total_operations']}")
        print(f"Successful: {summary['successful_count']}")
        print(f"Failed: {summary['failed_count']}")
        
        # Ask for confirmation
        print("\n⚠ WARNING: This will move files back to their original locations!")
        response = input("Continue? (yes/no): ").strip().lower()
        
        if response not in ['yes', 'y']:
            print("\n✗ Undo cancelled by user.")
            return
        
        # Undo operations
        print("\nUndoing operations...")
        successful, failed = logger.undo_operations(log_file)
        
        # Show results
        print_separator()
        print("UNDO RESULTS")
        print_separator()
        print(f"✓ Successfully restored: {len(successful)}")
        print(f"✗ Failed to restore: {len(failed)}")
        
        if failed:
            print("\nFailed to restore:")
            for op in failed:
                print(f"  ✗ {op['target_path']}")
                print(f"    Error: {op['undo_error']}")
        
        print_separator()
        
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


def dry_run_mode(directory, add_date_prefix, recursive):
    """Dry run mode: Same as preview but with different terminology"""
    print_separator()
    mode_text = "DRY RUN MODE - Simulating operations"
    if recursive:
        mode_text += " (RECURSIVE)"
    print(mode_text)
    print_separator()
    
    preview_mode(directory, add_date_prefix, recursive)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='File Organizer + Renamer - A safety-first file organization tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Preview changes:
    python main.py --preview "C:\\Users\\YourName\\Downloads"
  
  Apply changes:
    python main.py --apply "C:\\Users\\YourName\\Downloads"
  
  Add date prefix to filenames:
    python main.py --preview "C:\\Users\\YourName\\Downloads" --date-prefix
  
  Undo last operation:
    python main.py --undo
  
  Dry run (same as preview):
    python main.py --dry-run "C:\\Users\\YourName\\Downloads"

Safety Features:
  - Preview mode shows all changes before applying
  - No files are overwritten (conflicts get numbered)
  - All operations are logged for undo capability
  - Works offline with no external services
        """
    )
    
    # Mode selection (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--preview', metavar='DIRECTORY', 
                           help='Preview changes without applying them')
    mode_group.add_argument('--apply', metavar='DIRECTORY',
                           help='Apply changes to files')
    mode_group.add_argument('--undo', nargs='?', const=True, metavar='LOG_FILE',
                           help='Undo last operation (optionally specify log file)')
    mode_group.add_argument('--dry-run', metavar='DIRECTORY',
                           help='Dry run (same as --preview)')
    
    # Additional options
    parser.add_argument('--date-prefix', action='store_true',
                       help='Add date prefix (YYYYMMDD_) to filenames')
    parser.add_argument('--recursive', action='store_true',
                       help='Scan subdirectories recursively (default: top-level only)')
    parser.add_argument('--clean-empty', action='store_true',
                       help='Delete empty folders after organizing (optional)')
    
    args = parser.parse_args()
    
    # Execute based on mode
    if args.preview:
        preview_mode(args.preview, args.date_prefix, args.recursive)
    elif args.apply:
        apply_mode(args.apply, args.date_prefix, args.recursive, args.clean_empty)
    elif args.undo:
        # If undo is True (no arg), use None; otherwise use the provided path
        log_file = None if args.undo is True else args.undo
        undo_mode(log_file)
    elif args.dry_run:
        dry_run_mode(args.dry_run, args.date_prefix, args.recursive)


if __name__ == '__main__':
    main()
