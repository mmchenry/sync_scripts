# %% =======================================================
""" General parameters"""

import os
from sync_data import create_sync_manager

# Whether to use checksum mode, which is more robust but slower
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

# List of video directories to sync (bidirectional)
video_dirs = [
    "processed_video"
]

# List of one-way video directories (local -> remote only)
one_way_video_dirs = [
    "raw"
]


# %% =======================================================
""" Paths for Home Linux machine + Thumb drive """

# Detect paths automatically
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

# Remote volume base path
remote_data_root = "/media/mmchenry/ThumbDrive/"
remote_video_root = "/media/mmchenry/ThumbDrive/"
if os.path.exists(remote_data_root):
    print("✓ Using THUMB drive paths")
else:
    raise RuntimeError("Could not find Thumbdrive to sync with.")

print(f"Local data root: {local_data_root}")
print(f"Local video root: {local_video_root}")
print(f"Remote data root: {remote_data_root}")
print(f"Remote video root: {remote_video_root}")


# %% =======================================================
""" Paths for Mac Laptop + Linux machine """

if os.path.exists("/Users/mmchenry/Documents"):
    print("✓ Using MAC laptop paths")
    local_data_root = "/Users/mmchenry/Documents/Projects/catfish_kinematics"
    local_video_root = "/Users/mmchenry/Documents/Video/catfish_kinematics"
else:
    raise RuntimeError("Could not find Mac laptop to sync with.")

if os.path.exists("/Volumes/Shared/catfish_kinematics"):
    remote_data_root = "/Volumes/Shared/catfish_kinematics"
    remote_video_root = "/Volumes/Shared/catfish_kinematics"
    print("✓ Using Linux machine paths")
else:
    raise RuntimeError("Could not find Linux machine to sync with.")

print(f"Local data root: {local_data_root}")
print(f"Local video root: {local_video_root}")
print(f"Remote data root: {remote_data_root}")
print(f"Remote video root: {remote_video_root}")


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
""" At School Linux machine + Network drive """
# %% =======================================================

# %% =======================================================
""" At School Linux machine + Thumb drive """
# %% =======================================================



# %% =======================================================
""" Additional Control Options """

# Sync only specific pairs (examples)
# sync_manager.sync_pair_by_name("data_mean_images_to_local", dry_run=True)
# sync_manager.sync_pair_by_name("video_processed_video_to_remote", dry_run=True)

# You can also access individual sync pairs directly:
# for pair in sync_manager.config["sync_pairs"]:
#     if "processed_video" in pair["name"]:
#         sync_manager.sync_pair(pair, dry_run=True)