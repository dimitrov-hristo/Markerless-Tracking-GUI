import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import time
import os
import shutil
import re
import annotationFolders
import threading
from tkinter.scrolledtext import ScrolledText
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import videoTrim_functions

class MyApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.stop_event = threading.Event()
        self.progress_seconds_increment = 0

        self.default_save_directory = "C:/default/save/path"
        self.calibrationVid_directory = ''
        self.default_board_size = "10x7"
        self.default_marker_length = "18.75"
        self.default_markers_dict_number = "50"
        self.default_markers_bits_number = "4"
        self.default_board_square_side_length = "25"
        self.default_board_type = "Charuco"
        self.default_animal_calibration = "false"
        self.default_fisheye = "false"
        self.default_file_extension = '.mp4'
        self.default_file_suffix = '-cam([A-Z])'

        # Define shared variables with default values
        self.save_directory = tk.StringVar(value=self.default_save_directory)
        self.left_hand = tk.BooleanVar()
        self.right_hand = tk.BooleanVar(value=True)
        self.full_body = tk.BooleanVar()

        self.board_size = tk.StringVar(value=self.default_board_size)
        self.marker_length = tk.StringVar(value=self.default_marker_length)
        self.markers_dict_number = tk.StringVar(value=self.default_markers_dict_number)
        self.markers_bits_number = tk.StringVar(value=self.default_markers_bits_number)
        self.board_type = tk.StringVar(value=self.default_board_type)
        self.board_square_side_length = tk.StringVar(value=self.default_board_square_side_length)
        self.animal_calibration = tk.StringVar(value=self.default_animal_calibration)
        self.fisheye = tk.StringVar(value=self.default_fisheye)
        self.file_extension = tk.StringVar(value=self.default_file_extension)
        self.file_suffix = tk.StringVar(value=self.default_file_suffix)

        self.default_start_frame = tk.StringVar(value="0")
        self.default_stop_frame = tk.StringVar(value="1")
        self.default_plot_frame = tk.StringVar(value="0")
        self.default_multiTrim_val = tk.StringVar(value="1")
        self.default_recLen_val = tk.StringVar(value="0")
        self.default_lightOn_val = tk.StringVar(value="220")
        self.video_ROI_location = {}

        self.processing_variables = {
            'leftHand': 0,
            'rightHand': 0,
            'fullBody': 0,
            'calibration': 0
        }

        # Thread management
        self.current_thread_key = None
        self.threads = {
            'threadLhand': None,
            'threadRhand': None,
            'threadBody': None,
            'threadCalibration': None
        }

        self.stop_events = {
            'threadLhand': threading.Event(),
            'threadRhand': threading.Event(),
            'threadBody': threading.Event(),
            'threadCalibration': threading.Event()
        }

        self.string_mapping = {
            'leftHand': "Left",
            'rightHand': "Right",
            'fullBody': "Full Body",
            'calibration': "Calibration"
        }
        self.closeThread_on_demand = False
        self.interrupted_process = False
        self.processing_bodyPart = ''
        self.gui_directory = os.path.dirname(os.path.abspath(__file__))
        # Track changes for enabling/disabling "Apply" button
        self.changes_made = False

        # Track if configuration has been applied
        self.configuration_applied = False

        self.check_thread_status()

        # Set the title of the window
        self.title("Markerless Tracking GUI")

        # Center the window on the screen
        self.center_window(500, 400)

        # Start with the main menu
        self.main_menu()

    def center_window(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def main_menu(self):
        self.clear_window()

        # Reset window size to default when showing the main menu
        self.geometry("500x400")
        
        # Restore the default close behavior
        self.protocol("WM_DELETE_WINDOW", self.quit)

        # Disable buttons if configuration not applied
        state = tk.NORMAL if self.configuration_applied else tk.DISABLED

        configure_button = tk.Button(self, text="Configure", command=self.configure_page)
        calibrate_button = tk.Button(self, text="3D Calibration", command=self.calibration_page, state=state)
        # Define the button with different labels
        annotate_2d_button = tk.Button(self, text="2D Annotation", command=lambda: self.videoProcessing_page("Annotate 2D"), state=state)
        annotate_3d_button = tk.Button(self, text="3D Annotation", command=lambda: self.videoProcessing_page("Annotate 3D"), state=state)

        label_2d_button = tk.Button(self, text="2D Video Labelling", command=lambda: self.videoProcessing_page("Label 2D"), state=state)
        label_3d_button = tk.Button(self, text="3D Video Labelling", command=lambda: self.videoProcessing_page("Label 3D"), state=state)

        hand_features_button = tk.Button(self, text="Hand Features", command=self.hand_features, state=state)
        video_trimming_button = tk.Button(self, text="Video Trimming", command=self.videoTrim_window)

        exit_button = tk.Button(self, text="Exit", command=self.quit)

        button_ypadding = 15

        configure_button.pack(pady=button_ypadding)
        video_trimming_button.pack(pady=button_ypadding)
        annotate_2d_button.pack(pady=button_ypadding)
        calibrate_button.pack(pady=button_ypadding)
        annotate_3d_button.pack(pady=button_ypadding)
        label_2d_button.pack(pady=button_ypadding)
        label_3d_button.pack(pady=button_ypadding)
        hand_features_button.pack(pady=button_ypadding)
        exit_button.pack(pady=button_ypadding)

        # Thread management
        self.current_thread_key = None
        self.threads = {
            'threadLhand': None,
            'threadRhand': None,
            'threadBody': None,
            'threadCalibration': None
        }

        self.stop_events = {
            'threadLhand': threading.Event(),
            'threadRhand': threading.Event(),
            'threadBody': threading.Event(),
            'threadCalibration': threading.Event()
        }

        if self.closeThread_on_demand:
            self.close_threads()
            self.closeThread_on_demand = False
            self.check_thread_status()

    def configure_page(self):
        self.clear_window()

        # Back button
        back_button = tk.Button(self, text="←", command=lambda: self.check_apply_before_back("Main Page"), font=("Arial", 14))
        back_button.place(x=10, y=10)

        # Offset for widgets to start lower and not block the back button
        offset_frame = tk.Frame(self, height=50)
        offset_frame.pack()

        # Save Directory
        save_dir_frame = tk.Frame(self)
        save_dir_frame.pack(pady=5, fill=tk.X, padx=20)
        
        save_dir_entry = tk.Entry(save_dir_frame, textvariable=self.save_directory)
        save_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        save_dir_entry.bind("<KeyRelease>", self.enable_apply)  # Detect changes in the entry

        save_dir_button = tk.Button(save_dir_frame, text="Browse\nSaving Directory", command=self.select_save_directory)
        save_dir_button.pack(side=tk.RIGHT)

        # Checkboxes
        tk.Checkbutton(self, text="Left Hand", variable=self.left_hand, command=self.enable_apply).pack(pady=5)
        tk.Checkbutton(self, text="Right Hand", variable=self.right_hand, command=self.enable_apply).pack(pady=5)
        tk.Checkbutton(self, text="Full Body", variable=self.full_body, command=self.enable_apply).pack(pady=5)

        tk.Label(self, text="Video File Extension:").pack(pady=5)
        videoFile_extension_combobox = ttk.Combobox(self, textvariable=self.file_extension, values=['mp4', 'avi','mov', 'mpeg', 'flv', 'mkv'], 
                                           state="readonly")
        videoFile_extension_combobox.pack(pady=5)

        tk.Label(self, text="Video File Naming Suffix:").pack(pady=5)
        videoFile_suffix_combobox = ttk.Combobox(self, textvariable=self.file_suffix, values=['-cam([A-Z])', '_cam([A-Z])', '-cam([1-9])', '_cam([1-9])', '-cam([a-z])', '_cam([a-z])'], 
                                           state="readonly")
        videoFile_suffix_combobox.pack(pady=5)

        self.file_extension.trace_add("write", self.config_file_extension_overwrite)
        self.file_suffix.trace_add("write", self.config_file_extension_overwrite)

        # Apply button
        apply_button = tk.Button(self, text="Apply", state=tk.DISABLED, command=lambda: self.apply_changes("Config Page"))
        apply_button.pack(side=tk.BOTTOM, pady=10)

        # Adjust appearance of the disabled Apply button
        self.style_disabled_button(apply_button)

        self.apply_button = apply_button

        # Force update of widgets to ensure they display properly on first load
        self.update_idletasks()

    def calibration_page(self):
        self.clear_window()

        self.center_window(500, 400)

        back_button = tk.Button(self, text="←", command=lambda: self.check_apply_before_back("Main Page"), font=("Arial", 14))
        back_button.place(x=10, y=10)

        tk.Button(self, text="Change Board Parameters", command=self.board_parameters_page).pack(pady=5)
        tk.Button(self, text="Calibrate", command=self.calibrate).pack(pady=5)

        apply_button = tk.Button(self, text="Apply", state=tk.DISABLED, command=lambda: self.apply_changes("Calibration Page"))
        apply_button.pack(side=tk.BOTTOM, pady=10)

        # Adjust appearance of the disabled Apply button
        self.style_disabled_button(apply_button)

        self.apply_button = apply_button

    def board_parameters_page(self):
        self.clear_window()
        
        # Set a larger window size for the board parameters page
        self.center_window(500, 800)

        back_button = tk.Button(self, text="←", command=lambda: self.check_apply_before_back("Board Parameters Page"), font=("Arial", 14))
        back_button.place(x=10, y=10)

        tk.Label(self, text="Board Size:").pack(pady=5)
        board_size_entry = tk.Entry(self, textvariable=self.board_size)
        board_size_entry.pack(pady=5)

        tk.Label(self, text="Marker Length:").pack(pady=5)
        marker_length_entry = tk.Entry(self, textvariable=self.marker_length)
        marker_length_entry.pack(pady=5)

        tk.Label(self, text="Number of Bits in the Markers:").pack(pady=5)
        markers_bits_number_entry = tk.Entry(self, textvariable=self.markers_bits_number)
        markers_bits_number_entry.pack(pady=5)

        tk.Label(self, text="Number of Markers in the Dictionary:").pack(pady=5)
        markers_dict_number_entry = tk.Entry(self, textvariable=self.markers_dict_number)
        markers_dict_number_entry.pack(pady=5)

        tk.Label(self, text="Square Side Length (Charuco/CheckerBoard):").pack(pady=5)
        board_square_side_length_entry = tk.Entry(self, textvariable=self.board_square_side_length)
        board_square_side_length_entry.pack(pady=5)

        tk.Label(self, text="Board Type:").pack(pady=5)
        board_type_combobox = ttk.Combobox(self, textvariable=self.board_type, values=["Charuco", "Aruco", "Checkerboard"], 
                                           state="readonly")
        board_type_combobox.pack(pady=5)

        tk.Label(self, text="Animal Calibration:").pack(pady=5)
        animal_calibration_combobox = ttk.Combobox(self, textvariable=self.animal_calibration, values=["True", "False"], 
                                           state="readonly")
        animal_calibration_combobox.pack(pady=5)

        tk.Label(self, text="Fisheye Lense:").pack(pady=5)
        fisheye_combobox = ttk.Combobox(self, textvariable=self.fisheye, values=["True", "False"], 
                                           state="readonly")
        fisheye_combobox.pack(pady=5)

        # Change back to default button
        reset_button = tk.Button(self, text="Reset to Default", command=self.reset_board_parameters)
        reset_button.pack(pady=10)

        # Trace changes in the board parameters
        self.board_size.trace_add("write", self.enable_apply)
        self.marker_length.trace_add("write", self.enable_apply)
        self.markers_dict_number.trace_add("write", self.enable_apply)
        self.markers_bits_number.trace_add("write", self.enable_apply)
        self.board_square_side_length.trace_add("write", self.enable_apply)
        self.board_type.trace_add("write", self.enable_apply)
        self.animal_calibration.trace_add("write", self.enable_apply)
        self.fisheye.trace_add("write", self.enable_apply)

        apply_button = tk.Button(self, text="Apply", state=tk.DISABLED, command=lambda: self.apply_changes("Board Parameters Page"))
        apply_button.pack(side=tk.BOTTOM, pady=10)

        # Adjust appearance of the disabled Apply button
        self.style_disabled_button(apply_button)

        self.apply_button = apply_button

        # Force update of widgets to ensure they display properly on re-entry
        self.update_idletasks()

    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()

    def select_save_directory(self):
        selected_directory = filedialog.askdirectory()
        if selected_directory:
            self.save_directory.set(os.path.normpath(selected_directory))
            self.enable_apply()
        self.focus_force()  # Bring focus back to the main window
        self.lift()         # Lift the window to the front

    def reset_board_parameters(self):
        self.board_size.set(self.default_board_size)
        self.marker_length.set(self.default_marker_length)
        self.markers_dict_number.set(self.default_markers_dict_number)
        self.markers_bits_number.set(self.default_markers_bits_number)
        self.board_type.set(self.default_board_type)
        self.board_square_side_length.set(self.default_board_square_side_length)
        self.animal_calibration.set(self.default_animal_calibration)
        self.fisheye.set(self.default_fisheye)
        self.enable_apply()

    def enable_apply(self, *args):
        self.changes_made = True
        self.apply_button.config(state=tk.NORMAL, bg="lightblue", fg="black")

    def style_disabled_button(self, button):
        button.config(state=tk.DISABLED, bg="lightgrey", fg="darkgrey", disabledforeground="darkgrey")

    def check_apply_before_back(self, menu):
        if self.changes_made:
            result = messagebox.askyesno("Apply Changes", "Do you want to apply the changes you have made?")
            if result:
                self.apply_changes(menu)
        if menu == "Main Page":
            self.main_menu()
        elif menu == "Board Parameters Page":
            self.calibration_page()

    def videoProcessing_page(self, mode):
        self.processing_operation = mode
        existing_folders = False
        csv_files = False
        asked_for_file_deletion = False
        # Select directory for annotation 

        selected_directory = filedialog.askdirectory()
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
                                if messagebox.askyesno("Existing files", f"The folder {folder_name} already exists in {selected_directory} path. Do you want to DELETE and RE-RUN {mode}?"):    
                                    asked_for_file_deletion = True   
                                    if os.path.exists(folder_to_delete):
                                        shutil.rmtree(folder_to_delete)
                                else:
                                    asked_for_file_deletion = True
                                    existing_folders = True
                                    messagebox.showinfo("Warning","Exiting processing due to files already existing.")
                                    self.lift()
                                    break
                            elif asked_for_file_deletion and not existing_folders:
                                if os.path.exists(folder_to_delete):
                                    shutil.rmtree(folder_to_delete)
                                    existing_folders = False
            if existing_folders == False:
                self.input_directory = os.path.normpath(selected_directory)
                num_files, total_files_size_bytes, unique_recordings, videos_raw_folders = annotationFolders.count_video_files_and_size(self.input_directory, self.file_extension.get())
                self.total_files_size_MB = round(total_files_size_bytes / (1024 ** 2),2)
                if mode == "Annotate 2D":
                    self.num_processing_files = int(num_files)
                elif csv_files:
                    unique_recordings = annotationFolders.count_unique_csv_files(self.input_directory)
                    self.num_processing_files = int(unique_recordings)
                else:
                    self.num_processing_files = int(videos_raw_folders)
                                        
                # Check if the conditions are met
                if num_files > 30 or self.total_files_size_MB > 200:
                    proceed = messagebox.askyesno("Warning", f"There are {num_files} files (total size {self.total_files_size_MB}MB), which can take awhile to process. Are you sure you want to proceed?")
                    if proceed:
                        self.processing_window()                        
                else:
                    self.processing_window()     

    def processing_window(self):
        self.clear_window()

        # Set a larger window size for the processing window
        self.geometry("1000x800")

        self.protocol("WM_DELETE_WINDOW", self.on_processing_window_close)

        # Store that we are in the processing window
        self.in_processing_window = True

        self.files_processed = 0

        tk.Label(self, text=f"Current Input Directory: {self.input_directory }").pack(pady=10)
        tk.Label(self, text=f"Current Computation: {self.processing_operation }").pack(pady=10)

        self.progress_bar = ttk.Progressbar(self, length=400, mode='determinate')
        self.progress_bar.pack(pady=20)

        self.progress_label = tk.Label(self, text="Processing: Video 0/0")
        self.progress_label.pack(pady=5)

        self.estimated_time_label = tk.Label(self, text="Estimated remaining time: Computing...")
        self.estimated_time_label.pack(pady=5)

        self.output_text = ScrolledText(self, height=20, width=80)
        self.output_text.pack(pady=10)

        self.processing_variables = {
            'leftHand': self.left_hand.get(),
            'rightHand': self.right_hand.get(),
            'fullBody': self.full_body.get(),
            'calibration': 0
        }

        self.number_of_selected_bodyParts = sum(1 for value in self.processing_variables.values() if value == 1)

        self.start_threads()

    def calibration_window(self):
        self.clear_window()
        self.geometry("600x400")
        self.output_text = ScrolledText(self, height=20, width=80)
        self.output_text.pack(pady=10)

        self.processing_variables = {
            'leftHand': 0,
            'rightHand': 0,
            'fullBody': 0,
            'calibration': 1
        }

        self.number_of_selected_bodyParts = sum(1 for value in self.processing_variables.values() if value == 1)
        self.in_processing_window = True

        self.start_threads()
        # Processing complete
        #messagebox.showinfo("Calibration Complete.")
        #self.main_menu()
              
    # Created for communication with annotationFolders. If report_string is a directory
    # it means a file is being processed, thus it increments the number of files processed
    # updates the current file name, and calculates the elapsed time before continuing
    # to the update progress window. If report_string is not a directory, then it is meant
    # for reporting a problem with missing or existing files. If report_string starts with
    # a number (2D or 3D), then this pertains to missing files. However, if report_string
    # starts with a letter, it is to notify you that the files for 2D or 3D annotation already exist.
    # It always asks you if you want to continue checking the rest of the folder directories.
    # If reporting_string starts with "STD", this means it is a terminal/cmd message for calibration.
    # Since during calibration, the update bar always starts with a number a percent and a "|"
    # Thus, it looks for this string pattern via regex and if it matches it knows it is an update bar.
    # Update bar line gets overwritten on every new update to prevent printing every update on different
    # lines, overloading the screen and the user. If finished then it signals to stop the thread for calibration.
    def processing_communication(self,report_string):
        if os.path.exists(report_string):
            
            self.fileName = report_string
            if self.files_processed == 0:
                self.elapsedTime = 'Computing...'
            else:
                self.elapsedTime = time.perf_counter() - self.startProcTime
            self.update_progress()
            #self.after(5000, self.update_progress_regularly)
            self.files_processed+=1
        else:
            if report_string == "Finished":
                # Processing complete
                self.closeThread_on_demand = True
                
            elif report_string[0].isdigit():
                word_pairs = report_string.split(", ")
                current_task = word_pairs[0]
                missing_files = " ".join(word_pairs[1:])
                messagebox.showinfo("Warning",  f"You are missing {missing_files} files. Without these, you cannot perform {current_task}")
                self.closeThread_on_demand = True
            elif "STD" in report_string and self.in_processing_window:
                if "Finished" in report_string:
                    self.closeThread_on_demand = True
                    source_file_path = os.path.join(self.calibrationVid_directory , "calibration.toml")
                    calibration_file_names = ["calibration.toml", "detections.pickle"]
                    if os.path.exists(source_file_path):
                        destination_calibration_file = os.path.join(self.gui_directory, "calibration.toml")
                        # Remove a previous calibration file if it exists
                        if os.path.exists(destination_calibration_file):
                            os.remove(destination_calibration_file)
                        # Move the calibration file to the destination folder
                        for file_name in calibration_file_names:
                            source_path = os.path.join(self.calibrationVid_directory, file_name)
                            shutil.copy(source_path, self.gui_directory)  
                        print(f"File calibration.toml has been moved to '{self.gui_directory}'.")
                else:
                    display_string = report_string.split("\n", 1)[1]
                    match = re.search(r'(\d+)%\|.*\|', display_string)
                    if match:
                        self.output_text.delete("end-2l", "end-1l")
                        # Insert the new message at the end
                        self.output_text.insert(tk.END, display_string)
                    else:
                        self.output_text.insert(tk.END, display_string)

                    self.output_text.see(tk.END)
            elif "Video trimming" in report_string:
                messagebox.showinfo("Video Trim Complete",  report_string)
            else:
                messagebox.showinfo("Warning",  report_string)
                self.closeThread_on_demand = True
                    
                
    def update_progress(self):
        # Update progress bar
        self.progress_bar['value'] = (self.files_processed / self.num_processing_files) * 100
        self.progress_bar.update()

        # Update progress label
        if self.num_processing_files > 1:
            self.progress_label.config(text=f"Processing {self.processing_bodyPart}: Video {self.files_processed+1}/{self.num_processing_files} at location {self.fileName}")
        else:
            self.progress_label.config(text=f"Processing {self.processing_bodyPart}: Folder {self.files_processed+1}/{self.num_processing_files} at location {self.fileName}")

        # Calculate estimated time remaining
        if isinstance(self.elapsedTime, str) and self.num_processing_files > 1:
            self.estimated_time_label.config(text=f"Estimated remaining time: Computing...")
        elif self.num_processing_files == 1:
            self.estimated_time_label.config(text=f"Estimated remaining time: Track Console Below")
        else:
            avg_time_per_file = self.elapsedTime / self.files_processed
            estimated_time_remaining = avg_time_per_file * (self.num_processing_files - self.files_processed)
            if estimated_time_remaining < 100:
                self.estimated_time_label.config(text=f"Estimated remaining time: {int(estimated_time_remaining)} secs")
            elif estimated_time_remaining < 3600:
                estimated_minutes = int(estimated_time_remaining/60)
                estimated_seconds = int(estimated_time_remaining) - (estimated_minutes*60)
                self.estimated_time_label.config(text=f"Estimated remaining time: {estimated_minutes} min and {estimated_seconds} secs")
            else:
                estimated_hours = int(estimated_time_remaining/3600)
                estimated_minutes = int(estimated_time_remaining/60) - (estimated_hours*60)
                estimated_seconds = int(estimated_time_remaining) - (estimated_minutes*60)
                self.estimated_time_label.config(text=f"Estimated remaining time: {estimated_hours} hr, {estimated_minutes} min and {estimated_seconds} secs")

        # Simulate updating the processing information
        self.progress_label.update()
        self.estimated_time_label.update()
        
    def on_processing_window_close(self):
        if self.in_processing_window:  # Check if we're in the processing window
            if messagebox.askyesno("Terminate Process", "Are you sure you want to terminate the executing process?"):
                self.closeThread_on_demand = True
                self.interrupted_process = True
                time.sleep(0.5)
                self.in_processing_window = False
                self.protocol("WM_DELETE_WINDOW", self.quit)  # Reset protocol
                self.main_menu()
            else:
                self.lift()  # Bring window to front if cancel is selected
        else:
            self.quit()  # Allow normal closing when not in processing window

    def apply_changes(self, menu):
        # Implement logic to save the changes here
        print(f"Applied changes: Save Directory = {self.save_directory.get()}, Config Folder = {self.gui_directory}")
        if menu == 'Board Parameters Page':
            self.board_parameters_overwrite()
            print(f"Board Size = {self.board_size.get()}, Marker Length = {self.marker_length.get()}, Markers Number = {self.markers_dict_number.get()}, Board Type = {self.board_type.get()}")
        if menu == 'Config Page':
            self.change_body_annotation()
        self.changes_made = False
        self.apply_button.config(state=tk.DISABLED)
        self.style_disabled_button(self.apply_button)

        # Enable 2D Annotation and 3D Calibration buttons
        self.configuration_applied = True

    def calibrate(self):
        calibrationVid_directory = filedialog.askdirectory()
        if calibrationVid_directory:
            calibration_folder_name = os.path.basename(os.path.normpath(calibrationVid_directory))
            # Check if the folder name is not 'calibration'
            if calibration_folder_name != 'calibration':
                # Create the new folder path with 'calibration' as the name
                new_calibration_folder_path = os.path.join(os.path.dirname(os.path.normpath(calibrationVid_directory)), 'calibration')            
                # Rename the folder
                os.rename(os.path.normpath(calibrationVid_directory), new_calibration_folder_path)
                self.calibrationVid_directory = os.path.normpath(new_calibration_folder_path)
            else:
                self.calibrationVid_directory = os.path.normpath(calibrationVid_directory)
            

            contains_mp4 = any(file.endswith(self.file_extension.get()) for file in os.listdir(self.calibrationVid_directory) if os.path.isfile(os.path.join(self.calibrationVid_directory, file)))
            
            if contains_mp4:
                calibration_file_names = ["calibration.toml", "detections.pickle"]
                source_file_path = os.path.join(self.calibrationVid_directory, "calibration.toml")
                if os.path.exists(source_file_path):
                    for file_name in calibration_file_names:
                        source_path = os.path.join(self.calibrationVid_directory, file_name)

                        destination_calibration_file = os.path.join(self.gui_directory, "calibration.toml")
                        # Remove a previous calibration file if it exists
                        if os.path.exists(destination_calibration_file):
                            os.remove(destination_calibration_file)

                        shutil.copy(source_path, self.gui_directory)                    
                    messagebox.showinfo("Info",  f" No calibration needed. Folder: {self.calibrationVid_directory} Already contains calibration files. Files have now been moved to the default GUI Location")
                    self.main_menu()
                else:
                    #remove pickle file from a failed calibration
                    pickleFile = os.path.join(self.calibrationVid_directory, "detections.pickle")
                    if os.path.exists(pickleFile):
                        os.remove(pickleFile)
                    annotationFolders.create_folder_and_copy_files(self.gui_directory, os.path.dirname(self.calibrationVid_directory), "config.toml")
                    command = 'cd ' + os.path.dirname(self.calibrationVid_directory)
                    annotationFolders.execute_anaconda_command(command,self.processing_communication)

                    self.calibration_window()
            else:
                print(f"Calibration Video Directory: {self.calibrationVid_directory} Does Not Contain Any Videos With The Selected Video File Extension From Configuration")

    def board_parameters_overwrite(self):
        # Path to the original config.toml file
        
        original_config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.toml")
        print(f"Original Config Directory: {original_config_path}")
        # Load the existing config.toml as text
        with open(original_config_path, 'r') as file:
            config_content = file.read()

        # Define the new calibration section content without leading spaces
        new_calibration_content = (
            "[calibration]\n"
            f"board_type = \"{self.board_type.get().lower()}\"\n"
            f"board_size = [{int(self.board_size.get().split('x')[0])}, {int(self.board_size.get().split('x')[1])}]\n"
            f"board_marker_bits = {int(self.markers_bits_number.get())}\n"
            f"board_marker_dict_number = {int(self.markers_dict_number.get())}\n"
            f"board_marker_length = {float(self.marker_length.get())}\n"
            f"board_square_side_length = {int(self.board_square_side_length.get())}\n"
            f"animal_calibration = {self.animal_calibration.get().lower()}\n"
            f"fisheye = {self.fisheye.get().lower()}\n"
        )

        # Regular expression to match the [calibration] section
        calibration_pattern = re.compile(r'(\[calibration\][\s\S]*?)(\n\[\w+\]|\Z)', re.MULTILINE)
        config_content = re.sub(calibration_pattern, new_calibration_content + r'\2', config_content)

        # Save the updated config.toml in the selected directory
        updated_config_path = os.path.join(self.gui_directory, "config.toml")
        with open(updated_config_path, 'w') as file:
            file.write(config_content.strip() + "\n")  # Strip any trailing space and add a newline


        print(f"Updated config.toml saved at: {updated_config_path}")

    def config_file_extension_overwrite(self, *args):
        original_config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.toml")
        print(f"Original Config Directory: {original_config_path}")
        # Load the existing config.toml as text
        with open(original_config_path, 'r') as file:
            config_content = file.read()

        newExt = self.file_extension.get()
        fileEnd = self.file_suffix.get()
        # Define the patterns to search for
        video_extension_pattern = r"(video_extension\s*=\s*)'[^']*'"
        cam_regex_pattern = r"(cam_regex\s*=\s*)'[^']*'"

        # Use the variables in the replacement
        new_video_extension = rf"\1'{newExt}'"
        new_cam_regex = rf"\1'{fileEnd}'"

        # Perform the replacements
        config_content = re.sub(video_extension_pattern, new_video_extension, config_content)
        config_content = re.sub(cam_regex_pattern, new_cam_regex, config_content)

        # Save the updated config.toml in the selected directory
        updated_config_path = os.path.join(self.gui_directory, "config.toml")
        with open(updated_config_path, 'w') as file:
            file.write(config_content) 

        print(f"Updated config.toml saved at: {updated_config_path}")

    def start_threads(self):
        # Define the thread starting order and corresponding strings
        thread_conditions = [
            ('leftHand', 'threadLhand'),
            ('rightHand', 'threadRhand'),
            ('fullBody', 'threadBody'),
            ('calibration', 'threadCalibration')
        ]

        # Manage threads based on conditions
        for var_key, thread_key in thread_conditions:
            if self.processing_variables[var_key] == 1:
                if self.threads[thread_key] is None and self.current_thread_key is None:
                    self.current_thread_key = thread_key
                    if var_key == 'calibration':
                        command = 'anipose calibrate'
                        self.threads[thread_key] = threading.Thread(target=annotationFolders.execute_anaconda_command, args=(command,self.processing_communication))
                        self.threads[thread_key].start()
                        print(f"Thread for {self.string_mapping[var_key]} started.")
                    else:
                        # Start the thread if not already running
                        direction = self.string_mapping[var_key]
                        if direction == "Full Body":
                            self.processing_bodyPart = direction
                        else:
                            self.processing_bodyPart = direction + "_Hand"

                        self.startProcTime = time.perf_counter()
                        self.threads[thread_key] = threading.Thread(target=annotationFolders.process_folders, args=(self.input_directory,self.save_directory.get(),direction, self.file_extension.get(),self.processing_communication,self.processing_operation,self.gui_directory,self.stop_events[thread_key]))
                        self.threads[thread_key].start()
                        print(f"Thread for {direction} started.")
                elif not self.threads[thread_key].is_alive():
                    # Handle any specific logic for when the thread should be restarted if needed
                    direction = self.string_mapping[var_key]
                    print(f"Thread for {direction} finished")

    def close_threads(self):
        for thread_key in self.threads:
            if self.threads[thread_key] and self.threads[thread_key].is_alive():
                self.stop_events[thread_key].set()
                print("setting stop event as")
                print(self.stop_events[thread_key].is_set())
                time.sleep(1)
                self.threads[thread_key].join()
                print("thread is joined")
        
    def check_thread_status(self):
        """Check if the worker thread has finished and update the GUI accordingly."""
        if self.closeThread_on_demand:
            self.close_threads()
            self.number_of_selected_bodyParts -= 1
            if self.number_of_selected_bodyParts > 0:
                self.current_thread_key = None
                print(f"number_of_selected_bodyParts is {self.number_of_selected_bodyParts}")
                messagebox.showinfo("Info",  "Current processing of selected body part completed! Proceeding to next selected body part.")
                time.sleep(5)
                self.start_threads()
                self.closeThread_on_demand = False
                self.after(500, self.check_thread_status)
            else:
                if self.interrupted_process:
                    self.interrupted_process = False
                else:
                    messagebox.showinfo("Info",  "Processing is complete!")
                self.main_menu()
        else:
            # Continue checking periodically
            self.after(500, self.check_thread_status)  # Check every 500 ms


    def videoTrim_window(self):
        self.clear_window()

        # Set a larger window size for the processing window
        self.geometry("600x400")
        button_ypadding = 10
        back_button = tk.Button(self, text="←", command=lambda: self.check_apply_before_back("Main Page"), font=("Arial", 14))
        back_button.place(x=10, y=10)

        manual_trim_button = tk.Button(self, text="Manual", command=lambda: self.videoTrimming_page("Manual Trimming"))
        manual_trim_button.pack(pady=button_ypadding)

        automatic_trim_button = tk.Button(self, text="Automatic\n(Lights)", command=lambda: self.videoTrimming_page("Automatic Trimming"))
        automatic_trim_button.pack(pady=button_ypadding)

        video_vis_button = tk.Button(self, text="Video\nVisualisation", command=lambda: self.videoTrimming_page("Video Visualisation"))
        video_vis_button.pack(pady=button_ypadding)

    def videoTrimming_page(self, video_operation):
        # Select directory for annotation
        if video_operation == "Manual Trimming":
            selected_video_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.avi *.mkv *.mov *.flv *.mpeg"), ("All files", "*.*")])
            if selected_video_path:
                self.manual_videoTrim_window(os.path.normpath(selected_video_path))
            else:
                self.focus_force()  # Bring focus back to the main window
                self.lift()         # Lift the window to the front
        elif video_operation == "Automatic Trimming":
            selected_directory = filedialog.askdirectory()
            if selected_directory:
                self.automatic_videoTrim_window(os.path.normpath(selected_directory))
            else:
                self.focus_force()  # Bring focus back to the main window
                self.lift()         # Lift the window to the front

    def manual_videoTrim_window(self,video_path):
        
        self.clear_window()

        # Set a larger window size for the processing window
        self.geometry("1500x900")

        back_button = tk.Button(self, text="←", command=lambda: self.check_apply_before_back("Main Page"), font=("Arial", 14))
        back_button.place(x=10, y=10)
        
        button_ypadding = 10
        button_xpadding = 0

        # Define the layout frames
        top_frame = tk.Frame(self)
        top_frame.pack(pady=button_ypadding)

        input_frame = tk.Frame(self)
        input_frame.pack(pady=5)

        plot_frame = tk.Frame(self)
        plot_frame.pack(pady=button_ypadding)

        vidFile_suffix = self.file_suffix.get()
        # Add "Trim" button at the top
        trim_button = tk.Button(top_frame, text="Trim", command=lambda: videoTrim_functions.individualVid_trim(video_path, self.save_directory.get(), self.file_extension.get(), int(self.start_entry.get()), int(self.stop_entry.get()),vidFile_suffix[0:4]))
        trim_button.pack()

        # Add "Start Frame" label and input box
        start_label = tk.Label(input_frame, text="Start Frame:")
        start_label.grid(row=0, column=0, padx=button_xpadding, pady=button_ypadding, sticky="W")
        self.start_entry = tk.Entry(input_frame, width=10, textvariable=self.default_start_frame)
        self.start_entry.grid(row=0, column=1, padx=button_xpadding, pady=button_ypadding, sticky="W")

        # Add "Stop Frame" label and input box
        stop_label = tk.Label(input_frame, text="Stop Frame:")
        stop_label.grid(row=0, column=2, padx=button_xpadding, pady=button_ypadding, sticky="E")
        self.stop_entry = tk.Entry(input_frame, width=10, textvariable=self.default_stop_frame)
        self.stop_entry.grid(row=0, column=3, padx=button_xpadding, pady=button_ypadding, sticky="W")

        empty_label = tk.Label(input_frame, text="")
        empty_label.grid(row=0, column=4, padx=button_xpadding, pady=button_ypadding)       

        # Add "Plot Frame" label and input box
        plot_label = tk.Label(input_frame, text="Plot Frame:")
        plot_label.grid(row=1, column=0, padx=button_xpadding, pady=button_ypadding, sticky="W")

        # Add "Next" button with song symbol (right arrow)
        prev_button = tk.Button(input_frame, text="⏮", command=lambda: self.plot_frame(-1, video_path))
        prev_button.grid(row=1, column=1, padx=button_xpadding, pady=button_ypadding, sticky="E")

        self.plot_entry = tk.Entry(input_frame, width=10, textvariable=self.default_plot_frame)
        self.plot_entry.grid(row=1, column=2, padx=button_xpadding, pady=button_ypadding, sticky="W")

        # Add "Next" button with song symbol (right arrow)
        next_button = tk.Button(input_frame, text="⏭", command=lambda: self.plot_frame(1, video_path))
        next_button.grid(row=1, column=3, padx=button_xpadding, pady=button_ypadding, sticky="W")

        # Add "Plot" button that calls external function
        plot_button = tk.Button(input_frame, text="Plot", command=lambda: self.plot_frame(0, video_path))
        plot_button.grid(row=1, column=4, padx=button_xpadding, pady=button_ypadding, sticky="W")

        # Add matplotlib plot below buttons
        self.fig = Figure(figsize=(5, 3), dpi=300)
        self.ax = self.fig.add_subplot(111)  # Create an axis for the plot
        frame_number = int(self.plot_entry.get())
        videoTrim_functions.plot_frame(video_path, frame_number, self.ax)
        self.fig.tight_layout(pad=0.5)

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack()

        input_frame.grid_columnconfigure(0, weight=0)
        input_frame.grid_columnconfigure(1, weight=0)
        input_frame.grid_columnconfigure(2, weight=0)
        input_frame.grid_columnconfigure(3, weight=0)
        input_frame.grid_columnconfigure(4, weight=0)

        self.update_idletasks()

    def automatic_videoTrim_window(self,video_path):
        
        self.clear_window()

        # Set a larger window size for the processing window
        self.geometry("1500x900")
        
        back_button = tk.Button(self, text="←", command=lambda: self.check_apply_before_back("Main Page"), font=("Arial", 14))
        back_button.place(x=10, y=10)
        
        button_ypadding = 10
        button_xpadding = 10
        textbox_width = 6

        top_frame = tk.Frame(self)
        top_frame.pack(pady=button_ypadding)

        input_frame = tk.Frame(self)
        input_frame.pack(pady=5)

        plot_frame = tk.Frame(self)
        plot_frame.pack(pady=button_ypadding)

        vidFile_suffix = self.file_suffix.get()

        # Disable buttons if configuration not applied 
        state = tk.NORMAL if self.video_ROI_location else tk.DISABLED

        # Add "Trim" button at the top
        trim_button = tk.Button(top_frame, text="Trim", command=lambda: videoTrim_functions.automatic_trim(video_path, self.save_directory.get(), int(self.multiTrim_entry.get()), self.video_ROI_location, self.file_extension.get(), vidFile_suffix[0:4], int(self.recLen_entry.get()), self.processing_communication),state=state)
        trim_button.pack()

        # Adjust appearance of the disabled Apply button
        if state == tk.DISABLED:
            self.style_disabled_button(trim_button)
        else:
            trim_button.config(state=tk.NORMAL, bg="lightblue", fg="black")

        # Add matplotlib plot below buttons
        self.fig = Figure(figsize=(5, 3), dpi=300)
        self.ax = self.fig.add_subplot(111)  # Create an axis for the plot
        self.ax.axis('off')
        self.fig.tight_layout(pad=0.5)

        # Add "Start Frame" label and input box
        multiTrim_label = tk.Label(input_frame, text="Multiple trims within a video:")
        multiTrim_label.grid(row=0, column=0, padx=button_xpadding, pady=button_ypadding, sticky="W")
        self.multiTrim_entry = tk.Entry(input_frame, width=textbox_width, textvariable=self.default_multiTrim_val)
        self.multiTrim_entry.grid(row=0, column=1, padx=button_xpadding, pady=button_ypadding, sticky="W")

        # Add "Stop Frame" label and input box
        recLen_label = tk.Label(input_frame, text="OPTIONAL\nRecording Length (s):")
        recLen_label.grid(row=0, column=2, padx=button_xpadding, pady=button_ypadding, sticky="E")
        self.recLen_entry = tk.Entry(input_frame, width=textbox_width, textvariable=self.default_recLen_val)
        self.recLen_entry.grid(row=0, column=3, padx=button_xpadding, pady=button_ypadding, sticky="W")    

        # Add "Plot Frame" label and input box
        lightOn_label = tk.Label(input_frame, text="Light On Threshold (0-255):")
        lightOn_label.grid(row=1, column=0, padx=button_xpadding, pady=button_ypadding, sticky="W")
        self.lightOn_entry = tk.Entry(input_frame, width=textbox_width, textvariable=self.default_lightOn_val)
        self.lightOn_entry.grid(row=1, column=1, padx=button_xpadding, pady=button_ypadding, sticky="W")   

        ROI_button = tk.Button(input_frame, text="Select ROI", command=lambda: self.ROI_selection(video_path))
        ROI_button.grid(row=1, column=2, columnspan=2, padx=button_xpadding, pady=button_ypadding, sticky="W")

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack()

        input_frame.grid_columnconfigure(0, weight=0)
        input_frame.grid_columnconfigure(1, weight=0)
        input_frame.grid_columnconfigure(2, weight=0)
        input_frame.grid_columnconfigure(3, weight=0)

        self.update_idletasks()

    def plot_frame(self, frame_scroll, video_path):

        if frame_scroll == 1:
            current_frameNum = int(self.plot_entry.get())
            self.plot_entry.delete(0, tk.END)  # Clear the existing value
            self.plot_entry.insert(0, str(current_frameNum+1))  # Insert new value at the beginning
        elif frame_scroll == -1:
            current_frameNum = int(self.plot_entry.get())
            self.plot_entry.delete(0, tk.END)  # Clear the existing value
            self.plot_entry.insert(0, str(current_frameNum-1))  # Insert new value at the beginning

        frame_number = int(self.plot_entry.get()) # Get the frame number from input
        videoTrim_functions.plot_frame(video_path, frame_number, self.ax)  # Pass self.ax to the external function
        self.canvas.draw()  # Update the canvas to reflect changes

    def video_trimming(self,input_path,start_frame,stop_frame):
        vid_name = os.path.basename(input_path)
        base_name, ext = os.path.splitext(vid_name)
        file_suffix = self.file_suffix.get()
        if not ext == self.file_extension.get():
            raise ValueError("The file does not have the video file extension selected at Configuration.")
        # Find the position of '_cam[A-Z]'
        if file_suffix[0:4] not in base_name:
            raise ValueError(f"Filename does not contain '{file_suffix[0:4]}'.")
        # Insert '_trimmed' before '_cam'
        trimmed_base_name = base_name.replace(file_suffix[0:4], '_trimmed' + file_suffix[0:4])
        # Construct the new filename with '_trimmed'
        new_file_name = f"{trimmed_base_name}{ext}"
        # Construct the new path in the output directory
        video_output_path = os.path.join(self.save_directory.get(), new_file_name)

        videoTrim_functions.trim_video_ffmpeg(input_path, video_output_path, start_frame, stop_frame)

    def ROI_selection(self,input_path):
        self.video_ROI_location = {}
        batches = {}
        ROI_video_rootFolder = ''
        var = tk.BooleanVar(value=False)
        for root, dirs, files in os.walk(input_path):
            if any(file.endswith(self.file_extension.get()) for file in files):
                for file in files:
                    if file.endswith(self.file_extension.get()):
                        ROI_video_rootFolder = root
                        # Process the .mp4 file
                        batch_name = file.split('cam')[0]
                        # Add the file to the corresponding batch
                        if batch_name not in batches:
                            batches[batch_name] = []
                        batches[batch_name].append(file)

                        
                        #video_ROI_location[file] = {'x': x, 'y': y, 'width': width, 'height': height}
                
                # Exit from all loops after processing the mp4 files
                break
        first_batch = list(batches.keys())[0]
        if first_batch:
            for file in batches[first_batch]:
                ROI_video_file = os.path.join(ROI_video_rootFolder, file)
                print(f"Processing video file: {ROI_video_file}")
                self.video_ROI_location[file] = videoTrim_functions.checkROI(ROI_video_file, 1, self.ax, self.canvas, var)

        self.fig.clear()  # This clears the entire figure including all axes
        self.ax = self.fig.add_subplot(111)  # Add the axis back if needed
        self.canvas.draw()  # Redraw the canvas to show the cleared figure

        print(self.video_ROI_location)
        messagebox.showinfo("ROI Selection Complete", "ROI Selection Complete.")
        self.automatic_videoTrim_window(os.path.normpath(input_path))

    def hand_features(self):
        calibration_string = f"Calibrating with Board Size: {self.board_size.get()}, Marker Length: {self.marker_length.get()}, Markers Number: {self.markers_dict_number.get()}, Board Type: {self.board_type.get()}"
        print(calibration_string)

    def change_body_annotation(self):
        
        if self.changes_made:
            # The new configuration you want to use (static replacements)
            hand_scheme = '''scheme = [
    ["WRIST", "THUMB_CMC", "THUMB_MCP", "THUMB_IP", "THUMB_TIP"],
    ["WRIST", "INDEX_FINGER_MCP", "INDEX_FINGER_PIP", "INDEX_FINGER_DIP", "INDEX_FINGER_TIP"],
    ["WRIST", "MIDDLE_FINGER_MCP", "MIDDLE_FINGER_PIP", "MIDDLE_FINGER_DIP", "MIDDLE_FINGER_TIP"],
    ["WRIST", "RING_FINGER_MCP", "RING_FINGER_PIP", "RING_FINGER_DIP", "RING_FINGER_TIP"],
    ["WRIST", "PINKY_MCP", "PINKY_PIP", "PINKY_DIP", "PINKY_TIP"]
]'''

            hand_constraints = '''constraints = [
    ["WRIST", "THUMB_CMC"], ["THUMB_CMC", "THUMB_MCP"], ["THUMB_MCP", "THUMB_IP"], ["THUMB_IP", "THUMB_TIP"],
    ["WRIST", "INDEX_FINGER_MCP"], ["INDEX_FINGER_MCP", "INDEX_FINGER_PIP"], ["INDEX_FINGER_PIP", "INDEX_FINGER_DIP"], ["INDEX_FINGER_DIP", "INDEX_FINGER_TIP"],
    ["WRIST", "MIDDLE_FINGER_MCP"], ["MIDDLE_FINGER_MCP", "MIDDLE_FINGER_PIP"], ["MIDDLE_FINGER_PIP", "MIDDLE_FINGER_DIP"], ["MIDDLE_FINGER_DIP", "MIDDLE_FINGER_TIP"],
    ["WRIST", "RING_FINGER_MCP"], ["RING_FINGER_MCP", "RING_FINGER_PIP"], ["RING_FINGER_PIP", "RING_FINGER_DIP"], ["RING_FINGER_DIP", "RING_FINGER_TIP"],
    ["WRIST", "PINKY_MCP"], ["PINKY_MCP", "PINKY_PIP"], ["PINKY_PIP", "PINKY_DIP"], ["PINKY_DIP", "PINKY_TIP"]
]'''

            hand_angles = '''thumb_1 = ["THUMB_CMC", "THUMB_MCP", "THUMB_IP"]
thumb_2 = ["THUMB_MCP", "THUMB_IP", "THUMB_TIP"]
index_1 = ["INDEX_FINGER_MCP", "INDEX_FINGER_PIP", "INDEX_FINGER_DIP"]
index_2 = ["INDEX_FINGER_PIP", "INDEX_FINGER_DIP", "INDEX_FINGER_TIP"]
middle_1 = ["MIDDLE_FINGER_MCP", "MIDDLE_FINGER_PIP", "MIDDLE_FINGER_DIP"]
middle_2 = ["MIDDLE_FINGER_PIP", "MIDDLE_FINGER_DIP", "MIDDLE_FINGER_TIP"]
ring_1 = ["RING_FINGER_MCP", "RING_FINGER_PIP", "RING_FINGER_DIP"]
ring_2 = ["RING_FINGER_PIP", "RING_FINGER_DIP", "RING_FINGER_TIP"]
pinky_1 = ["PINKY_MCP", "PINKY_PIP", "PINKY_DIP"]
pinky_2 = ["PINKY_PIP", "PINKY_DIP", "PINKY_TIP"]
'''

            #
            body_scheme = '''scheme = [
    ["LEFT_SHOULDER","LEFT_ELBOW", "LEFT_WRIST", "LEFT_PINKY"],
    ["LEFT_SHOULDER","LEFT_ELBOW", "LEFT_WRIST", "LEFT_INDEX"],
    ["LEFT_SHOULDER","LEFT_ELBOW", "LEFT_WRIST", "LEFT_THUMB"],
    ["RIGHT_SHOULDER","RIGHT_ELBOW", "RIGHT_WRIST", "RIGHT_PINKY"],
    ["RIGHT_SHOULDER","RIGHT_ELBOW", "RIGHT_WRIST", "RIGHT_INDEX"],
    ["RIGHT_SHOULDER","RIGHT_ELBOW", "RIGHT_WRIST", "RIGHT_THUMB"],
    ["RIGHT_SHOULDER", "LEFT_SHOULDER"],
    ["RIGHT_SHOULDER", "RIGHT_HIP", "RIGHT_KNEE", "RIGHT_ANKLE", "RIGHT_HEEL"],
    ["RIGHT_SHOULDER", "RIGHT_HIP", "RIGHT_KNEE", "RIGHT_ANKLE",      "RIGHT_FOOT_INDEX"],
    ["LEFT_SHOULDER", "LEFT_HIP", "LEFT_KNEE", "LEFT_ANKLE", "LEFT_HEEL"],
    ["LEFT_SHOULDER", "LEFT_HIP", "LEFT_KNEE", "LEFT_ANKLE", "LEFT_FOOT_INDEX"],
    ["MOUTH_RIGHT", "MOUTH_LEFT"],
    ["RIGHT_EAR", "RIGHT_EYE_OUTER", "RIGHT_EYE", "RIGHT_EYE_INNER", "NOSE"],
    ["LEFT_EAR", "LEFT_EYE_OUTER", "LEFT_EYE", "LEFT_EYE_INNER", "NOSE"]
    ]
'''

            body_constraints = '''constraints = [
    ["NOSE","LEFT_EYE_INNER"],["NOSE","RIGHT_EYE_INNER"],["LEFT_EYE_INNER", "LEFT_EYE"],["LEFT_EYE", "LEFT_EYE_OUTER"],
    ["RIGHT_EYE_INNER", "RIGHT_EYE"],["RIGHT_EYE", "RIGHT_EYE_OUTER"],["LEFT_EYE_OUTER", "LEFT_EAR"],["RIGHT_EYE_OUTER","RIGHT_EAR"],
    ["MOUTH_LEFT", "MOUTH_RIGHT"],["LEFT_SHOULDER", "RIGHT_SHOULDER"],["LEFT_SHOULDER", "LEFT_ELBOW"],["LEFT_ELBOW", "LEFT_WRIST"],
    ["LEFT_WRIST", "LEFT_PINKY"],["LEFT_WRIST", "LEFT_THUMB"],["LEFT_WRIST", "LEFT_INDEX"],["LEFT_INDEX","LEFT_THUMB"],
    ["LEFT_SHOULDER", "LEFT_HIP"],["LEFT_HIP","RIGHT_HIP"],["LEFT_HIP","LEFT_KNEE"],["LEFT_KNEE","LEFT_ANKLE"],
["LEFT_ANKLE", "LEFT_HEEL"],["LEFT_ANKLE", "LEFT_FOOT_INDEX"],["LEFT_FOOT_INDEX", "LEFT_HEEL"],["RIGHT_SHOULDER", "RIGHT_ELBOW"],
    ["RIGHT_ELBOW", "RIGHT_WRIST"],["RIGHT_WRIST", "RIGHT_THUMB"],["RIGHT_WRIST", "RIGHT_INDEX"],["RIGHT_INDEX","RIGHT_PINKY"],
["RIGHT_WRIST", "RIGHT_PINKY"],["RIGHT_SHOULDER", "RIGHT_HIP"],["RIGHT_HIP","RIGHT_KNEE"],["RIGHT_KNEE","RIGHT_ANKLE"],
["RIGHT_ANKLE", "RIGHT_HEEL"],["RIGHT_ANKLE", "RIGHT_FOOT_INDEX"],["RIGHT_FOOT_INDEX", "RIGHT_HEEL"]
]'''

            body_angles = '''right_elbow_flexion = ["RIGHT_SHOULDER", "RIGHT_ELBOW", "RIGHT_WRIST"]
left_elbow_flexion = ["LEFT_SHOULDER", "LEFT_ELBOW", "LEFT_WRIST"]
'''

            if self.full_body.get():
                selected_scheme = body_scheme
                selected_constraints = body_constraints
                selected_angles = body_angles
            else:
                selected_scheme = hand_scheme
                selected_constraints = hand_constraints
                selected_angles = hand_angles
            original_config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.toml")
            print(f"Original Config Directory: {original_config_path}")
            # Load the existing config.toml as text
            with open(original_config_path, 'r') as file:
                content = file.read()

            # Update the [labeling] scheme section
            content = re.sub(r'\[labeling\]\s+scheme\s*=\s*\[.*?\](\s*],?)', f'[labeling]\n{selected_scheme}', content, flags=re.DOTALL)
                
            # Update the [triangulation] constraints section
            content = re.sub(r'constraints\s*=\s*\[.*?\](\s*],?)', f'{selected_constraints}', content, flags=re.DOTALL)

            # Update the [angles] section
            content = re.sub(r'\[angles\].*?$', f'[angles]\n{selected_angles}', content, flags=re.DOTALL)

            # Save the updated config.toml in the selected directory
            updated_config_path = os.path.join(self.gui_directory, "config.toml")
            with open(updated_config_path, 'w') as file:
                file.write(content) 

            print(f"Updated config.toml saved at: {updated_config_path}")

# Run the application
if __name__ == "__main__":
    app = MyApp()
    app.mainloop()

