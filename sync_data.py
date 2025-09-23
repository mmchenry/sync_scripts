#!/usr/bin/env python3
"""
Data Synchronization Script using rsync

This script synchronizes data between a thumb drive and network storage locations
using rsync for efficient file transfer and synchronization.
"""

import os
import sys
import subprocess
import logging
import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

if os.path.exists("/mnt/schooling_data"):
    data_root = "/mnt/schooling_data/catfish_flowtank_kinematics"
    video_root = "/mnt/schooling_video/catfish_kinematics"
    print("✓ Using NETWORK paths (prioritized)")
    
elif os.path.exists("/home/mmchenry/Documents/catfish_kinematics"):
    data_root = "/home/mmchenry/Documents/catfish_kinematics"
    video_root = "/home/mmchenry/Documents/catfish_kinematics"
    print("⚠️  Using LOCAL paths (network not available)")
else:
    raise RuntimeError("Could not find directory to sync with.")

print(f"Data root: {data_root}")
print(f"Video root: {video_root}")

thumb_root = "/media/mmchenry/ThumbDrive/catfish_flowtank_kinematics"

checksum_mode = True

# List of data directories to sync
data_dirs = [
    "mean_images",
    "sleap_flowtank_under_1",
    "sleap_flowtank_under_3",
    "sleap_flowtank_side_1",
    "sleap_flowtank_side_3",
    "syncing_scripts",
    "matlab_data"
]

# Verify thumb drive directories exist
for dir_name in data_dirs:
    dir_path = os.path.join(thumb_root, dir_name)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"Created directory: {dir_path}")


# List of video directories to sync (bidirectional)
video_dirs = [
    "processed_video"
]

# List of one-way video directories (network -> thumb drive only)
one_way_video_dirs = [
    "raw"
]

# Verify thumb drive directories exist (directly under /media/mmchenry/ThumbDrive/)
thumb_drive_base = "/media/mmchenry/ThumbDrive/"

# Create data directories
for dir_name in data_dirs:
    dir_path = os.path.join(thumb_drive_base, dir_name)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"Created directory: {dir_path}")

# Create video directories
for dir_name in video_dirs:
    dir_path = os.path.join(thumb_drive_base, dir_name) 
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"Created directory: {dir_path}")

# Create one-way video directories
for dir_name in one_way_video_dirs:
    dir_path = os.path.join(thumb_drive_base, dir_name) 
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"Created directory: {dir_path}")

# Check for directories in thumb_drive_base that are not included in sync lists
def check_unsynced_directories():
    """Check for directories in thumb_drive_base that are not in data_dirs or video_dirs."""
    if not os.path.exists(thumb_drive_base):
        return
    
    # Include one-way video directories in the check
    all_synced_dirs = set(data_dirs + video_dirs + one_way_video_dirs)
    thumb_dirs = []
    
    try:
        thumb_dirs = [d for d in os.listdir(thumb_drive_base) 
                     if os.path.isdir(os.path.join(thumb_drive_base, d))]
    except PermissionError:
        print(f"Warning: Cannot access {thumb_drive_base} to check for unsynced directories")
        return
    
    unsynced_dirs = [d for d in thumb_dirs if d not in all_synced_dirs]
    
    if unsynced_dirs:
        print("\n" + "="*60)
        print("WARNING: Found directories in thumb_drive_base that are NOT included in sync:")
        print("="*60)
        for dir_name in unsynced_dirs:
            dir_path = os.path.join(thumb_drive_base, dir_name)
            print(f"  - {dir_name} ({dir_path})")
        print("\nThese directories will NOT be synchronized.")
        print("Add them to either 'data_dirs', 'video_dirs', or 'one_way_video_dirs' if they should be synced.")
        print("="*60 + "\n")
    else:
        print("✓ All directories in thumb_drive_base are included in sync configuration")

# Run the check
check_unsynced_directories()
    
print(f"Data root: {data_root}")
print(f"Video root: {video_root}")
print(f"Thumb root: {thumb_root}")

