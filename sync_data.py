#!/usr/bin/env python3
"""
Data Synchronization Script using rsync

This script synchronizes data between a remote volume and local storage locations
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


def setup_sync_directories(data_dirs: List[str], video_dirs: List[str], one_way_video_dirs: List[str], 
                          remote_data_base: str = "/media/mmchenry/ThumbDrive/",
                          remote_video_base: str = "/media/mmchenry/ThumbDrive/") -> None:
    """Create necessary directories on remote volumes and check for unsynced directories."""
    
    # Create data directories
    for dir_name in data_dirs:
        dir_path = os.path.join(remote_data_base, dir_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {dir_path}")

    # Create video directories
    for dir_name in video_dirs:
        dir_path = os.path.join(remote_video_base, dir_name) 
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {dir_path}")

    # Create one-way video directories
    for dir_name in one_way_video_dirs:
        dir_path = os.path.join(remote_video_base, dir_name) 
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {dir_path}")

    # Check for directories in remote bases that are not included in sync lists
    check_unsynced_directories(data_dirs, video_dirs, one_way_video_dirs, remote_data_base, remote_video_base)


def check_unsynced_directories(data_dirs: List[str], video_dirs: List[str], one_way_video_dirs: List[str],
                              remote_data_base: str = "/media/mmchenry/ThumbDrive/",
                              remote_video_base: str = "/media/mmchenry/ThumbDrive/") -> None:
    """Check for directories in remote bases that are not in data_dirs or video_dirs."""
    
    # Check data remote base
    if os.path.exists(remote_data_base):
        all_synced_dirs = set(data_dirs)
        remote_dirs = []
        
        try:
            remote_dirs = [d for d in os.listdir(remote_data_base) 
                         if os.path.isdir(os.path.join(remote_data_base, d))]
        except PermissionError:
            print(f"Warning: Cannot access {remote_data_base} to check for unsynced directories")
        else:
            unsynced_dirs = [d for d in remote_dirs if d not in all_synced_dirs]
            
            if unsynced_dirs:
                print("\n" + "="*60)
                print("WARNING: Found directories in remote_data_base that are NOT included in sync:")
                print("="*60)
                for dir_name in unsynced_dirs:
                    dir_path = os.path.join(remote_data_base, dir_name)
                    print(f"  - {dir_name} ({dir_path})")
                print("\nThese directories will NOT be synchronized.")
                print("Add them to 'data_dirs' if they should be synced.")
                print("="*60 + "\n")
            else:
                print("✓ All directories in remote_data_base are included in sync configuration")
    
    # Check video remote base
    if os.path.exists(remote_video_base):
        all_synced_dirs = set(video_dirs + one_way_video_dirs)
        remote_dirs = []
        
        try:
            remote_dirs = [d for d in os.listdir(remote_video_base) 
                         if os.path.isdir(os.path.join(remote_video_base, d))]
        except PermissionError:
            print(f"Warning: Cannot access {remote_video_base} to check for unsynced directories")
        else:
            unsynced_dirs = [d for d in remote_dirs if d not in all_synced_dirs]
            
            if unsynced_dirs:
                print("\n" + "="*60)
                print("WARNING: Found directories in remote_video_base that are NOT included in sync:")
                print("="*60)
                for dir_name in unsynced_dirs:
                    dir_path = os.path.join(remote_video_base, dir_name)
                    print(f"  - {dir_name} ({dir_path})")
                print("\nThese directories will NOT be synchronized.")
                print("Add them to 'video_dirs' or 'one_way_video_dirs' if they should be synced.")
                print("="*60 + "\n")
            else:
                print("✓ All directories in remote_video_base are included in sync configuration")


class DataSyncManager:
    def __init__(self, config_file: str = None, checksum_mode: bool = False):
        """Initialize the DataSyncManager with configuration."""
        self.config_file = config_file or "sync_config.json"
        self.checksum_mode = checksum_mode
        
        # Default values - will be overridden by create_sync_manager
        self.local_data_root = "/home/mmchenry/Documents/catfish_kinematics"
        self.local_video_root = "/home/mmchenry/Documents/catfish_kinematics"
        self.data_dirs = []
        self.video_dirs = []
        self.one_way_video_dirs = []
        self.remote_data_base = "/media/mmchenry/ThumbDrive/"
        self.remote_video_base = "/media/mmchenry/ThumbDrive/"
        
        # Logging will be set up after remote paths are configured
        self.logger = None
    
    def setup_logging(self):
        """Setup logging configuration."""
        # Try to use remote_data_base for logs, fall back to current directory if not available
        log_dir = None
        if os.path.exists(self.remote_data_base):
            log_dir = Path(self.remote_data_base) / "syncing_scripts" / "logs"
        else:
            # Fall back to current directory for logs
            log_dir = Path.cwd() / "logs"
        
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
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
            self.logger.info(f"Logging initialized. Log file: {log_file}")
        except Exception as e:
            # If we can't create log directory, just use console logging
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[logging.StreamHandler(sys.stdout)]
            )
            self.logger = logging.getLogger(__name__)
            self.logger.warning(f"Could not create log directory {log_dir}: {e}. Using console logging only.")
    
    def load_config(self):
        """Load synchronization configuration from JSON file."""
        # Use remote_data_base for config file location
        config_path = Path(self.remote_data_base) / "syncing_scripts" / self.config_file
        
        # Always generate sync pairs dynamically based on detected paths
        # This ensures the script works correctly on different systems
        sync_pairs = []
        
        # Sync data directories bidirectionally (remote <-> local)
        for data_dir in self.data_dirs:
            # Remote -> Local (NO deletion - safe sync)
            rsync_options_safe = ["-av", "--progress", "--no-perms", "--no-group"]
            if self.checksum_mode:
                rsync_options_safe.append("--checksum")
            
            # Local -> Remote (WITH deletion - source deletions propagate)
            rsync_options_with_delete = ["-av", "--delete", "--progress", "--no-perms", "--no-group"]
            if self.checksum_mode:
                rsync_options_with_delete.append("--checksum")
            
            # Normalize paths to avoid double slashes
            remote_base = self.remote_data_base.rstrip("/")
            local_base = self.local_data_root.rstrip("/")
            
            # Remote -> Local (safe sync, no deletion)
            sync_pairs.append({
                "name": f"data_{data_dir}_to_local",
                "source": f"{remote_base}/{data_dir}",
                "destination": f"{local_base}/{data_dir}",
                "enabled": True,
                "rsync_options": rsync_options_safe
            })
            
            # Local -> Remote (with deletion - source deletions propagate)
            sync_pairs.append({
                "name": f"data_{data_dir}_to_remote",
                "source": f"{local_base}/{data_dir}",
                "destination": f"{remote_base}/{data_dir}",
                "enabled": True,
                "rsync_options": rsync_options_with_delete
            })
        
        # Sync video directories bidirectionally (remote <-> local)
        for video_dir in self.video_dirs:
            # Remote -> Local (NO deletion - safe sync)
            rsync_options_safe = ["-av", "--progress", "--no-perms", "--no-group"]
            if self.checksum_mode:
                rsync_options_safe.append("--checksum")
            
            # Local -> Remote (WITH deletion - source deletions propagate)
            rsync_options_with_delete = ["-av", "--delete", "--progress", "--no-perms", "--no-group"]
            if self.checksum_mode:
                rsync_options_with_delete.append("--checksum")
            
            # Normalize paths to avoid double slashes
            remote_base = self.remote_video_base.rstrip("/")
            local_base = self.local_video_root.rstrip("/")
            
            # Remote -> Local (safe sync, no deletion)
            sync_pairs.append({
                "name": f"video_{video_dir}_to_local",
                "source": f"{remote_base}/{video_dir}",
                "destination": f"{local_base}/{video_dir}",
                "enabled": True,
                "rsync_options": rsync_options_safe
            })
            
            # Local -> Remote (with deletion - source deletions propagate)
            sync_pairs.append({
                "name": f"video_{video_dir}_to_remote",
                "source": f"{local_base}/{video_dir}",
                "destination": f"{remote_base}/{video_dir}",
                "enabled": True,
                "rsync_options": rsync_options_with_delete
            })
        
        # Sync one-way video directories (local -> remote only)
        for video_dir in self.one_way_video_dirs:
            rsync_options = ["-av", "--progress", "--no-perms", "--no-group"]  # No --delete for one-way sync
            if self.checksum_mode:
                rsync_options.append("--checksum")
            # Normalize paths to avoid double slashes
            remote_base = self.remote_video_base.rstrip("/")
            local_base = self.local_video_root.rstrip("/")
            sync_pairs.append({
                "name": f"video_{video_dir}_oneway",
                "source": f"{local_base}/{video_dir}",
                "destination": f"{remote_base}/{video_dir}",
                "enabled": True,
                "rsync_options": rsync_options,
                "description": "One-way sync: local -> remote only"
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
        config_path = Path(self.remote_data_base) / "syncing_scripts" / self.config_file
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
        self.logger.info(f"Configuration updated with detected paths:")
        self.logger.info(f"  local_data_root={self.local_data_root}")
        self.logger.info(f"  local_video_root={self.local_video_root}")
        self.logger.info(f"  remote_data_base={self.remote_data_base}")
        self.logger.info(f"  remote_video_base={self.remote_video_base}")
        self.logger.info(f"Sync mode: {mode} comparison")
    
    def save_config(self):
        """Save current configuration to JSON file."""
        config_path = Path(self.remote_data_base) / "syncing_scripts" / self.config_file
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
        
        # Add verbose output to show what files are being checked/transferred
        if "-v" not in rsync_options and "--verbose" not in rsync_options:
            cmd.append("-v")
        
        # Add stats to show detailed transfer statistics
        if "--stats" not in rsync_options:
            cmd.append("--stats")
        
        # Add itemize-changes to show detailed file information (what changed)
        if "--itemize-changes" not in rsync_options:
            cmd.append("--itemize-changes")
        
        # Add exclude patterns
        for pattern in self.config.get("exclude_patterns", []):
            cmd.extend(["--exclude", pattern])
        
        # Add dry run option
        if dry_run:
            cmd.append("--dry-run")
        
        # Normalize paths to avoid double slashes
        source_normalized = source.rstrip("/") + "/"
        destination_normalized = destination.rstrip("/")
        
        # Add source and destination
        cmd.extend([source_normalized, destination_normalized])
        
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
            # Parse output to show what happened
            output_lines = output.strip().split('\n')
            
            # Extract file transfer lines (itemize-changes output)
            file_changes = []
            stats_section = False
            stats_lines = []
            
            for line in output_lines:
                line = line.strip()
                if not line:
                    continue
                # Itemize-changes lines start with indicators like >f, >d, etc.
                if line and (line.startswith('>') or line.startswith('<') or line.startswith('c') or line.startswith('h') or line.startswith('*')):
                    file_changes.append(line)
                # Stats section starts with "Number of files"
                elif "Number of files" in line or "Total file size" in line or "Total transferred file size" in line:
                    stats_section = True
                    stats_lines.append(line)
                elif stats_section and (":" in line or line.startswith("sent ") or line.startswith("total size")):
                    stats_lines.append(line)
            
            if file_changes:
                self.logger.info(f"Sync completed successfully for '{name}' - Files changed:")
                for line in file_changes[:20]:  # Show first 20 changes
                    self.logger.info(f"  {line}")
                if len(file_changes) > 20:
                    self.logger.info(f"  ... and {len(file_changes) - 20} more files")
            elif stats_lines:
                # Show stats if available
                self.logger.info(f"Sync completed successfully for '{name}' - Statistics:")
                for line in stats_lines[:10]:  # Show first 10 stat lines
                    self.logger.info(f"  {line}")
            else:
                # Fallback to basic summary
                summary_lines = [line for line in output_lines if line.startswith('sent ') or line.startswith('total size')]
                if summary_lines:
                    self.logger.info(f"Sync completed successfully for '{name}' - No files needed transfer (already in sync)")
                    for line in summary_lines:
                        self.logger.info(f"  {line}")
                else:
                    self.logger.info(f"Sync completed successfully for '{name}' - No files needed transfer (already in sync)")
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
    
    def sync_pair_by_name(self, pair_name: str, dry_run: bool = False) -> bool:
        """Synchronize a specific pair by name."""
        for pair in self.config["sync_pairs"]:
            if pair["name"] == pair_name:
                return self.sync_pair(pair, dry_run)
        
        self.logger.error(f"Sync pair '{pair_name}' not found")
        return False


def create_sync_manager(local_data_root: str, local_video_root: str, data_dirs: List[str], 
                       video_dirs: List[str], one_way_video_dirs: List[str],
                       remote_data_base: str = "/media/mmchenry/ThumbDrive/",
                       remote_video_base: str = "/media/mmchenry/ThumbDrive/",
                       checksum_mode: bool = False) -> DataSyncManager:
    """Create and configure a DataSyncManager with the provided parameters."""
    
    print(f"Local data root: {local_data_root}")
    print(f"Local video root: {local_video_root}")
    print(f"Remote data base: {remote_data_base}")
    print(f"Remote video base: {remote_video_base}")
    
    # Setup directories
    setup_sync_directories(data_dirs, video_dirs, one_way_video_dirs, remote_data_base, remote_video_base)
    
    # Create sync manager with custom configuration
    sync_manager = DataSyncManager(checksum_mode=checksum_mode)
    sync_manager.local_data_root = local_data_root
    sync_manager.local_video_root = local_video_root
    sync_manager.data_dirs = data_dirs
    sync_manager.video_dirs = video_dirs
    sync_manager.one_way_video_dirs = one_way_video_dirs
    sync_manager.remote_data_base = remote_data_base
    sync_manager.remote_video_base = remote_video_base
    
    # Setup logging now that remote paths are configured
    sync_manager.setup_logging()
    
    # Reload configuration with new parameters
    sync_manager.load_config()
    
    return sync_manager


def main():
    """Main function to handle command line arguments and execute sync."""
    parser = argparse.ArgumentParser(description="Synchronize data between remote volume and local storage")
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
    parser.add_argument("--remote-data-base", type=str, 
                       help="Remote base path for data directories")
    parser.add_argument("--remote-video-base", type=str, 
                       help="Remote base path for video directories")
    
    args = parser.parse_args()
    
    # Default configuration - can be overridden by calling create_sync_manager directly
    if os.path.exists("/mnt/schooling_data"):
        local_data_root = "/mnt/schooling_data/catfish_flowtank_kinematics"
        local_video_root = "/mnt/schooling_video/catfish_kinematics"
        print("✓ Using NETWORK paths (prioritized)")
        
    elif os.path.exists("/home/mmchenry/Documents/catfish_kinematics"):
        local_data_root = "/home/mmchenry/Documents/catfish_kinematics"
        local_video_root = "/home/mmchenry/Documents/catfish_kinematics"
        print("⚠️  Using LOCAL paths (network not available)")
    else:
        raise RuntimeError("Could not find directory to sync with.")

    # Default directory lists
    data_dirs = [
        "mean_images",
        "sleap_flowtank_under_1",
        "sleap_flowtank_under_3",
        "sleap_flowtank_side_1",
        "sleap_flowtank_side_3",
        "syncing_scripts",
        "matlab_data"
    ]

    video_dirs = [
        "processed_video"
    ]

    one_way_video_dirs = [
        "raw"
    ]
    
    # Set default remote paths if not provided via command line
    remote_data_base = args.remote_data_base or "/media/mmchenry/ThumbDrive/"
    remote_video_base = args.remote_video_base or "/media/mmchenry/ThumbDrive/"
    
    # Initialize sync manager
    sync_manager = create_sync_manager(
        local_data_root=local_data_root,
        local_video_root=local_video_root,
        data_dirs=data_dirs,
        video_dirs=video_dirs,
        one_way_video_dirs=one_way_video_dirs,
        remote_data_base=remote_data_base,
        remote_video_base=remote_video_base,
        checksum_mode=args.checksum
    )
    
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