# TrackStudio
TrackStudio is an interactive open-source toolkit for markerless tracking. It provides a visual interface enabling trimming of videos, synchronising between cameras, using MediaPipe and Anipose for 2D and 3D tracking (including camera calibration) with result visualisation, without the requirement of any coding. It is aimed at any user regardless of their technical level of expertise. Advanced users can still enhance the utility of the toolkit and easily replace the methods used for 2D and 3D markerless tracking (see "Code Architecture" section below).

Check out the [TrackStudio paper](https://www.biorxiv.org) for detailed information on how to install and use TrackStudio and general advice on markerless tracking video recordings and setup.

Below is included further information on multi-camera recording setups in OBS, light-based approach for cameras synchronisation, and details on code implementation.

## Multi-camera recording setup via OBS software

In OBS

## Light-based camera synchronisation

To synchronise cameras

## Code Architecture

The main Python script, Python_TS_GUI.py, contains the graphical user interface (GUI) and operates/calls all the main functions for the toolkit. It contains the settings for the GUI and visualisation as well as setting variables for executing markerless tracking operations (e.g. video directory, file extensions, body part that is selected for tracking, calibration settings, etc.). All the GUI pages are defined in their respective functions noted with “_page” in their function name; the processing windows within each page are defined in their respective functions noted with “_window” in their function name.

Whenever processing is required, it is submitted via starting a thread, so that visualisation and updates are provided in parallel with the processing. Starting a new thread is handled by the “start_threads” function, which detects the processing that is submitted (e.g. calibration) and starts a unique thread for it. Checking and closing threads are provided by “check_thread_status” and “close_threads” functions respectively. 

Communications between the processing thread and the main thread for the GUI are handled via the “processing_communication” function, which can be passed to functions outside of the main Python_TS_GUI.py script via “safe_gui_callback” function.

Video Trimming is done either manually or automatically (via LED detection). All the functions pertaining to video trimming are contained within videoTrim_functions and are called from the Python_TS_GUI.py script when the respective buttons are pressed. 

The rest of the GUI functionality is mainly handled by functions within the “annotationFolders.py” script, called from the Python_TS_GUI.py script. For 2D annotation, it automatically navigates to the relevant directory and executes a MediaPipe-based script via a MediaPipe-specific virtual environment. Similarly, for calibration, triangulation, and video labelling, it automatically navigates to the relevant directory and executes relevant Anipose commands via the main environment, which contains not only the GUI functionality but also Anipose-preconfigured packages.

If people want to call the GUI via an Anaconda Command Prompt window, they can do so by navigating to the GUI’s folder, activating the GUI and Anipose environment (“conda activate aniposeEnv”), followed by running the main Python_TS_GUI.py script (“python Python_TS_GUI.py”).

If people want to change the methods for 2D/3D tracking or calibration, they can do so by pre-packaging an environment and changing the relevant lines in the “annotationFolders.py” script for that tracking functionality. For example, if someone wants to change how 2D annotations are done, they only need to change 2 lines within the “annotationFolders.py” script:

Line 28: execute_anaconda_command(f"conda run -n mediaPipeEnv python {run2D_dir} \"{path}\" \"{dest_folder}\" \"{selected_bodypart}\"",report_callback)

Line 56: execute_anaconda_command(f"conda run -n mediaPipeEnv python {run2D_dir} \"{path}\" \"{folder_path}\" \"{selected_bodypart}\"",report_callback)

Both lines are the same, and would need to be updated in the same manner:
1)	Substitute the “run2D.py” script within the GUI folder with the method that you want to use – the script name should remain “run2D.py”. Currently “run2D.py” script is having 3 inputs for (1) the video directory that you want to annotate, (2) the output directory, and (3) the selected body part for annotation (“video_dir, output_dir, bodypart_selection”) – if your function uses more inputs, this part of the line should also be changed.
2)	Change the “mediaPipeEnv” to the name of the virtual environment for the tool that you are using for your method (e.g. OpenPose).

## License
TrackStudio is released under the Apache-2.0 license.  
See `LICENSE` and `NOTICE` for details and third-party attributions.
