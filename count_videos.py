import os
from count_unique_recordings import count_unique_recordings

def count_video_files_and_size(input_dir,video_file_extension):
    total_files = 0
    total_size = 0
    unique_recordings = 0
    video_folders = 0
    #check if there are any videos-raw folders in the directory
    #this check ensures that video files and videos-raw folders
    #are captured correctly
    folder_check = any(d == 'videos-raw' and os.path.isdir(os.path.join(root, d)) for root, dirs, _ in os.walk(input_dir) for d in dirs)

    if folder_check:
        for root, dirs, files in os.walk(input_dir):
            last_folder = os.path.basename(os.path.normpath(root))
            if last_folder == 'videos-raw':
                video_folders +=1
                unique_recordings_count, error_string = count_unique_recordings(root, video_file_extension)
                if error_string:
                    break
                else:
                    unique_recordings += unique_recordings_count
                for file in files:
                    if file.endswith(video_file_extension):
                        total_files += 1
                        total_size += os.path.getsize(os.path.join(root, file))
    else:
        for root, dirs, files in os.walk(input_dir):
            last_folder = os.path.basename(os.path.normpath(root))
            unique_recordings_count, error_string = count_unique_recordings(root, video_file_extension)
            if error_string:
                break
            else:
                for file in files:
                        if file.endswith(video_file_extension):
                            total_files += 1
                            total_size += os.path.getsize(os.path.join(root, file))

    return total_files, total_size, unique_recordings, video_folders, error_string