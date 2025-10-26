# Mac Backup Script Documentation

## Overview

The `sync_mac.py` script provides a comprehensive backup solution for your Mac, using rsync to efficiently backup your entire `/Users/mmchenry` folder to an external drive called "Mac Backup" in a folder called "Backup MacPro".

## Features

- **Complete User Backup**: Backs up your entire user directory including documents, applications, settings, and more
- **Intelligent Exclusions**: Automatically excludes system caches, temporary files, and other unnecessary data
- **Progress Monitoring**: Shows real-time progress during backup operations
- **Dry Run Mode**: Preview what will be backed up without making actual changes
- **Comprehensive Logging**: Detailed logs saved to `logs/` directory
- **Error Handling**: Robust error handling with clear error messages

## Prerequisites

1. **External Drive**: An external drive named "Mac Backup" must be connected and mounted
2. **Python 3**: The script requires Python 3.6 or later
3. **rsync**: rsync is included with macOS by default

## Setup

1. **Connect External Drive**: 
   - Connect your external drive to your Mac
   - Rename it to "Mac Backup" (if not already named)
   - Ensure it's mounted and accessible at `/Volumes/Mac Backup`

2. **Make Script Executable**:
   ```bash
   chmod +x sync_mac.py
   ```

## Usage

### Basic Backup
```bash
python3 sync_mac.py
```

### Preview Changes (Dry Run)
```bash
python3 sync_mac.py --dry-run
```

### Verbose Output
```bash
python3 sync_mac.py --verbose
```

### Show Configuration Info
```bash
python3 sync_mac.py --info
```

### Use Checksum Comparison
```bash
python3 sync_mac.py --checksum
```

### Combined Options
```bash
python3 sync_mac.py --dry-run --verbose --checksum
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `--dry-run` | Preview changes without making them |
| `--verbose`, `-v` | Show detailed output including rsync details |
| `--checksum` | Use checksum comparison instead of timestamps for file comparison |
| `--info` | Display backup configuration information |

## What Gets Backed Up

The script backs up your entire `/Users/mmchenry` directory, including:

- **Documents**: All files in Documents folder
- **Desktop**: Desktop files and folders
- **Downloads**: Downloaded files
- **Pictures**: Photos and images
- **Movies**: Video files
- **Music**: Audio files
- **Applications**: User-installed applications
- **Library**: Application settings, preferences, and data
- **Code Projects**: Development projects and repositories

## What Gets Excluded

To optimize backup speed and storage usage, the following are automatically excluded:

### System Files
- `.DS_Store` files
- `.Trash` folder
- `.Spotlight-V100` (Spotlight index)
- `.fseventsd` (file system events)
- `.TemporaryItems`

### Application Caches
- `Library/Caches/*`
- `Library/Application Support/CrashReporter/*`
- `Library/Logs/*`

### Browser Data (Optional)
- Chrome cache files
- Firefox cache files
- Safari local storage

### Development Artifacts
- `node_modules` folders
- `__pycache__` folders
- `.git` repositories
- Build and distribution folders
- Log files and temporary files

### Large Files
- Disk images (`.dmg`)
- ISO files
- Virtual machine files
- Time Machine backups

## Backup Process

1. **Drive Detection**: Script automatically finds the "Mac Backup" drive
2. **Path Validation**: Verifies source and destination paths exist
3. **Directory Creation**: Creates "Backup MacPro" folder on external drive if needed
4. **File Comparison**: Uses timestamps by default, or checksums if `--checksum` flag is used
5. **rsync Execution**: Performs incremental backup using rsync
6. **Logging**: Records all operations to timestamped log files

## Checksum vs Timestamp Comparison

By default, the script uses **timestamp comparison** to determine which files need to be synced. This is faster and suitable for most use cases.

### Using Timestamps (Default)
- Fast comparison based on file modification dates
- Good for regular backups
- rsync only transfers files that are newer in the source

### Using Checksums (`--checksum` flag)
- Slower but more accurate comparison using file checksums
- Useful when:
  - Files may have been modified without timestamp changes
  - You want to ensure absolute file content synchronization
  - Working across different file systems that may have timestamp issues
- rsync compares actual file contents, not just dates

**When to use checksum mode:**
- After moving files between systems
- When verifying backup integrity
- If you suspect timestamp issues
- For critical data where absolute accuracy is required

## Log Files

Log files are saved in the `logs/` directory with timestamps:
```
logs/mac_backup_20241201_143022.log
```

Logs include:
- Backup start/end times
- File transfer progress
- Error messages
- Configuration details

## Troubleshooting

### "Backup drive 'Mac Backup' not found"
- Ensure external drive is connected and mounted
- Check that drive is named exactly "Mac Backup"
- Run `ls /Volumes` to see available drives

### Permission Errors
- Ensure you have read access to `/Users/mmchenry`
- Check that external drive has write permissions
- Run script with appropriate user privileges

### rsync Errors
- Check available disk space on external drive
- Verify external drive is not corrupted
- Check log files for detailed error messages

### Large Backup Size
- Use `--dry-run` first to estimate backup size
- Consider excluding additional folders by modifying exclude patterns
- Ensure external drive has sufficient free space

## Customization

### Modifying Exclude Patterns

To customize what gets excluded, edit the `exclude_patterns` list in the `build_rsync_command()` method:

```python
exclude_patterns = [
    # Add your custom exclusions here
    "Documents/LargeFiles/*",
    "Movies/HomeVideos/*",
    # ... existing patterns
]
```

### Changing Backup Location

To backup to a different drive or folder, modify these variables in the `__init__` method:

```python
self.backup_drive_name = "YourDriveName"
self.backup_folder = "YourBackupFolder"
```

## Safety Features

- **Dry Run Mode**: Always test with `--dry-run` first
- **Incremental Backup**: Only transfers changed files
- **Delete Protection**: Uses `--delete` carefully to maintain sync
- **Comprehensive Logging**: Full audit trail of all operations
- **Error Handling**: Graceful failure with clear error messages

## Best Practices

1. **Regular Backups**: Run backups regularly to keep data current
2. **Test First**: Always use `--dry-run` before actual backups
3. **Monitor Logs**: Check log files for any issues
4. **Verify Drives**: Ensure external drive is healthy and has space
5. **Update Exclusions**: Review and update exclude patterns as needed

## Example Workflow

```bash
# 1. Check configuration
python3 sync_mac.py --info

# 2. Preview what will be backed up
python3 sync_mac.py --dry-run --verbose

# 3. Run actual backup
python3 sync_mac.py --verbose

# 4. Check logs if needed
ls logs/
tail logs/mac_backup_*.log
```

## Support

For issues or questions:
1. Check log files in `logs/` directory
2. Run with `--verbose` for detailed output
3. Use `--dry-run` to test changes safely
4. Verify external drive is properly mounted and accessible
