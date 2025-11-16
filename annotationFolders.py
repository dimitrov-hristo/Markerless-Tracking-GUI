# SPDX-License-Identifier: Apache-2.0
import os
import shutil
import subprocess
import time
import threading
import sys
from count_unique_recordings import count_unique_recordings


def process_folders(input_dir, output_dir, selected_bodypart, video_file_extension, report_callback, mode, config_dir, stop_event):

    def create_folder(path):
        if not os.path.exists(path):
            os.makedirs(path)
    
    def copy_mp4_files(src_folder, dest_folder):
        mp4Files = 0
        for filename in os.listdir(src_folder):
            if filename.endswith(video_file_extension):
                mp4Files+=1
                shutil.copy(os.path.join(src_folder, filename), dest_folder)
                if mode == "Annotate 2D":
                    report_callback(dest_folder)
                    time.sleep(0.5)
                    path = os.path.join(src_folder, filename)
                    run2D_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "run2D.py")
                    execute_anaconda_command(f"conda run -n mediaPipeEnv python {run2D_dir} \"{path}\" \"{dest_folder}\" \"{selected_bodypart}\"",report_callback)
        if mp4Files == 0:
            report_callback("2D Annotation, Input Videos")

    def process_mp4_folder(folder_path,contains_csv_files):
        
        #Delete any empty folders before running anything to prevent
        #bugs coming from a user creating an empty folder by accident
        #at the last level
        for root, dirs, files in os.walk(folder_path):
            if not dirs and not files:
                print(f"Empty folder deleted at: {root}")
                shutil.rmtree(root)

        last_folder = os.path.basename(os.path.normpath(folder_path))
        parent_dir = os.path.dirname(folder_path)
        labeled_video_folder_names = ['videos-labeled', 'videos-combined', 'videos-3d']

        if last_folder == 'videos-raw' or contains_csv_files:

            if mode == "Annotate 2D":
                # Create the "2d-pose" folder next to "videos-raw"
                for filename in os.listdir(folder_path):
                    if filename.endswith(video_file_extension):
                        report_callback(folder_path)
                        time.sleep(0.5)
                        path = os.path.join(folder_path, filename)
                        run2D_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "run2D.py")
                        execute_anaconda_command(f"conda run -n mediaPipeEnv python {run2D_dir} \"{path}\" \"{folder_path}\" \"{selected_bodypart}\"",report_callback)
                    else:
                        report_callback("2D Annotation, Input Videos")
                        time.sleep(3)

            elif mode == 'Annotate 3D':
                
                calibration_file_path = os.path.join(config_dir, "calibration.toml")
                if calibration_file_path:
                    pose3d_dir = os.path.join(parent_dir, 'pose-3d')

                    if os.path.exists(pose3d_dir) and not os.listdir(pose3d_dir):
                        os.rmdir(pose3d_dir)
                    create_folder_and_copy_files(config_dir, os.path.dirname(parent_dir), "config.toml")
                    
                    calibration_target_folder = os.path.join(parent_dir, 'calibration')
                    create_folder_and_copy_files(config_dir, calibration_target_folder, "calibration.toml")

                    command = 'cd ' +  os.path.dirname(parent_dir)
                    execute_anaconda_command(command,report_callback)
        
                    report_callback(folder_path)

                    command = 'anipose triangulate'
                    execute_anaconda_command(command,report_callback)
                    
                    command = 'anipose angles'
                    execute_anaconda_command(command,report_callback)
                        
                else:
                    if os.path.exists(os.path.join(parent_dir, 'pose-2d')):
                        report_callback("3D Annotation, Camera Calibration")
                        time.sleep(3)
                    elif os.path.exists(os.path.join(parent_dir, 'videos-raw')):
                        report_callback("3D Annotation, 2D Annotation, and Camera Calibration")
                        time.sleep(3)
                    else:
                        report_callback("3D Annotation, Input Videos, 2D Annotation, and Camera Calibration")
                        time.sleep(3)
                    
            elif mode == 'Label 2D':
                print("Stop event at Label 2D")
                print(stop_event.is_set())
                
                command = 'cd ' +  os.path.dirname(parent_dir)
                execute_anaconda_command(command,report_callback)

                report_callback(folder_path)

                command = 'anipose label-2d'
                execute_anaconda_command(command,report_callback)

            elif mode == 'Label 3D':

                print("Stop event at Label 3D")
                print(stop_event.is_set())

                report_callback(folder_path)

                command = 'cd ' +  os.path.dirname(parent_dir)
                execute_anaconda_command(command,report_callback)

                command = 'anipose label-3d'
                execute_anaconda_command(command,report_callback)

                unique_recordings, error_string = count_unique_recordings(folder_path, video_file_extension)
                mp4_count = 0

                # Iterate over all files in the folder
                for file in os.listdir(folder_path):
                    # Check if the file ends with .mp4
                    if file.endswith(video_file_extension):
                        mp4_count += 1

                # FFMPEG CANNOT PRODUCE A COMBINED TILE VIDEO FOR MORE THAN 4 INDIVIDUAL VIDEOS
                if mp4_count/unique_recordings <= 4:
                    command = 'anipose label-combined'
                    execute_anaconda_command(command,report_callback)
                
        elif last_folder not in labeled_video_folder_names and mode == 'Annotate 2D':
            
            # Create the required folders in the output directory
            relative_path = os.path.relpath(folder_path, input_dir)
            new_dir = os.path.join(output_dir, selected_bodypart, relative_path)
            print(f"New Directory at '{new_dir}'")
            videos_raw_folder = os.path.join(new_dir, 'videos-raw')

            create_folder(new_dir)
            create_folder(videos_raw_folder)

            create_folder_and_copy_files(config_dir, os.path.dirname(new_dir), "config.toml")
            copy_mp4_files(folder_path, videos_raw_folder)

    def find_and_process_folders(base_dir):

        processed_files_number = 0
        # if a folder contains only files and they are CSV, then process it
        # as most likely the user has chosen a pose-2d or pose-3d folder for
        # videos labeling
        items = os.listdir(base_dir)
        if "Label" in mode:
            if all(os.path.isfile(os.path.join(base_dir, item)) for item in items):
                processed_files_number = 1
                for root, dirs, files in os.walk(input_dir):
                    if any(file.endswith('.csv') for file in files):
                        process_mp4_folder(base_dir,True)

        # Otherwise, if a folder contains only mp4 files or other subfolders,
        # Then for each lowest-directory folder that contains mp4 files
        # Send that low folder directory for processing. Depending on the mode,
        # It could either process these files directly (2D Annotation), or it will
        # move up a directory and do the other functions like 3D Annotation and Labeling.
        # An error will be raised to the GUI if missing prerequisite folders.
        for root, dirs, files in os.walk(base_dir):
            if stop_event.is_set():
                    break
            if any(file.endswith(video_file_extension) for file in files):
                processed_files_number += 1
                if stop_event.is_set():
                    break
                process_mp4_folder(root,False)

        if processed_files_number == 0:
            report_callback(f"Processing folder path '{os.path.dirname(base_dir)}': no video files found inside the folder directory")
            time.sleep(5)
        if not stop_event.is_set():
            report_callback("Finished")
            time.sleep(3)

    # Start processing
    find_and_process_folders(input_dir)

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

def execute_anaconda_command(command,report_callback):
    try:
        if command.startswith('cd '):
            directory = command[3:].strip()
            os.chdir(directory)
            print(f"Changed directory to: {directory}")
        else:
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, text=True, bufsize=1,env=env)
            # Continuously read from the combined stdout and stderr
            with process.stdout:
                for line in iter(process.stdout.readline, ''):
                    sys.stdout.write(line)
                    sys.stdout.flush()
                    report_callback(f"STDOUT:\n{line}")
            process.wait()  # Wait for the process to finish
            
            if 'calibrate' in command:   
                report_callback("STDOUT: Finished")
                time.sleep(3)

    except Exception as e:
        print("An error occurred:", str(e))

