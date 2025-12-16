# %% =======================================================
""" General parameters"""

import os
from sync_data import create_sync_manager

# Whether to use checksum mode, which is more robust but slower
checksum_mode = False

# List of data directories to sync
data_dirs = [
    "mean_images",
    "sleap_flowtank_under_1",
    "sleap_flowtank_under_3",
    "sleap_flowtank_side_1",
    "sleap_flowtank_side_3",
    "matlab_data"
]

# List of video directories to sync (bidirectional)
video_dirs = [
    "processed_video"
]

# List of one-way video directories (local -> remote only)
one_way_video_dirs = [
    # "raw"
]


# %% =======================================================
""" Paths for Linux machine + Thumb drive """

# WORK Linux directory
if os.path.exists("/vortex/schooling_video") and os.path.exists("/flux/schooling_data"):
    local_data_root = "/flux/schooling_data/catfish_flowtank_kinematics"
    local_video_root = "/vortex/schooling_video/catfish_kinematics"
    local_log_root = "/flux/schooling_data/catfish_flowtank_log"
    print("✓ Using NETWORK paths (prioritized)")
    
# HOME Linux directory
elif os.path.exists("/home/mmchenry/Documents/catfish_kinematics"):
    local_data_root = "/home/mmchenry/Documents/catfish_kinematics/data"
    local_video_root = "/home/mmchenry/Documents/catfish_kinematics/video"
    local_log_root = "/home/mmchenry/Documents/catfish_flowtank_log"
    print("⚠️  Using LOCAL paths (network not available)")

# Check for Mac paths
elif os.path.exists("/Users/mmchenry/Documents"):
    local_data_root = "/Users/mmchenry/Documents/Projects/catfish_kinematics"
    local_video_root = "/Users/mmchenry/Documents/Video/catfish_kinematics"
    print("✓ Using MAC laptop paths")
else:
    raise RuntimeError("Could not find directory to sync with.")

# Remote volume base path - check multiple possible mount points
remote_data_root = None
remote_video_root = None

# Check for thumb drive in various locations
thumb_drive_paths = [
    "/mnt/thumbdrive",
    "/media/mmchenry/thumbdrive",
    "/media/mmchenry/USB_DRIVE",
    "/media/mmchenry/ThumbDrive",
    "/Volumes/Shared/catfish_kinematics"  # Mac mount point
]

for path in thumb_drive_paths:
    if os.path.exists(path):
        remote_data_root = path + "/data/"
        remote_video_root = path + "/video/"
        print(f"✓ Using THUMB drive paths: {path}")
        break

if remote_data_root is None:
    raise RuntimeError("Could not find thumbdrive to sync with. Checked: " + ", ".join(thumb_drive_paths))

# Local log root - syncs with remote data
local_log_root = "/home/mmchenry/Documents/catfish_flowtank_log"
remote_log_root = remote_data_root + "catfish_flowtank_log/"  # Logs sync to catfish_flowtank_log subdirectory in remote data

print(f"Local data root: {local_data_root}")
print(f"Local video root: {local_video_root}")
print(f"Local log root: {local_log_root}")
print(f"Remote data root: {remote_data_root}")
print(f"Remote video root: {remote_video_root}")
print(f"Remote log root: {remote_log_root}")


# %% =======================================================
""" Create sync manager """

# Create sync manager with detected paths
sync_manager = create_sync_manager(
    local_data_root=local_data_root,
    local_video_root=local_video_root,
    data_dirs=data_dirs,
    video_dirs=video_dirs,
    one_way_video_dirs=one_way_video_dirs,
    remote_data_base=remote_data_root,
    remote_video_base=remote_video_root,
    checksum_mode=checksum_mode
)

# %% =======================================================
""" List sync pairs """

# List all available sync pairs
print("\n" + "="*60)
print("AVAILABLE SYNC PAIRS:")
print("="*60)
sync_manager.list_sync_pairs()


# %% =======================================================
""" Run dry run """

# Run dry run to see what would be synced
print("\n" + "="*60)
print("DRY RUN - PREVIEW OF CHANGES:")
print("="*60)
sync_manager.sync_all(dry_run=True)


# %% =======================================================
""" Perform actual sync """

# Uncomment the line below to perform actual sync
sync_manager.sync_all(dry_run=False)





# %% =======================================================
""" Additional Control Options """

# Sync only specific pairs (examples)
# sync_manager.sync_pair_by_name("data_mean_images_to_local", dry_run=True)
# sync_manager.sync_pair_by_name("video_processed_video_to_remote", dry_run=True)

# You can also access individual sync pairs directly:
# for pair in sync_manager.config["sync_pairs"]:
#     if "processed_video" in pair["name"]:
#         sync_manager.sync_pair(pair, dry_run=True)