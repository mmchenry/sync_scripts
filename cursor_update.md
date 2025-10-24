# Cursor IDE Update Guide

This guide explains how to update Cursor IDE on Linux using the provided installation script.

## Quick Update Method

### Using the Installation Script

1. **Download the latest Cursor AppImage**
   
   Visit the official Cursor download page or use the direct download link:
   ```
   https://www.cursor.com/api/download?platform=linux-x64&releaseTrack=stable
   ```
   
   Or download via command line:
   ```bash
   cd ~/Downloads
   curl -L "https://www.cursor.com/api/download?platform=linux-x64&releaseTrack=stable" -o Cursor-latest.AppImage
   ```

2. **Run the installation script**
   ```bash
   ./home/mmchenry/code/sync_scripts/update_cursor.sh
   ```

The script will automatically:
- ✓ Find the Cursor AppImage in your Downloads folder
- ✓ Install it to `~/.local/bin/cursor.appimage`
- ✓ Extract and install the application icon
- ✓ Create a launcher script at `~/.local/bin/cursor`
- ✓ Set up a desktop entry for your application menu
- ✓ Add Cursor to your PATH

## Manual Update Method

If you prefer to update manually:

1. **Download the AppImage**
   ```bash
   wget -O ~/Downloads/Cursor-latest.AppImage \
     "https://www.cursor.com/api/download?platform=linux-x64&releaseTrack=stable"
   ```

2. **Make it executable**
   ```bash
   chmod +x ~/Downloads/Cursor-*.AppImage
   ```

3. **Replace the old version**
   ```bash
   mv ~/Downloads/Cursor-*.AppImage ~/.local/bin/cursor.appimage
   ```

4. **Update the desktop database** (optional)
   ```bash
   update-desktop-database ~/.local/share/applications
   ```

## Launching Cursor

After installation or update, you can launch Cursor in multiple ways:

### Option 1: Command Line
Open a new terminal and type:
```bash
cursor
```

### Option 2: Current Terminal Session
If the command isn't found, update your PATH:
```bash
export PATH="$HOME/.local/bin:$PATH"
cursor
```

### Option 3: Applications Menu
- Log out and log back in
- Look for "Cursor AI IDE" in your applications menu
- Or press `Alt+F2` and type `cursor`

### Option 4: Direct Execution
```bash
~/.local/bin/cursor
```

## What Gets Installed

The installation script creates the following:

| File/Location | Purpose |
|---------------|---------|
| `~/.local/bin/cursor.appimage` | The main Cursor application |
| `~/.local/bin/cursor` | Launcher script for command-line access |
| `~/.local/share/applications/cursor.desktop` | Desktop entry for application menu |
| `~/.local/share/icons/cursor.png` | Application icon |
| `~/.local/share/icons/hicolor/256x256/apps/cursor.png` | Icon in standard location |
| `~/.bashrc` (modified) | PATH configuration for command-line access |

## Checking Your Current Version

To see which version of Cursor you have installed:
```bash
~/.local/bin/cursor.appimage --version
```

## Troubleshooting

### Issue: "cursor: command not found"

**Solution 1**: Update PATH for current session
```bash
export PATH="$HOME/.local/bin:$PATH"
```

**Solution 2**: Open a new terminal window
The PATH should be automatically configured in new terminal sessions.

**Solution 3**: Check if the launcher exists
```bash
ls -l ~/.local/bin/cursor
```

### Issue: "Cursor doesn't appear in Applications menu"

**Solution**: Refresh the desktop environment
- Log out and log back in
- Or restart your computer
- Or manually update the database:
  ```bash
  update-desktop-database ~/.local/share/applications
  ```

### Issue: "No icon in the dock/taskbar"

**Solution**: The icon should appear after:
1. Running the update script (which extracts the icon)
2. Logging out and logging back in
3. Restarting the desktop environment

If it still doesn't appear, verify the icon exists:
```bash
file ~/.local/share/icons/cursor.png
```

### Issue: "AppImage not found in Downloads"

**Solution**: Make sure you've downloaded the Cursor AppImage to your `~/Downloads` folder:
```bash
ls -lh ~/Downloads/Cursor-*.AppImage
```

### Issue: "Permission denied"

**Solution**: Make sure the AppImage is executable:
```bash
chmod +x ~/Downloads/Cursor-*.AppImage
```

## Update Frequency

Cursor releases updates regularly. To stay up-to-date:

1. **Check for updates**: Visit [https://cursor.com](https://cursor.com) or check within the app
2. **Download new version**: Use the download URL above
3. **Run the script**: Execute `./update_cursor.sh` to install the new version

## Download URLs

- **Latest Stable (Linux x64)**: 
  ```
  https://www.cursor.com/api/download?platform=linux-x64&releaseTrack=stable
  ```

- **Official Website**: [https://cursor.com](https://cursor.com)

## Uninstalling Cursor

To remove Cursor from your system:

```bash
rm ~/.local/bin/cursor.appimage
rm ~/.local/bin/cursor
rm ~/.local/share/applications/cursor.desktop
rm ~/.local/share/icons/cursor.png
rm -rf ~/.local/share/icons/hicolor/256x256/apps/cursor.png
rm -rf ~/.cursor
```

Then remove the PATH entry from `~/.bashrc` if desired.

## Additional Resources

- **Official Documentation**: [https://cursor.com/docs](https://cursor.com/docs)
- **Support**: Visit the Cursor website for support and updates
- **AppImage Info**: [https://appimage.org](https://appimage.org)

## Script Details

The `update_cursor.sh` script performs the following operations:

1. Locates the Cursor AppImage in `~/Downloads`
2. Creates necessary directories (`~/.local/bin`, `~/.local/share/applications`, etc.)
3. Copies and sets permissions for the AppImage
4. Extracts the application icon from the AppImage
5. Creates a desktop entry for application menu integration
6. Creates a launcher script for command-line access
7. Updates PATH in shell configuration files
8. Updates desktop and icon databases

All operations are performed in your user directory and don't require root privileges.

---

**Last Updated**: October 2025  
**Script Version**: Compatible with Cursor AppImage distributions

