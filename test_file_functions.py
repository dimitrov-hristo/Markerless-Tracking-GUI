
import os
import shutil
import re
from count_unique_recordings import count_unique_recordings
from count_videos import count_video_files_and_size

def count_unique_csv_files(folder_path):
    unique_recordings = set()
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv") and "cam" in filename:
            recording_identifier = filename.split("cam")[0]
            unique_recordings.add(recording_identifier)
        elif filename.endswith(".csv") and not "cam" in filename:
            unique_recordings.add(recording_identifier)
    return len(unique_recordings)

def create_folder_and_copy_files(source_folder, destination_folder, file_names):
    try:
        # Create the destination folder if it doesn't exist
        os.makedirs(destination_folder, exist_ok=True)
        
        # Copy each specified file to the destination folder
        if isinstance(file_names, str):
            source_path = os.path.join(source_folder, file_names)
            destination_path = os.path.join(destination_folder, file_names)
            shutil.copy2(source_path, destination_path)
        else:
            for file_name in file_names:
                source_path = os.path.join(source_folder, file_name)
                destination_path = os.path.join(destination_folder, file_name)
                shutil.copy2(source_path, destination_path)
        
        print("Files copied successfully!")
    
    except Exception as e:
        print("An error occurred:", str(e))


def videoProcessing_page(mode, selected_directory):
    processing_operation = mode
    existing_folders = False
    csv_files = False
    asked_for_file_deletion = False
    # Select directory for annotation 

    if selected_directory:
        if mode == "Annotate 2D":
            deletion_folder_names = ["pose-2d"]
        elif mode == "Label 2D":
            deletion_folder_names = ["videos-labeled"]
        elif mode == "Annotate 3D":
            deletion_folder_names = ["pose-3d", "angles"]
        elif mode == "Label 3D":
            deletion_folder_names = ["videos-3d", "videos-combined"]
        
        # Walk through the directory tree
        for dirpath, dirnames, filenames in os.walk(selected_directory):
            # Check if the target folder is in the current directory's subdirectories
            if all(os.path.isfile(os.path.join(selected_directory, item)) for item in os.listdir(selected_directory)):
                dirnames = os.listdir(os.path.dirname(os.path.normpath(dirpath))) 
                dirpath = os.path.dirname(os.path.normpath(dirpath))
                csv_files = True
            for dirname in dirnames:
                for folder_name in deletion_folder_names:
                    if dirname == folder_name:
                        folder_to_delete = os.path.join(dirpath, dirname)
                        if not asked_for_file_deletion:
                            asked_for_file_deletion = True 
                            print(f"The folder {folder_name} already exists in {selected_directory} path. Do you want to DELETE and RE-RUN {mode}?")
                            print(f"Deleting the folder: {folder_to_delete}")
                        elif asked_for_file_deletion and not existing_folders:
                            print(f"Deleting the folder: {folder_to_delete}")
                            existing_folders = False
        if existing_folders == False:
            input_directory = os.path.normpath(selected_directory)
            num_files, total_files_size_bytes, unique_recordings, videos_raw_folders = count_video_files_and_size(input_directory, '.mp4')
            total_files_size_MB = round(total_files_size_bytes / (1024 ** 2),2)
            if mode == "Annotate 2D":
                num_processing_files = int(num_files)
            elif csv_files:
                unique_recordings = count_unique_csv_files(input_directory)
                num_processing_files = int(unique_recordings)
            else:
                num_processing_files = int(videos_raw_folders)
                                    
            # Check if the conditions are met
            if num_files > 30 or total_files_size_MB > 200:
                proceed = print(f"There are {num_files} files (total size {total_files_size_MB}MB), which can take awhile to process. Are you sure you want to proceed?")
                if proceed:
                    print('Proceeding to processing window')                      
            else:
                print('Proceeding to processing window') 

input_directory = 'D:\\MT_GUI_TEST\\Test_differentTime'
file_extension='mp4'
num_files, total_files_size_bytes, unique_recordings, videos_raw_folders, error_string = count_video_files_and_size(input_directory, file_extension)     

print(num_files)
print(total_files_size_bytes)
print(unique_recordings)
print(videos_raw_folders)
print(error_string)
