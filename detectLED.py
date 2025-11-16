#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: Apache-2.0
import cv2
import numpy as np

def detectLightChange(videoPath, vid_ROI, recording_length, run_nums, led_intensity):
    cap = cv2.VideoCapture(videoPath)
    video_length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    frame_number=0
    light_on_array = np.ones((run_nums,1))
    light_off_array = np.ones((run_nums,1)) + 1
    
    x = vid_ROI[0]
    y = vid_ROI[1]
    width = vid_ROI[2]
    height = vid_ROI[3]
 
    light_on = False
    light_on_frameNumb=0
    light_on_inc = 0 #indicating the number of light_on events
    light_off_inc = 0 #indicating the number of light_off events
    frame_off = 20 #initialisation for a frame_off number, set at 20 frames, meaning the initial 20 frames are ignored for the very first light detection to avoid errors

    pixelNum_threshold = 1
    pixelIntensity_threshold = led_intensity
    
    while True:
        ret, frame = cap.read()

        if not ret:
            #If no frame is read and if a light has been detected at least once AND the light_off 
            #of the last event is lower than the light_on at the last event, then set the light off
            #of the last event to be 1 frame higher than the light_on. This prevents scenarios where
            #a light on is detected but the light never switches off by the end of the recording.
            if light_on_inc > 0 and light_off_array[light_on_inc-1] <= light_on_array[light_on_inc-1]:
                light_off_array[light_on_inc-1] = light_on_array[light_on_inc-1] + 1
            break   

        #Detects if the light_off events are equal to the number of runs, hence not wasting time on
        #scanning more frames as it is not necessary and would not generate a mistake.
        if light_off_inc == run_nums:
            break

        frame_number = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        frameROI = frame[y:y+height, x:x+width]
        roiRed = frameROI[:, :,2] #extracts only the red values of the RGB triplet
        #indicates if there are any pixels lighting up in red, and a red pixel light is
        #defined as a pixel within the ROI selected that is higher than the pixel intensity
        #threshold set. The highest possible pixel intensity is 255, which represents the most intense red light
        redPixels = sum(sum(row) for row in roiRed > pixelIntensity_threshold)

        #Checks if there are enough red pixels (above set threshold) and if light hasn't been on
        #AND the frame number is larger than the last time a light was off (if it hasn't been off yet there's an initial threshold of 20 frames)
        if redPixels > pixelNum_threshold and light_on==False and frame_number>frame_off:
            print("Light turned on!")
            print(frame_number)
            
            light_on_array[light_on_inc] = frame_number
            light_on_frameNumb = frame_number
            light_on_inc += 1
            light_on=True   
        #Goes into that statement only if the user sets a recording length            
        elif recording_length > 0 and light_on:
            light_off_array[light_off_inc] = light_on_array[light_on_inc - 1] + (recording_length*60) + 1
            #Detects if the required length of the video exeeds the actual video length
            if light_off_array[light_off_inc] >= video_length:
                print('longer recording')
                light_off_array[light_off_inc] = video_length-1
            frame_off = light_off_array[light_off_inc]
            light_off_inc +=1
            light_on=False
            if run_nums == 1:
                break
        #If no recording length is provided, then it checks if the light is off based on:
        #number of red pixels, the light being on beforehand, and the frame number being larger than the light_on event + 30 frames (buffer)
        elif redPixels < pixelNum_threshold and light_on and frame_number >= light_on_frameNumb+30:
            print("Light turned off!")
            print(frame_number)
            light_off_array[light_off_inc] = frame_number
            #Detects if the required length of the video exeeds the actual video length
            if light_off_array[light_off_inc] >= video_length:
                print('longer recording')
                light_off_array[light_off_inc] = video_length-1
            frame_off = light_off_array[light_off_inc]
            light_off_inc +=1
            light_on=False

        if cv2.waitKey(1) & 0xFF == ord('q'):
            #Catch statements to detected if light-on event is detected BUT
            # the light-off event is missing
            if light_on_inc > 0 and light_off_array[light_on_inc-1] <= light_on_array[light_on_inc-1]:
                light_off_array[light_on_inc-1] = light_on_array[light_on_inc-1] + 1
            break
                
    cap.release()
    cv2.destroyAllWindows()

    #Convert light_on and _off arrays to ints in case only 1 run number was indicated
    if run_nums < 2:
        light_on_array = int(light_on_array[0][0])
        light_off_array = int(light_off_array[0][0])
        
    return light_on_array,light_off_array,video_length