class DataSyncManager:
    def __init__(self, config_file: str = None, checksum_mode: bool = False):
        """Initialize the DataSyncManager with configuration."""
        self.thumb_drive_path = "/media/mmchenry/ThumbDrive/"
        self.config_file = config_file or "sync_config.json"
        self.checksum_mode = checksum_mode
        self.setup_logging()
        self.load_config()
    
    def setup_logging(self):
        """Setup logging configuration."""
        log_dir = Path(self.thumb_drive_path) / "syncing_scripts" / "logs"
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self):
        """Load synchronization configuration from JSON file."""
        config_path = Path(self.thumb_drive_path) / "syncing_scripts" / self.config_file
        
        # Always generate sync pairs dynamically based on detected paths
        # This ensures the script works correctly on different systems
        sync_pairs = []
        
        # Sync data directories bidirectionally (thumb drive <-> local)
        for data_dir in data_dirs:
            # Thumb drive -> Local (NO deletion - safe sync)
            rsync_options_safe = ["-av", "--progress", "--no-perms", "--no-group"]
            if self.checksum_mode:
                rsync_options_safe.append("--checksum")
            
            # Local -> Thumb drive (WITH deletion - source deletions propagate)
            rsync_options_with_delete = ["-av", "--delete", "--progress", "--no-perms", "--no-group"]
            if self.checksum_mode:
                rsync_options_with_delete.append("--checksum")
            
            # Thumb drive -> Local (safe sync, no deletion)
            sync_pairs.append({
                "name": f"data_{data_dir}_to_local",
                "source": f"/media/mmchenry/ThumbDrive/{data_dir}",
                "destination": f"{data_root}/{data_dir}",
                "enabled": True,
                "rsync_options": rsync_options_safe
            })
            
            # Local -> Thumb drive (with deletion - source deletions propagate)
            sync_pairs.append({
                "name": f"data_{data_dir}_to_thumb",
                "source": f"{data_root}/{data_dir}",
                "destination": f"/media/mmchenry/ThumbDrive/{data_dir}",
                "enabled": True,
                "rsync_options": rsync_options_with_delete
            })
        
        # Sync video directories bidirectionally (thumb drive <-> local)
        for video_dir in video_dirs:
            # Thumb drive -> Local (NO deletion - safe sync)
            rsync_options_safe = ["-av", "--progress", "--no-perms", "--no-group"]
            if self.checksum_mode:
                rsync_options_safe.append("--checksum")
            
            # Local -> Thumb drive (WITH deletion - source deletions propagate)
            rsync_options_with_delete = ["-av", "--delete", "--progress", "--no-perms", "--no-group"]
            if self.checksum_mode:
                rsync_options_with_delete.append("--checksum")
            
            # Thumb drive -> Local (safe sync, no deletion)
            sync_pairs.append({
                "name": f"video_{video_dir}_to_local",
                "source": f"/media/mmchenry/ThumbDrive/{video_dir}",
                "destination": f"{video_root}/{video_dir}",
                "enabled": True,
                "rsync_options": rsync_options_safe
            })
            
            # Local -> Thumb drive (with deletion - source deletions propagate)
            sync_pairs.append({
                "name": f"video_{video_dir}_to_thumb",
                "source": f"{video_root}/{video_dir}",
                "destination": f"/media/mmchenry/ThumbDrive/{video_dir}",
                "enabled": True,
                "rsync_options": rsync_options_with_delete
            })
        
        # Sync one-way video directories (network -> thumb drive only)
        for video_dir in one_way_video_dirs:
            rsync_options = ["-av", "--progress", "--no-perms", "--no-group"]  # No --delete for one-way sync
            if self.checksum_mode:
                rsync_options.append("--checksum")
            sync_pairs.append({
                "name": f"video_{video_dir}_oneway",
                "source": f"{video_root}/{video_dir}",
                "destination": f"/media/mmchenry/ThumbDrive/{video_dir}",
                "enabled": True,
                "rsync_options": rsync_options,
                "description": "One-way sync: network -> thumb drive only"
            })
        
        # Default configuration with dynamic paths
        self.config = {
            "sync_pairs": sync_pairs,
            "global_rsync_options": ["-av", "--progress"],
            "exclude_patterns": [
                "*.tmp",
                "*.log",
                ".DS_Store",
                "Thumbs.db",
                "__pycache__",
                "*.pyc"
            ]
        }
        
        # Load user overrides from config file (but don't override the paths)
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    # Only update non-path related settings
                    if "global_rsync_options" in user_config:
                        self.config["global_rsync_options"] = user_config["global_rsync_options"]
                    if "exclude_patterns" in user_config:
                        self.config["exclude_patterns"] = user_config["exclude_patterns"]
                    # Update enabled status for individual sync pairs if they exist
                    if "sync_pairs" in user_config:
                        user_pairs = {pair["name"]: pair for pair in user_config["sync_pairs"]}
                        for pair in self.config["sync_pairs"]:
                            if pair["name"] in user_pairs:
                                pair["enabled"] = user_pairs[pair["name"]].get("enabled", True)
                self.logger.info(f"Loaded user configuration from {config_path}")
            except Exception as e:
                self.logger.warning(f"Could not load config file: {e}. Using defaults.")
        
        # Always save the current configuration with detected paths
        self.save_config()
        mode = "checksum" if self.checksum_mode else "timestamp"
        self.logger.info(f"Configuration updated with detected paths: data_root={data_root}, video_root={video_root}")
        self.logger.info(f"Sync mode: {mode} comparison")
    
    def save_config(self):
        """Save current configuration to JSON file."""
        config_path = Path(self.thumb_drive_path) / "syncing_scripts" / self.config_file
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.info(f"Configuration saved to {config_path}")
        except Exception as e:
            self.logger.error(f"Could not save configuration: {e}")
    
    def validate_paths(self, source: str, destination: str) -> Tuple[bool, str]:
        """Validate that source and destination paths exist and are accessible."""
        source_path = Path(source)
        dest_path = Path(destination)
        
        if not source_path.exists():
            return False, f"Source path does not exist: {source}"
        
        if not source_path.is_dir():
            return False, f"Source path is not a directory: {source}"
        
        # Check if destination parent directory exists
        if not dest_path.parent.exists():
            try:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created destination directory: {dest_path.parent}")
            except Exception as e:
                return False, f"Cannot create destination directory: {e}"
        
        return True, "OK"
    
    def build_rsync_command(self, source: str, destination: str, 
                           rsync_options: List[str], dry_run: bool = False) -> List[str]:
        """Build the rsync command with appropriate options."""
        cmd = ["rsync"]
        
        # Add specific options for this sync pair (these already include global options)
        cmd.extend(rsync_options)
        
        # Add exclude patterns
        for pattern in self.config.get("exclude_patterns", []):
            cmd.extend(["--exclude", pattern])
        
        # Add dry run option
        if dry_run:
            cmd.append("--dry-run")
        
        # Add source and destination
        cmd.extend([f"{source}/", destination])
        
        return cmd
    
    def run_rsync(self, source: str, destination: str, rsync_options: List[str], 
                  dry_run: bool = False) -> Tuple[bool, str]:
        """Execute rsync command and return success status and output."""
        cmd = self.build_rsync_command(source, destination, rsync_options, dry_run)
        
        self.logger.info(f"Running command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd, 
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
    
    def sync_pair(self, pair: Dict, dry_run: bool = False) -> bool:
        """Synchronize a single source-destination pair."""
        name = pair["name"]
        source = pair["source"]
        destination = pair["destination"]
        rsync_options = pair.get("rsync_options", [])
        
        self.logger.info(f"Starting sync for '{name}': {source} -> {destination}")
        
        # Validate paths
        is_valid, error_msg = self.validate_paths(source, destination)
        if not is_valid:
            self.logger.error(f"Validation failed for '{name}': {error_msg}")
            return False
        
        # Run rsync
        success, output = self.run_rsync(source, destination, rsync_options, dry_run)
        
        if success:
            self.logger.info(f"Sync completed successfully for '{name}'")
            if output.strip():
                self.logger.info(f"Output: {output}")
        else:
            self.logger.error(f"Sync failed for '{name}': {output}")
        
        return success
    
    def sync_all(self, dry_run: bool = False) -> bool:
        """Synchronize all enabled sync pairs."""
        self.logger.info("Starting synchronization process")
        
        if dry_run:
            self.logger.info("DRY RUN MODE - No actual changes will be made")
        
        success_count = 0
        total_count = 0
        
        for pair in self.config["sync_pairs"]:
            if not pair.get("enabled", True):
                self.logger.info(f"Skipping disabled sync pair: {pair['name']}")
                continue
            
            total_count += 1
            if self.sync_pair(pair, dry_run):
                success_count += 1
        
        self.logger.info(f"Synchronization complete: {success_count}/{total_count} pairs successful")
        return success_count == total_count
    
    def list_sync_pairs(self):
        """List all configured sync pairs."""
        print("\nConfigured Sync Pairs:")
        print("=" * 50)
        
        for i, pair in enumerate(self.config["sync_pairs"], 1):
            status = "ENABLED" if pair.get("enabled", True) else "DISABLED"
            print(f"{i}. {pair['name']} [{status}]")
            print(f"   Source: {pair['source']}")
            print(f"   Destination: {pair['destination']}")
            print(f"   Options: {' '.join(pair.get('rsync_options', []))}")
            print()

def main():
    """Main function to handle command line arguments and execute sync."""
    parser = argparse.ArgumentParser(description="Synchronize data between thumb drive and network storage")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Preview changes without making them")
    parser.add_argument("--list", action="store_true", 
                       help="List all configured sync pairs")
    parser.add_argument("--config", type=str, 
                       help="Path to configuration file")
    parser.add_argument("--pair", type=str, 
                       help="Sync only a specific pair by name")
    parser.add_argument("--checksum", action="store_true", 
                       help="Use checksum comparison instead of timestamps for file comparison")
    
    args = parser.parse_args()
    
    # Initialize sync manager
    sync_manager = DataSyncManager(args.config, args.checksum)
    
    if args.list:
        sync_manager.list_sync_pairs()
        return
    
    if args.pair:
        # Sync specific pair
        pair_found = False
        for pair in sync_manager.config["sync_pairs"]:
            if pair["name"] == args.pair:
                pair_found = True
                sync_manager.sync_pair(pair, args.dry_run)
                break
        
        if not pair_found:
            print(f"Error: Sync pair '{args.pair}' not found")
            sys.exit(1)
    else:
        # Sync all pairs
        success = sync_manager.sync_all(args.dry_run)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
