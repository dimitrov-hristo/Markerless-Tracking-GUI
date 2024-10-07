import cv2
import re
import numpy as np
import detectLED
import os
from moviepy.editor import VideoFileClip
from matplotlib.widgets import RectangleSelector

#video_path = '/Volumes/Plasticity/Projects/hristo_grasping/Behavioural_data/CT_005/Object_10/Towards/2024-03-12-12-14-01-camD.mp4'
#loaded_array = np.load('/Volumes/Plasticity/Projects/hristo_grasping/Behavioural_data/CT_005/Object_10/Towards/off_array_camD.npy')

#on_frames = loaded_array[0:5] 


def plot_frame(video_path, frame_number, gui_ax):

    # Capture video frame
    cap = cv2.VideoCapture(video_path)  # Replace with your video file
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)  # Go to specific frame
    ret, frame = cap.read()

    if ret:
        # Convert BGR to RGB for matplotlib
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        gui_ax.clear()  # Clear previous plot
        gui_ax.set_title('Frame {}'.format(frame_number))
        gui_ax.axis('off')
        gui_ax.imshow(frame_rgb)  # Plot the frame
        

    cap.release()

def checkROI(videoPath, ROI_frame, ax, canvas, var):
    cap = cv2.VideoCapture(videoPath)
    
    frame_number = 0
    
    # Get the desired frame from the video
    while frame_number < ROI_frame:
        ret, frame = cap.read()
        frame_number += 1
        if not ret:
            print("Failed to read the video frame.")
            return None
    
    # Convert the frame to RGB (matplotlib uses RGB)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Deactivate and remove the previous RectangleSelector (if any)
    if hasattr(ax, 'rect_selector') and ax.rect_selector is not None:
        ax.rect_selector.set_active(False)
        ax.rect_selector = None  # Remove the reference to the old selector
    
    # Clear previous rectangles and frame content
    ax.clear()  # This clears any previous frame and overlays (including old rectangles)
    ax.imshow(frame_rgb)
    
    # Redraw the canvas (for Tkinter)
    canvas.draw()

    # Global variable to store the coordinates of the rectangle
    roi_coords = []

    # Define a callback function to capture the ROI coordinates
    def onselect(eclick, erelease):
        # Extract the start and end points of the selected region
        x1, y1 = eclick.xdata, eclick.ydata  # Mouse down event
        x2, y2 = erelease.xdata, erelease.ydata  # Mouse release event
        
        # Calculate the top-left corner and the width/height of the selection
        x, y = int(min(x1, x2)), int(min(y1, y2))
        width, height = int(abs(x2 - x1)), int(abs(y2 - y1))
        
        # Store the ROI coordinates
        roi_coords.clear()  # Clear any previous selection
        roi_coords.append((x, y, width, height))


    # Handle the confirmation of the selection via a key press (Enter key)
    def on_key(event):
        if event.key == 'enter':  # 'Enter' key finalizes the selection
            if roi_coords:
                var.set(True) 
                #canvas.get_tk_widget().quit()  # Close the interactive session
            else:
                print("No region has been selected.")

    # Updated RectangleSelector to keep interactivity but hide the resize handles
    rect_selector = RectangleSelector(ax, onselect, 
                                      interactive=True,  # Keep the interactive functionality
                                      useblit=True, 
                                      button=[1], 
                                      minspanx=5, 
                                      minspany=5, 
                                      spancoords='pixels', 
                                      props=dict(facecolor='none', edgecolor='red', linewidth=1.5),
                                      handle_props=dict(marker='o', markersize=0.1, color='none'))  # Minimize handles
    
    # Store the current RectangleSelector in the axes for future deactivation
    ax.rect_selector = rect_selector
    
    # Connect the keyboard event to listen for 'enter' key
    canvas.mpl_connect('key_press_event', on_key)

    var.set(False)  # Reset the flag
    canvas.get_tk_widget().wait_variable(var) 
    
    if roi_coords:
        return roi_coords[0]  # Return the ROI coordinates (x, y, width, height)
    else:
        print("No ROI was selected.")
        return None

