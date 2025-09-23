# Data Synchronization Script

This directory contains a Python script for synchronizing data between your thumb drive and network storage using rsync.

## Files

- `sync_data.py` - Main Python script that handles synchronization
- `sync_config.json` - Configuration file (auto-generated on first run)
- `logs/` - Directory containing synchronization logs

## Quick Start

### Basic Usage

```bash
# List all configured sync pairs
python3 sync_data.py --list

# Preview changes (dry run)
python3 sync_data.py --dry-run

# Perform actual synchronization
python3 sync_data.py

# Sync only a specific pair
python3 sync_data.py --pair data_mean_images_to_local

# Use checksum comparison instead of timestamps
python3 sync_data.py --checksum --dry-run
```

## Configuration

The script uses a JSON configuration file (`sync_config.json`) that is automatically created on first run. You can edit this file to customize:

- Source and destination paths
- rsync options for each sync pair
- Global exclude patterns
- Enable/disable specific sync pairs

### Default Configuration

The script automatically detects your system configuration and creates sync pairs for:

**Data Directories** (bidirectional sync):
- `mean_images`
- `sleap_flowtank_under_1`, `sleap_flowtank_under_3`
- `sleap_flowtank_side_1`, `sleap_flowtank_side_3`
- `syncing_scripts`
- `matlab_data`

**Video Directories**:
- `processed_video` (bidirectional sync)
- `raw` (one-way sync: network → thumb drive only)

The script prioritizes network paths (`/mnt/schooling_data/` and `/mnt/schooling_video/`) over local paths when available.

### Adding New Sync Pairs

Edit `sync_config.json` and add new entries to the `sync_pairs` array:

```json
{
  "name": "my_new_sync",
  "source": "/path/to/source",
  "destination": "/path/to/destination",
  "enabled": true,
  "rsync_options": ["-av", "--delete", "--progress"]
}
```

## Features

- **Automatic Path Detection**: Prioritizes network paths over local paths
- **Bidirectional Sync**: Two-way synchronization with controlled deletion policies
- **One-way Sync**: Network-to-thumb-drive only sync for raw video files
- **Dry Run Mode**: Preview changes before making them
- **Checksum Comparison**: Optional checksum-based file comparison
- **Logging**: Detailed logs with timestamps
- **Error Handling**: Robust error handling and validation
- **Flexible Configuration**: JSON-based configuration system
- **Selective Sync**: Sync individual pairs or all pairs
- **Progress Display**: Real-time progress information via rsync
- **Directory Validation**: Warns about unsynced directories on thumb drive

## rsync Options

The script uses these default rsync options:
- `-a`: Archive mode (preserves permissions, timestamps, etc.)
- `-v`: Verbose output
- `--progress`: Show progress during transfer
- `--no-perms`: Skip permission preservation (avoids network filesystem issues)
- `--no-group`: Skip group ownership preservation
- `--delete`: Remove files from destination that don't exist in source (for local→thumb sync)
- `--checksum`: Use checksum comparison instead of timestamps (when `--checksum` flag is used)

## Exclude Patterns

The following patterns are excluded by default:
- `*.tmp`
- `*.log`
- `.DS_Store`
- `Thumbs.db`
- `__pycache__`
- `*.pyc`

## Logs

Synchronization logs are stored in the `logs/` directory with timestamps in the filename format: `sync_YYYYMMDD_HHMMSS.log`

## Requirements

- Python 3.6+
- rsync command-line tool
- Appropriate read/write permissions for source and destination paths
