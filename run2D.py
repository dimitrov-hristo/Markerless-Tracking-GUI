# SPDX-License-Identifier: Apache-2.0
import numpy as np
import cv2 as cv
import pickle
pickle.HIGHEST_PROTOCOL = 4
import os
import mediapipe as mp
import sys
import pandas as pd

def annotate_2D(mp_hands, bodyparts, path, cap, points, selected_bodypart, output_dir):

    with mp_hands.Hands(model_complexity=1, min_tracking_confidence = 0.5, min_detection_confidence = 0.5) as hands: 
        frame_num = -1
        while cap.isOpened():
            ret, frame = cap.read()
            if ret == True:     
                frame_num += 1
                image_height, image_width, _ = frame.shape
            
                image = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
                
                #Note that handedness is determined assuming the input image is mirrored,
                #i.e., taken with a front-facing/selfie camera with images flipped horizontally.
                #If it is not the case, please swap the handedness output in the application.
                image = cv.flip(image, 1)
                
                results = hands.process(image)
                
                if results.multi_hand_landmarks: 
                    
                    if len(results.multi_hand_landmarks) == 1:
                        hand = results.multi_hand_landmarks[0]
                    
                        if(results.multi_handedness[0].classification[0].label == selected_bodypart):
                            for lm in mp_hands.HandLandmark:
                                points[frame_num][lm.value][0] = image_width - hand.landmark[lm.value].x * image_width
                                points[frame_num][lm.value][1] = hand.landmark[lm.value].y * image_height
                                points[frame_num][lm.value][2] = 1 #hand.landmark[lm.value].visibility ALWAYS ZERO, UNCLEAR HOW TO UNLOCK
                        else:
                            for lm in mp_hands.HandLandmark:
                                points[frame_num][lm.value][0] = np.nan
                                points[frame_num][lm.value][1] = np.nan
                                points[frame_num][lm.value][2] = np.nan
                    elif len(results.multi_hand_landmarks) == 2:
                        for num, hand in enumerate(results.multi_hand_landmarks):
                            if(results.multi_handedness[num].classification[0].label == selected_bodypart):
                                #print("Right - 2")
                                for lm in mp_hands.HandLandmark:
                                    points[frame_num][lm.value][0] = image_width - hand.landmark[lm.value].x * image_width
                                    points[frame_num][lm.value][1] = hand.landmark[lm.value].y * image_height
                                    points[frame_num][lm.value][2] = 1 #hand.landmark[lm.value].visibility ALWAYS ZERO, UNCLEAR HOW TO UNLOCK
                        
                else:
                    for lm in mp_hands.HandLandmark:
                        points[frame_num][lm.value][0] = np.nan
                        points[frame_num][lm.value][1] = np.nan
                        points[frame_num][lm.value][2] = np.nan
            
            else:
                break
            
        cap.release()
        
        
        orderofbpincsv=bodyparts
        n_frames,n_joints, c = points.shape
        data = points.reshape(n_frames, n_joints*c)
        frameindex=list([i for i in range(n_frames)])

        scorer = 'DLC_Model_Name'
        index = pd.MultiIndex.from_product([[scorer], orderofbpincsv, ['x', 'y', 'likelihood']],names=['scorer', 'bodyparts', 'coords'])
        frame = pd.DataFrame(np.array(data,dtype=float), columns = index, index = frameindex)
        
        save_directory = os.path.dirname(output_dir)
        save_file_name = os.path.splitext(os.path.basename(path))[0]
        pose2D_folder = os.path.join(save_directory, 'pose-2d')
        if not os.path.exists(pose2D_folder):
            os.makedirs(pose2D_folder)
        save_path = os.path.join(pose2D_folder, save_file_name)

        frame.to_hdf(save_path+".h5", key = "whatever", mode='w')
        frame.to_csv(save_path+".csv")
        
        with open(save_path+".pickle", "wb") as file:
            pickle.dump(frame, file, protocol = 4)

def mark_holistic_video(mp_holistic, bodyparts, path, cap, points, output_dir):

    with mp_holistic.Holistic(static_image_mode=False,
    model_complexity=1, 
    min_detection_confidence=0.5, 
    min_tracking_confidence=0.5) as holistic: 
        
        frame_num = -1

        while cap.isOpened():
            ret, frame = cap.read()
            if ret == True:     
                frame_num += 1
                image_height, image_width, _ = frame.shape
            
                image = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
                
                results = holistic.process(image)
                
                if results.pose_landmarks: 
                    pose_landmarks = results.pose_landmarks.landmark
                    
                    for lm in mp_holistic.PoseLandmark:
                        index = lm.value
                        points[frame_num][index][0] = pose_landmarks[index].x * image_width
                        points[frame_num][index][1] = pose_landmarks[index].y * image_height
                        points[frame_num][index][2] = pose_landmarks[index].visibility
                
                else:
                    for lm in mp_holistic.PoseLandmark:
                        index = lm.value
                        points[frame_num][index][0] = np.nan
                        points[frame_num][index][1] = np.nan
                        points[frame_num][index][2] = np.nan
            
            else:
                break
            
        cap.release()
        
        orderofbpincsv = bodyparts
        n_frames, n_joints, c = points.shape # c = 3, stands for x,y,likelihood

        data = points.reshape(n_frames, n_joints * c) # data reshaped so that rows = frames, cols = joints*c

        frameindex = list([i for i in range(n_frames)]) # nr. of frames

        scorer = 'DLC_Model_Name'
        index = pd.MultiIndex.from_product([[scorer], orderofbpincsv, ['x', 'y', 'likelihood']],names=['scorer', 'bodyparts', 'coords'])
        frame = pd.DataFrame(np.array(data,dtype=float), columns = index, index = frameindex)
        
        save_directory = os.path.dirname(output_dir)
        save_file_name = os.path.splitext(os.path.basename(path))[0]
        pose2D_folder = os.path.join(save_directory, 'pose-2d')
        if not os.path.exists(pose2D_folder):
            os.makedirs(pose2D_folder)
        save_path = os.path.join(pose2D_folder, save_file_name)

        frame.to_hdf(save_path+".h5", key = "whatever", mode='w')
        frame.to_csv(save_path+".csv")
        
        with open(save_path+".pickle", "wb") as file:
            pickle.dump(frame, file, protocol = 4)

def run_mediapipe2D(videos_root_path, output_dir, selected_bodypart):
    
    bodyparts = []

    if 'Full Body' in selected_bodypart:
        mp_model = mp.solutions.holistic
        for lm in mp_model.PoseLandmark:
            bodyparts.append(lm.name)
    else:
        mp_model = mp.solutions.hands
        for lm in mp_model.HandLandmark:
            bodyparts.append(lm.name)
            
    cap = cv.VideoCapture(videos_root_path)

    if (cap.isOpened() == False):
        print("Error opening file")
    else:
        print(videos_root_path)
        n_frames = int(cap.get(cv.CAP_PROP_FRAME_COUNT))
        if (n_frames>0):
            points = np.empty((n_frames, len(bodyparts), 3))
            if 'Full Body' in selected_bodypart:
                mark_holistic_video(mp_model, bodyparts, videos_root_path, cap, points, output_dir) 
            else:
                annotate_2D(mp_model, bodyparts, videos_root_path, cap, points, selected_bodypart, output_dir) 
                

if __name__ == "__main__":
    video_dir = str(sys.argv[1])
    output_dir = str(sys.argv[2])
    bodypart_selection = str(sys.argv[3])
    run_mediapipe2D(video_dir, output_dir, bodypart_selection)
