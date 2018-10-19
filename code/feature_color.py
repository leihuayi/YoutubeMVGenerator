import cv2
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import time
import os
from scipy.stats import itemfreq
from sklearn.cluster import KMeans

CLUSTERS = 20
imgClusters = []

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
                        imgBase = cv2.resize(image, (0,0), fx=0.2, fy=0.2)
                    
                    else:
                        img = cv2.resize(image, (0,0), fx=0.2, fy=0.2)
                        imgBase = np.concatenate((imgBase, img), axis=1)

                count += 1 # Keeps track of number of frames

                if count==numFrames//2:
                    imgClusters.append(image)
            
            # imgBase = cv2.cvtColor(imgBase, cv2.COLOR_BGR2RGB)
            hist = extract_feature(imgBase)
            return hist
                
def extract_feature(img):
    color = ('b','g','r')
    hist = np.empty((0,256))
    # fig = plt.figure()
    for i,col in enumerate(color):
        histcolor = cv2.calcHist([img],[i],None,[256],[0,256])
        hist = np.append(hist, histcolor/np.linalg.norm(histcolor))
        # plt.plot(histcolor,color = col)
        # plt.xlim([0,256])
    # plt.show()
    # plt.close(fig)
    return hist

def display_clusters(df):
    clusNum = -1
    # We stack all images on imgBase.
    imgBase = np.empty((150,150,3), np.uint8)
    fig = plt.figure()
    columns = 2
    rows = CLUSTERS/2

    for index, row in df.iterrows():
        # new cluster
        if row['cluster'] != clusNum:
            if clusNum >= 0:
                # draw previous cluster
                plt.imshow(cv2.cvtColor(imgBase, cv2.COLOR_BGR2RGB))

            # start new cluster
            plt.subplot(rows, columns, row['cluster']+1)
            plt.axis("off")
            clusNum = row['cluster']
            imgBase = imgClusters[index]
        # aggregate image in cluster
        else:
            imgBase = np.concatenate((imgBase, imgClusters[index]), axis=1)

    plt.imshow(cv2.cvtColor(imgBase, cv2.COLOR_BGR2RGB))
    figManager = plt.get_current_fig_manager()
    figManager.window.showMaximized()
    plt.show()
    fig.close()

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

    # Display the clutering results
    df = pd.DataFrame.from_records(zip(listFiles,kmeans.labels_), columns=['file','cluster'])
    df = df.sort_values(by=['cluster','file'])
    # df.to_csv("../statistics/clusters-%s.csv"%vidName)
    display_clusters(df)

if __name__ == "__main__":
    main()

