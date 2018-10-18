import cv2
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import time
import os
from scipy.stats import itemfreq
from sklearn.cluster import KMeans

CLUSTERS = 5


# Function to average the dominant color analysis on several frames
def extract_frames(path): 

    sampling = 15
    # Path to video file
    if os.path.exists(path):

        vidObj = cv2.VideoCapture(path) 
        numFrames = int(vidObj.get(cv2.CAP_PROP_FRAME_COUNT))

        if numFrames<12:
            print("Scene too short. No analyzing")

        else:
            # print("Analyzing video %s : %d frames ..."%(os.path.basename(path),numFrames))

            # Used as counter variable 
            count = 0 
            deviate = 3 # Not start at 0 because of transition frames

            # checks whether frames were extracted 
            success = 1

            # We stack all images on imgBase.
            imgBase = np.zeros((150,150,3), np.uint8)

            while success: 
                success, image = vidObj.read() 

                # When we encounter a frame we want to analyse : stack image
                if count%sampling==deviate and count<numFrames:
                    numImg = (count-deviate)//sampling
                    # print("New image: %d"%numImg)

                    if numImg==0:
                        imgBase = cv2.resize(image, (0,0), fx=0.5, fy=0.5)
                    
                    else:
                        img = cv2.resize(image, (0,0), fx=0.5, fy=0.5)
                        imgBase = np.concatenate((imgBase, img), axis=1)

                count += 1 # Keeps track of number of frames
            
            # imgBase = cv2.cvtColor(imgBase, cv2.COLOR_BGR2RGB)
            hist = extract_feature(imgBase)
            return hist
                
def extract_feature(img):
    color = ('b','g','r')
    hist = np.empty((0,256))
    # fig = plt.figure()
    for i,col in enumerate(color):
        histcolor = cv2.calcHist([img],[i],None,[256],[0,256])
        hist = np.append(hist, histcolor)
        # plt.plot(histcolor,color = col)
        # plt.xlim([0,256])
    # plt.show()
    # plt.close(fig)
    return hist/np.linalg.norm(hist)

def main():
    start = time.time()
    vidName = "9bZkp7q19f0"
    
    listFiles = os.listdir("/home/manu/Documents/Thesis/Tests/"+vidName)
    arrHist = []

    for i,f in enumerate(listFiles):
        hist = extract_frames("/home/manu/Documents/Thesis/Tests/%s/%s"%(vidName,f))
        arrHist.append(hist)

    arrHist = np.array(arrHist)

    # Compute Kmeans on histograms to group videos
    kmeans = KMeans(n_clusters=CLUSTERS, random_state=0).fit(arrHist)

    print("Finished KMeans. Time elapsed : %f"%(time.time()-start))

    df = pd.DataFrame.from_records(zip(listFiles,kmeans.labels_), columns=['file','cluster'])
    df.to_csv("../statistics/clusters-%s.csv"%vidName)

if __name__ == "__main__":
    main()

