#!/bin/sh

# Get the real user's home directory when running with sudo
get_user_home() {
    if [ -n "$SUDO_USER" ]; then
        getent passwd "$SUDO_USER" | cut -d: -f6
    else
        echo "$HOME"
    fi
}

installCursor() {
    USER_HOME=$(get_user_home)
    
    # Check if Downloads directory exists
    if [ ! -d "$USER_HOME/Downloads" ]; then
        echo "Error: Downloads directory not found in $USER_HOME"
        exit 1
    fi

    # Look for Cursor AppImage in Downloads
    DOWNLOADED_APPIMAGE=""
    cd "$USER_HOME/Downloads" || exit 1
    for file in Cursor-*.AppImage; do
        if [ -f "$file" ]; then
            DOWNLOADED_APPIMAGE="$USER_HOME/Downloads/$file"
            break
        fi
    done

    if [ -z "$DOWNLOADED_APPIMAGE" ]; then
        echo "Error: No Cursor AppImage found in ~/Downloads"
        echo "Please download the Cursor AppImage to your Downloads folder"
        exit 1
    fi

    echo "Installing/Updating Cursor AI IDE..."
    echo "Installing for user: $(basename "$USER_HOME")"
    
    # Icon URLs to try (in order of preference)
    ICON_URL1="https://www.cursor.com/assets/images/logo.png"
    ICON_URL2="https://cursor.sh/favicon.png"
    ICON_URL3="https://avatars.githubusercontent.com/u/145340649"

    # Paths for installation (ALL in user's home directory)
    INSTALL_DIR="$USER_HOME/.local/bin"
    ICONS_DIR="$USER_HOME/.local/share/icons"
    APPLICATIONS_DIR="$USER_HOME/.local/share/applications"
    
    # Create directories one by one (some shells don't support mkdir -p)
    mkdir "$USER_HOME/.local" 2>/dev/null || true
    mkdir "$USER_HOME/.local/bin" 2>/dev/null || true
    mkdir "$USER_HOME/.local/share" 2>/dev/null || true
    mkdir "$USER_HOME/.local/share/icons" 2>/dev/null || true
    mkdir "$USER_HOME/.local/share/applications" 2>/dev/null || true
    
    # Set full paths
    APPIMAGE_PATH="$INSTALL_DIR/cursor.appimage"
    ICON_PATH="$ICONS_DIR/cursor.png"
    DESKTOP_ENTRY_PATH="$APPLICATIONS_DIR/cursor.desktop"

    # Check if curl is available (needed for icon download)
    CURL_AVAILABLE=0
    if command -v curl >/dev/null 2>&1; then
        CURL_AVAILABLE=1
    elif command -v wget >/dev/null 2>&1; then
        CURL_AVAILABLE=2
    fi

    # Copy and set permissions for the AppImage
    echo "Installing Cursor AppImage..."
    if ! cp "$DOWNLOADED_APPIMAGE" "$APPIMAGE_PATH"; then
        echo "Error: Failed to copy AppImage to $APPIMAGE_PATH"
        exit 1
    fi
    chmod +x "$APPIMAGE_PATH"
    
    # Set correct ownership
    if [ -n "$SUDO_USER" ]; then
        chown "$SUDO_USER:$(id -gn "$SUDO_USER")" "$APPIMAGE_PATH"
    fi

    # Download/Extract Cursor icon
    echo "Setting up Cursor icon..."
    ICON_SUCCESS=0
    
    # First, try to extract icon from the AppImage
    if [ -f "$APPIMAGE_PATH" ]; then
        # Try to extract the icon from the AppImage
        if "$APPIMAGE_PATH" --appimage-extract-and-run --appimage-help >/dev/null 2>&1; then
            # AppImage supports extraction
            TMP_EXTRACT="/tmp/cursor_icon_extract_$$"
            mkdir -p "$TMP_EXTRACT"
            cd "$TMP_EXTRACT" || true
            
            # Try different methods to get the icon
            if "$APPIMAGE_PATH" --appimage-extract "*.png" 2>/dev/null; then
                # Find the largest PNG (likely the app icon)
                LARGEST_PNG=$(find squashfs-root -name "*.png" -type f -exec ls -s {} + 2>/dev/null | sort -rn | head -1 | awk '{print $2}')
                if [ -n "$LARGEST_PNG" ] && [ -f "$LARGEST_PNG" ]; then
                    cp "$LARGEST_PNG" "$ICON_PATH" 2>/dev/null && ICON_SUCCESS=1
                fi
            fi
            
            # Cleanup
            cd - >/dev/null 2>&1
            rm -rf "$TMP_EXTRACT" 2>/dev/null
        fi
    fi
    
    # If extraction failed, try downloading from URLs
    if [ "$ICON_SUCCESS" = "0" ]; then
        echo "Attempting to download icon from web..."
        for ICON_URL in "$ICON_URL1" "$ICON_URL2" "$ICON_URL3"; do
            if [ "$CURL_AVAILABLE" = "1" ]; then
                if curl -L -f "$ICON_URL" -o "$ICON_PATH" 2>/dev/null; then
                    # Verify it's actually an image file (at least 1KB)
                    if [ -f "$ICON_PATH" ] && [ "$(stat -c%s "$ICON_PATH" 2>/dev/null || echo 0)" -gt 1000 ]; then
                        ICON_SUCCESS=1
                        break
                    fi
                fi
            elif [ "$CURL_AVAILABLE" = "2" ]; then
                if wget -q -O "$ICON_PATH" "$ICON_URL" 2>/dev/null; then
                    # Verify it's actually an image file (at least 1KB)
                    if [ -f "$ICON_PATH" ] && [ "$(stat -c%s "$ICON_PATH" 2>/dev/null || echo 0)" -gt 1000 ]; then
                        ICON_SUCCESS=1
                        break
                    fi
                fi
            fi
        done
    fi
    
    # If still no icon, create a simple fallback
    if [ "$ICON_SUCCESS" = "0" ]; then
        echo "Warning: Could not download/extract icon. Using system default."
        # Use a generic IDE icon from the system
        for FALLBACK_ICON in /usr/share/pixmaps/code.png /usr/share/pixmaps/text-editor.png /usr/share/icons/hicolor/256x256/apps/code.png; do
            if [ -f "$FALLBACK_ICON" ]; then
                cp "$FALLBACK_ICON" "$ICON_PATH" 2>/dev/null && break
            fi
        done
    fi
    
    # Set correct ownership
    if [ -n "$SUDO_USER" ] && [ -f "$ICON_PATH" ]; then
        chown "$SUDO_USER:$(id -gn "$SUDO_USER")" "$ICON_PATH"
    fi
    
    # Verify icon was created
    if [ -f "$ICON_PATH" ] && [ "$(stat -c%s "$ICON_PATH" 2>/dev/null || echo 0)" -gt 100 ]; then
        echo "✓ Icon installed successfully"
    else
        echo "⚠ Icon installation incomplete, but application will still work"
    fi

    # Create a .desktop entry for Cursor
    # Create applications directory if it doesn't exist
    mkdir -p "$(dirname "$DESKTOP_ENTRY_PATH")"
    
    # Copy icon to hicolor theme for better integration
    HICOLOR_ICON_DIR="$USER_HOME/.local/share/icons/hicolor/256x256/apps"
    mkdir -p "$HICOLOR_ICON_DIR"
    if [ -f "$ICON_PATH" ]; then
        cp "$ICON_PATH" "$HICOLOR_ICON_DIR/cursor.png" 2>/dev/null
        if [ -n "$SUDO_USER" ]; then
            chown -R "$SUDO_USER:$(id -gn "$SUDO_USER")" "$USER_HOME/.local/share/icons/hicolor" 2>/dev/null
        fi
    fi
    
    echo "Creating .desktop entry for Cursor..."
    cat > "$DESKTOP_ENTRY_PATH" <<EOL
[Desktop Entry]
Name=Cursor AI IDE
Exec=$APPIMAGE_PATH --no-sandbox %F
Icon=cursor
Type=Application
Categories=Development;TextEditor;IDE;Utility;
Terminal=false
StartupNotify=true
MimeType=text/plain;inode/directory;
Keywords=cursor;code;editor;ide;development;ai;
Comment=AI-powered code editor
EOL

    # Create cursor launcher script
    echo "Creating cursor launcher script..."
    mkdir -p "$(dirname "$USER_HOME/.local/bin/cursor")"
    cat > "$USER_HOME/.local/bin/cursor" <<EOL
#!/bin/sh
"$APPIMAGE_PATH" --no-sandbox "\$@" > /dev/null 2>&1 &
EOL
    chmod +x "$USER_HOME/.local/bin/cursor"
    
    # Set correct ownership of the launcher script
    if [ -n "$SUDO_USER" ]; then
        chown -R "$SUDO_USER:$(id -gn "$SUDO_USER")" "$USER_HOME/.local/bin"
    fi

    echo "Setting correct ownership..."
    # Set correct ownership of the .desktop file and all created files
    if [ -n "$SUDO_USER" ]; then
        chown -R "$SUDO_USER:$(id -gn "$SUDO_USER")" "$USER_HOME/.local/share"
        chown "$SUDO_USER:$(id -gn "$SUDO_USER")" "$DESKTOP_ENTRY_PATH"
    fi

    # Update desktop database
    echo "Updating desktop database..."
    if command -v update-desktop-database >/dev/null 2>&1; then
        if [ -n "$SUDO_USER" ]; then
            sudo -u "$SUDO_USER" update-desktop-database "$USER_HOME/.local/share/applications" 2>/dev/null || true
        else
            update-desktop-database "$USER_HOME/.local/share/applications" 2>/dev/null || true
        fi
    fi
    
    # Update icon cache
    echo "Updating icon cache..."
    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        if [ -n "$SUDO_USER" ]; then
            sudo -u "$SUDO_USER" gtk-update-icon-cache -f -t "$USER_HOME/.local/share/icons" 2>/dev/null || true
        else
            gtk-update-icon-cache -f -t "$USER_HOME/.local/share/icons" 2>/dev/null || true
        fi
    fi
    
    # Make desktop file executable (required by some desktop environments)
    chmod +x "$DESKTOP_ENTRY_PATH" 2>/dev/null || true
    
    # Ensure all the directories have correct permissions
    chmod 755 "$USER_HOME/.local" "$USER_HOME/.local/bin" "$USER_HOME/.local/share" "$USER_HOME/.local/share/applications" 2>/dev/null || true

    # Add ~/.local/bin to PATH if not already there
    # Try to add to both .profile and .bashrc for better compatibility
    PATH_ENTRY='export PATH="$HOME/.local/bin:$PATH"'
    
    for PROFILE_FILE in "$USER_HOME/.profile" "$USER_HOME/.bashrc"; do
        # Only add if file exists or can be created
        if [ -f "$PROFILE_FILE" ] || touch "$PROFILE_FILE" 2>/dev/null; then
            # Check if the PATH entry already exists
            if ! grep -q ".local/bin" "$PROFILE_FILE" 2>/dev/null; then
                echo "Adding ~/.local/bin to PATH in $(basename "$PROFILE_FILE")"
                echo "" >> "$PROFILE_FILE"
                echo "# Added by Cursor installer" >> "$PROFILE_FILE"
                echo "$PATH_ENTRY" >> "$PROFILE_FILE"
                # Fix ownership
                if [ -n "$SUDO_USER" ]; then
                    chown "$SUDO_USER:$(id -gn "$SUDO_USER")" "$PROFILE_FILE"
                fi
            fi
        fi
    done

    # Create a temporary script to update PATH for current session
    TMP_SCRIPT="/tmp/cursor_path_update.sh"
    echo "#!/bin/sh" > "$TMP_SCRIPT"
    echo "$PATH_ENTRY" >> "$TMP_SCRIPT"
    echo 'echo "PATH has been updated for this session"' >> "$TMP_SCRIPT"
    chmod +x "$TMP_SCRIPT"
    
    if [ -n "$SUDO_USER" ]; then
        chown "$SUDO_USER:$(id -gn "$SUDO_USER")" "$TMP_SCRIPT"
    fi

    echo ""
    echo "============================================"
    echo "Installation complete!"
    echo "============================================"
    echo ""
    echo "Files installed:"
    echo "  - AppImage: $APPIMAGE_PATH"
    echo "  - Launcher: $USER_HOME/.local/bin/cursor"
    echo "  - Desktop entry: $DESKTOP_ENTRY_PATH"
    echo "  - Icon: $ICON_PATH"
    echo ""
    echo "To run Cursor RIGHT NOW, choose ONE of these:"
    echo ""
    echo "Quick Start (for current terminal session):"
    echo "  1. Run: export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo "  2. Run: cursor"
    echo ""
    echo "Or run directly:"
    echo "    $USER_HOME/.local/bin/cursor"
    echo ""
    echo "============================================"
    echo "For FUTURE terminal sessions:"
    echo "============================================"
    echo "The PATH has been added to your shell config files."
    echo "After opening a NEW terminal window, you can just run: cursor"
    echo ""
    echo "============================================"
    echo "To find Cursor in Applications menu:"
    echo "============================================"
    echo "  - Log out and log back in (or restart)"
    echo "  - Look for 'Cursor AI IDE' in your applications"
    echo ""
    echo "If it doesn't appear after logging out/in, try:"
    echo "  - Restart your computer"
    echo "  - Or run: xdg-open $DESKTOP_ENTRY_PATH"
    echo ""
    echo "============================================"
    
    # Try to verify the installation
    if [ -f "$APPIMAGE_PATH" ] && [ -x "$APPIMAGE_PATH" ]; then
        echo "✓ AppImage is installed and executable"
    else
        echo "✗ Warning: AppImage may not be properly installed"
    fi
    
    if [ -f "$USER_HOME/.local/bin/cursor" ] && [ -x "$USER_HOME/.local/bin/cursor" ]; then
        echo "✓ Cursor launcher is installed and executable"
    else
        echo "✗ Warning: Cursor launcher may not be properly installed"
    fi
    
    if [ -f "$DESKTOP_ENTRY_PATH" ]; then
        echo "✓ Desktop entry is created"
    else
        echo "✗ Warning: Desktop entry may not be properly created"
    fi
    echo "============================================"
}

installCursor