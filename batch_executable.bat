@echo off
REM Activate the Anaconda environment
call C:\Users\hrist\Anaconda3\Scripts\activate.bat aniposeEnv
REM Run your Python script in a new minimized window
start /b python D:\Markerless_Tracking_GUI_git\Python_TS_GUI.py