def individualVid_trim(input_path, saving_dir, video_file_extension, start_frame, stop_frame, video_file_suffix):

    vid_name = os.path.basename(input_path)
    base_name, ext = os.path.splitext(vid_name)
    if not ext == video_file_extension:
        raise ValueError("The file does not have the selected video file extension at configuration.")
    # Find the position of '_cam[A-Z]'
    if video_file_suffix not in base_name:
        raise ValueError(f"Filename does not contain '{video_file_suffix}'.")
    # Insert '_trimmed' before '_cam'
    trimmed_base_name = base_name.replace(video_file_suffix, '_trimmed' + video_file_suffix)
    # Construct the new filename with '_trimmed'
    new_file_name = f"{trimmed_base_name}{ext}"
    video_output_path = os.path.join(saving_dir, new_file_name)

    cap = cv2.VideoCapture(input_path) 
    videoFPS = int(cap.get(cv2.CAP_PROP_FPS))
    
    bufferTime = 1/(videoFPS*2.1)

    video = VideoFileClip(input_path)
    trimmed = video.subclip((start_frame/videoFPS), (stop_frame/videoFPS) + bufferTime)
    trimmed.write_videofile(video_output_path, codec='libx264', audio_codec='aac', fps=videoFPS)

def automatic_trim(input_path, output_path, multiple_trims, ROIs, file_extension, file_suffix, recording_length, report_callback):
    print("Automatic trim")

    potentialErrorList = []
    tempArray = []
    video_naming_list = list(ROIs.keys())
    fileCount=0
    # Iterate over files in the folder
    for root, dirs, files in os.walk(input_path):

        if not dirs and files:
            sorted_video_files = sorted(files)
        
            relative_path = os.path.relpath(root, input_path)
            current_save_dir = os.path.join(output_path, relative_path,'videos-raw')     
                    
            for file_name in sorted_video_files:

                if file_name.endswith(file_extension):
                    if not os.path.exists(current_save_dir):
                        os.makedirs(current_save_dir)

                    fileCount+=1
                    current_video_path = os.path.join(root, file_name)
                    vid_ROI_name = list(filter(lambda x: file_name[-8:-4] in x, ROIs))[0]
                    vid_ROI = ROIs[vid_ROI_name]
                    print(vid_ROI)
                    on_array,off_array,total_frames = detectLED.detectLightChange(current_video_path, vid_ROI, recording_length, multiple_trims)
                    tempArray.append(on_array)

                    if multiple_trims > 1:
                        for ij in range(multiple_trims):
                            start_frame = on_array[ij] + 1
                            if recording_length > 0:
                                stop_frame = start_frame + recording_length
                            else: 
                                stop_frame = off_array[ij] + 1

                            individualVid_trim(current_video_path, current_save_dir, file_extension, start_frame, stop_frame, file_suffix)
                    else:
                        individualVid_trim(current_video_path, current_save_dir, file_extension, on_array, off_array, file_suffix)

                    if fileCount == len(video_naming_list):
                        # Escape the file extension for regex usage (in case there are special characters like '.' in it)
                        escaped_extension = re.escape(file_extension)

                        # Dictionary to hold the file names and their corresponding letter
                        file_dict = {}

                        # Extract the letter and file pair
                        for file in files:
                            # Use the escaped extension in the regex
                            match = re.search(rf'{file_suffix}\.{escaped_extension}$', file)
                            if match:
                                letter = match.group(1)
                                file_dict[letter] = file

                        # Sort the dictionary by the alphabetical order of the keys (letters)
                        sorted_letters = sorted(file_dict.keys())

                        # Initialize the variables dictionary and assign slices in sorted order
                        video_files_dict = {letter: slice(idx) for idx, letter in enumerate(sorted_letters)}

                        # Initialize flag variable
                        flagged = False

                        # Iterate over pairs of video_files_dict
                        for var1, slice1 in video_files_dict.items():
                            for var2, slice2 in video_files_dict.items():
                                if var1 != var2:  # Exclude same variable combinations
                                    diff = np.abs(tempArray[slice1.stop] - tempArray[slice2.stop])
                                    if np.any(diff > 5):
                                        potentialErrorList.append(os.path.join(root, 'cam' + var1 + '-' +' cam' + var2))
                                        flagged = True
                                        break
                            # if flagged:
                            #     break
                        tempArray = []
                        fileCount = 0
                    

    if potentialErrorList:
        # Open a text file for writing
        with open(output_path + "/errorfile_locations.txt", "w") as file:
            # Iterate over the list and write each item to the file
            for file_locations in potentialErrorList:
                file.write(file_locations + "\n")  # Write each location followed by a newline

    report_callback("Video trimming is completed.")

    
