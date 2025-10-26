#!/usr/bin/env python3
"""
Mac Backup Script using rsync

This script backs up the entire /Users/mmchenry folder to an external drive
called "Mac Backup" in a folder called "Backup".
"""

import os
import sys
import subprocess
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Tuple


class MacBackupManager:
    def __init__(self, dry_run: bool = False, verbose: bool = False, checksum_mode: bool = False):
        """Initialize the MacBackupManager."""
        self.dry_run = dry_run
        self.verbose = verbose
        self.checksum_mode = checksum_mode
        
        # Source and destination paths
        self.source_path = "/Users/mmchenry"
        self.backup_drive_name = "Mac Backup"
        self.backup_folder = "Backup MacPro"
        self.destination_path = None
        
        # Setup logging
        self.setup_logging()
        
        # Find the backup drive
        self.find_backup_drive()
    
    def setup_logging(self):
        """Setup logging configuration."""
        log_dir = Path.cwd() / "logs"
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"mac_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Mac Backup Manager initialized. Log file: {log_file}")
    
    def find_backup_drive(self):
        """Find the Mac Backup drive and set the destination path."""
        # Check /Volumes for mounted drives
        volumes_path = Path("/Volumes")
        
        if not volumes_path.exists():
            self.logger.error("Cannot access /Volumes directory")
            sys.exit(1)
        
        # Look for the Mac Backup drive
        backup_drive_path = volumes_path / self.backup_drive_name
        
        if not backup_drive_path.exists():
            self.logger.error(f"Backup drive '{self.backup_drive_name}' not found in /Volumes")
            self.logger.info("Available drives:")
            for volume in volumes_path.iterdir():
                if volume.is_dir():
                    self.logger.info(f"  - {volume.name}")
            sys.exit(1)
        
        # Set the full destination path
        self.destination_path = backup_drive_path / self.backup_folder
        
        self.logger.info(f"Found backup drive: {backup_drive_path}")
        self.logger.info(f"Destination path: {self.destination_path}")
    
    def validate_paths(self) -> Tuple[bool, str]:
        """Validate that source and destination paths exist and are accessible."""
        source_path = Path(self.source_path)
        
        if not source_path.exists():
            return False, f"Source path does not exist: {self.source_path}"
        
        if not source_path.is_dir():
            return False, f"Source path is not a directory: {self.source_path}"
        
        # Create destination directory if it doesn't exist
        dest_path = Path(self.destination_path)
        if not dest_path.exists():
            try:
                dest_path.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created destination directory: {dest_path}")
            except Exception as e:
                return False, f"Cannot create destination directory: {e}"
        
        return True, "OK"
    
    def build_rsync_command(self) -> list:
        """Build the rsync command with appropriate options."""
        cmd = ["rsync"]
        
        # Basic rsync options
        cmd.extend([
            "-av",                    # Archive mode, verbose
            "--progress",            # Show progress
            "--delete",              # Delete files in destination that don't exist in source
            "--delete-excluded",     # Delete excluded files from destination
            "--exclude-from=-"       # Read exclude patterns from stdin
        ])
        
        # Add checksum option if enabled
        if self.checksum_mode:
            cmd.append("--checksum")
        
        # Add dry run option
        if self.dry_run:
            cmd.append("--dry-run")
        
        # Exclude patterns for Mac backup
        exclude_patterns = [
            # System files and caches
            ".DS_Store",
            ".Trash",
            ".Spotlight-V100",
            ".fseventsd",
            ".TemporaryItems",
            ".VolumeIcon.icns",
            ".com.apple.timemachine.donotpresent",
            
            # Application caches and temporary files
            "Library/Caches/*",
            "Library/Application Support/CrashReporter/*",
            "Library/Logs/*",
            "Library/Preferences/com.apple.LaunchServices*",
            
            # Browser caches (optional - remove if you want to backup browser data)
            "Library/Application Support/Google/Chrome/Default/Cache/*",
            "Library/Application Support/Firefox/Profiles/*/cache2/*",
            "Library/Application Support/Safari/LocalStorage/*",
            
            # Development and build artifacts
            "node_modules",
            "__pycache__",
            "*.pyc",
            ".git",
            ".svn",
            "build",
            "dist",
            "*.log",
            "*.tmp",
            
            # Large media files that might not need backup (optional)
            # Uncomment the following lines if you don't want to backup these:
            # "Movies/*",
            # "Music/*",
            # "Pictures/*",
            
            # Virtual machines and large files
            "*.dmg",
            "*.iso",
            "*.vmdk",
            "*.vdi",
            
            # Time Machine backups (if any)
            "Backups.backupdb"
        ]
        
        # Add source and destination
        cmd.extend([f"{self.source_path}/", str(self.destination_path)])
        
        return cmd, exclude_patterns
    
    def run_backup(self) -> Tuple[bool, str]:
        """Execute the backup using rsync."""
        cmd, exclude_patterns = self.build_rsync_command()
        
        self.logger.info(f"Running backup command: {' '.join(cmd)}")
        self.logger.info(f"Excluding patterns: {len(exclude_patterns)} patterns")
        
        try:
            # Prepare exclude patterns for stdin
            exclude_input = '\n'.join(exclude_patterns)
            
            result = subprocess.run(
                cmd,
                input=exclude_input,
                capture_output=True,
                text=True,
                check=True
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\nStderr: {result.stderr}"
            
            return True, output
            
        except subprocess.CalledProcessError as e:
            error_msg = f"rsync failed with return code {e.returncode}: {e.stderr}"
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error running rsync: {e}"
            return False, error_msg
    
    def backup(self) -> bool:
        """Perform the backup operation."""
        self.logger.info("Starting Mac backup process")
        
        if self.dry_run:
            self.logger.info("DRY RUN MODE - No actual changes will be made")
        
        # Validate paths
        is_valid, error_msg = self.validate_paths()
        if not is_valid:
            self.logger.error(f"Validation failed: {error_msg}")
            return False
        
        # Run backup
        success, output = self.run_backup()
        
        if success:
            self.logger.info("Backup completed successfully")
            if output.strip() and self.verbose:
                self.logger.info(f"Output: {output}")
        else:
            self.logger.error(f"Backup failed: {output}")
        
        return success
    
    def show_backup_info(self):
        """Show information about the backup configuration."""
        print("\nMac Backup Configuration:")
        print("=" * 50)
        print(f"Source: {self.source_path}")
        print(f"Destination: {self.destination_path}")
        print(f"Backup Drive: {self.backup_drive_name}")
        print(f"Dry Run: {self.dry_run}")
        print(f"Verbose: {self.verbose}")
        print(f"Checksum Mode: {self.checksum_mode}")
        mode = "checksum" if self.checksum_mode else "timestamp"
        print(f"File Comparison: {mode}")
        print()


def main():
    """Main function to handle command line arguments and execute backup."""
    parser = argparse.ArgumentParser(description="Backup /Users/mmchenry to Mac Backup drive")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Preview changes without making them")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Show detailed output")
    parser.add_argument("--checksum", action="store_true", 
                       help="Use checksum comparison instead of timestamps for file comparison")
    parser.add_argument("--info", action="store_true", 
                       help="Show backup configuration information")
    
    args = parser.parse_args()
    
    # Create backup manager
    backup_manager = MacBackupManager(dry_run=args.dry_run, verbose=args.verbose, checksum_mode=args.checksum)
    
    if args.info:
        backup_manager.show_backup_info()
        return
    
    # Perform backup
    success = backup_manager.backup()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
