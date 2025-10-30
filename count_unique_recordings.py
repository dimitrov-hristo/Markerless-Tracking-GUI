# SPDX-License-Identifier: Apache-2.0
import os
import re

def count_unique_recordings(folder_path, video_file_extension):
    cam_pattern = re.compile(r"cam[\w\d]+", re.IGNORECASE)
    all_files = [f for f in os.listdir(folder_path) if f.endswith(video_file_extension) and "cam" in f.lower()]

    camera_ids = set()
    recordings = []
    error_string = ''

    for f in all_files:
        name_wo_ext = f.rsplit('.', 1)[0]
        cam_match = cam_pattern.search(name_wo_ext)
        if cam_match:
            camera_ids.add(cam_match.group().lower())
            recordings.append((f.split("cam")[0], cam_match.group().lower()))

    num_cameras = len(camera_ids)
    total_videos = len(all_files)
    if num_cameras == 0:
        recordings_count = 0
    else:
        if total_videos % num_cameras != 0:
            error_string = f"Mismatch detected: {total_videos} video files found, but {num_cameras} unique cameras identified. "f"This suggests that some recordings are missing camera files or misnamed."
            recordings_count = total_videos // num_cameras

        else:
            recordings_count = total_videos // num_cameras

            for i in range(0, len(recordings), num_cameras):
                chunk = recordings[i:i + num_cameras]
                base_names = {base for base, _ in chunk}
                if len(base_names) != 1:
                    error_string = f"Inconsistent base names in recording set: {chunk}, at folder directory: {folder_path}. Rename the files to be matching."

    return recordings_count, error_string