#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 12 08:33:58 2023

@author: hd04
"""

import cv2
import numpy as np

def detectLightChange(videoPath, vid_ROI, recording_length, run_nums):
    cap = cv2.VideoCapture(videoPath)
    video_length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(vid_ROI)
    print(videoPath)
    print(video_length)

    frame_number=0
    light_on_array = np.ones((run_nums,1))
    light_off_array = np.ones((run_nums,1)) + 1
    
    x = vid_ROI[0]
    y = vid_ROI[1]
    width = vid_ROI[2]
    height = vid_ROI[3]
 
    light_on = False
    light_on_frameNumb=0
    light_on_inc = 0
    light_off_inc = 0
    frame_off = 20

    pixelNum_threshold = 1
    pixelIntensity_threshold = 245
    
    while True:
        ret, frame = cap.read()

        if not ret:
            if light_on_inc > 0 and light_off_array[light_on_inc-1] <= light_on_array[light_on_inc-1]:
                light_off_array[light_on_inc-1] = light_on_array[light_on_inc-1] + 1
            break   

        if light_off_inc == run_nums:
            break
        frame_number = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        frameROI = frame[y:y+height, x:x+width]
        roiRed = frameROI[:, :,2]
        redPixels = sum(sum(row) for row in roiRed > pixelIntensity_threshold)

        if redPixels > pixelNum_threshold and light_on==False and frame_number>frame_off:
            print("Light turned on!")
            print(frame_number)
            
            light_on_array[light_on_inc] = frame_number
            light_on_frameNumb = frame_number
            light_on_inc += 1
            light_on=True                
        elif recording_length > 0 and light_on:
            light_off_array[light_off_inc] = light_on_array[light_on_inc - 1] + (recording_length*60) + 1
            if light_off_array[light_off_inc] >= video_length:
                print('longer recording')
                light_off_array[light_off_inc] = video_length-1
            frame_off = light_off_array[light_off_inc]
            light_off_inc +=1
            light_on=False
            if run_nums == 1:
                break
        elif redPixels < pixelNum_threshold and light_on and frame_number >= light_on_frameNumb+30:
            print("Light turned off!")
            print(frame_number)
            light_off_array[light_off_inc] = frame_number
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

    if run_nums < 2:
        light_on_array = int(light_on_array[0][0])
        light_off_array = int(light_off_array[0][0])
        
    return light_on_array,light_off_array,video_length

#video_path = 'C:\\Users\\ej06\\Coins_analysis\\CT_005\Day3\\Coin_task\\Coin_task_1-camA.mp4'
#vid_ROI = (15,818,57,53)
#recording_length = 65
#on_array,off_array,cam_frame_number = detectLightChange(video_path,vid_ROI,recording_length,1)
