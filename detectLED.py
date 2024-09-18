#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 12 08:33:58 2023

@author: hd04
"""

import cv2
import numpy as np

def detectLightChange(videoPath, vid_ROI, run_nums):
    cap = cv2.VideoCapture(videoPath)

    print(vid_ROI)
    print(videoPath)

    frame_number=0
    light_on_array = np.zeros((run_nums,1))
    light_off_array = np.zeros((run_nums,1))
    
    x = vid_ROI[0]
    y = vid_ROI[1]
    width = vid_ROI[2]
    height = vid_ROI[3]
 
    light_on = False
    light_on_frameNumb=0
    light_on_inc = 0
    light_off_inc = 0
    
    while True:
        ret, frame = cap.read()
        frame_number = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        if not ret:
            break       

        frameROI = frame[y:y+height, x:x+width]
        roiRed = frameROI[:, :,2]
        redPixels = sum(sum(row) for row in roiRed>245)

        if redPixels>1 and light_on==False and frame_number>80:
            print("Light turned on!")
            print(frame_number)
            
            light_on_array[light_on_inc] = frame_number
            light_on_frameNumb = frame_number
            light_on_inc += 1
            light_on=True                

        elif redPixels<1 and light_on and frame_number >= light_on_frameNumb+30:
            print("Light turned off!")
            print(frame_number)
            light_off_array[light_off_inc] = frame_number
            light_off_inc +=1
            light_on=False
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        frame_number += 1
        
    cap.release()
    cv2.destroyAllWindows()

    if run_nums < 2:
        light_on_array = int(light_on_array[0][0])
        light_off_array = int(light_off_array[0][0])
    return light_on_array,light_off_array,frame_number+1

#video_path = '/Volumes/data/Group/Plasticity/Projects/hristo_grasping/Behavioural_data/CT_011/Object_10/Action_Towards/2024-05-16-14-17-54-camC.mp4'

#on_array,off_array,cam_frame_number = detectLightChange(video_path,5)
