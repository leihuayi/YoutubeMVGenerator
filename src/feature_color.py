import cv2
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import time
import os, glob, sys
import json
from scipy.stats import itemfreq
from sklearn.cluster import KMeans

CLUSTERS = 70
thumbnailsPath = "../statistics/imgClusters/"

'''
EXTRACT_FEATURE : for one video file, compute the mean color histogram
path (string) : path of video file
saveThumbnail (bool) : save or not an image representing the video (useful for representing kmeans result)
'''
def extract_feature(path, saveThumbnail): 

    # We will use image every sampling frame to compute the mean histogram
    sampling = 5

    # Path to video file
    if os.path.exists(path):
        vidObj = cv2.VideoCapture(path) 
        numFrames = int(vidObj.get(cv2.CAP_PROP_FRAME_COUNT))
        numSec = numFrames/vidObj.get(cv2.CAP_PROP_FPS)

        # Do not use scenes too short
        if numFrames<12:
            print("Scene too short (<25 frames, ~500ms). No analyzing")
            return (numSec, np.empty((0,0)))

        # Do not use scenes too long
        elif numFrames>125:
            print("Scene too long (>125 frames, ~5 sec). No analyzing")
            return (numSec, np.empty((0,0)))

        else:
            print("Analyzing video %s : %d frames, %f seconds ..."%(os.path.basename(path),numFrames,numSec))

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

                if saveThumbnail and count==numFrames//2 :
                    cv2.imwrite(thumbnailsPath+os.path.basename(path)+".jpg",image)
            
            # imgBase = cv2.cvtColor(imgBase, cv2.COLOR_BGR2RGB)
            hist = compute_histogram(imgBase)

            if hist[0] == 1 and hist[256] == 1 and hist[512] == 1:
                return (numSec, np.empty((0,0)))
            else:
                return (numSec, hist)


'''
Return an numpy array size 256 x 3 which is the color histogram of the picture :
[0,255] = blue
[256,511] = green
[512,767] = red
for each channel [0,255], index i gives the percentage of pixels with intensity i in the pic
'''
def compute_histogram(img):
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


'''
Helper function
'''
def list_scenes(folder, extension):
    listFiles = []

    for f in glob.glob(folder+"*.mp4"):
        fname = os.path.splitext(f)[0]
        # Find the folders for each video
        if os.path.exists(fname):
            # Add the list of scenes
            listFiles += glob.glob(fname+"/*."+extension)

    return listFiles


'''
Stores information for all scenes in a folder into json files
informations : scene length, color (feature)
'''
def store_color_features(folder):
    listFiles = list_scenes(folder, "mp4")

    for f in listFiles:
        # extract_feature(video file, save thumbnail for not)
        sceneLength, hist = extract_feature(f, False)

        if hist.size > 0 :
            jsonpath = os.path.splitext(f)[0]+'.json'
            jsondata = {'length':sceneLength,'color':hist.tolist()}
            with open(jsonpath, 'w') as outfile:
                json.dump(jsondata, outfile)


'''
Draws on plots each cluster to easily visualize the clustering results
'''
def display_clusters(df):
    clusNum = -1
    columns = 10
    rows = 0
    totalImgCluster = 0
    indexImgCluster = 0

    for index, row in df.iterrows():
        # new cluster = new plot
        if row['cluster'] != clusNum:

            # Show previous plot
            if clusNum >= 0 :
                if totalImgCluster>10:
                    figManager = plt.get_current_fig_manager()
                    figManager.window.showMaximized()
                    plt.show()
                plt.close(fig)

            # Build new plot
            clusNum = row['cluster']
            fig = plt.figure()
            totalImgCluster = len(df[df['cluster'] == clusNum])
            print("-- Cluster n°%d containing %d videos --"%(clusNum,totalImgCluster))
            indexImgCluster = 0

            # Have 10 columns and adapted number lines
            rows = totalImgCluster//10 if totalImgCluster%10==0 else totalImgCluster//10 + 1

        # draw image
        indexImgCluster += 1
        plt.subplot(rows, columns, indexImgCluster)
        plt.axis("off")
        thumbPath = os.path.splitext(thumbnailsPath+os.path.basename(row['file']))[0]+".mp4.jpg"
        image = cv2.imread(thumbPath)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        plt.imshow(image)

    figManager = plt.get_current_fig_manager()
    figManager.window.showMaximized()
    plt.show()
    plt.close(fig)


'''
Executes Kmeans on a given list of files
'''
def compute_kmeans(listFiles):
    # Read the features from json files
    arrHist = []
    arrLength = []
    for jsonFile in listFiles:
        with open(jsonFile, "r") as jFile:
            jdata = json.load(jFile)
            arrHist.append(jdata['color'])
            arrLength.append(jdata['length'])

    arrHist = np.array(arrHist)

    # Compute Kmeans on histograms to group videos
    kmeans = KMeans(n_clusters=CLUSTERS, init='random', random_state=2, max_iter=800, algorithm="full").fit(arrHist)
    
    # Display the clutering results
    df = pd.DataFrame.from_records(zip(listFiles,arrLength,kmeans.labels_), columns=['file','length','cluster'])
    df = df.sort_values(by=['cluster','file'])
    # df.to_csv("../statistics/clusters-%d.csv"%CLUSTERS)
    # display_clusters(df)
    return df
    

def main():
    start = time.time()

    # Extract the color features and store them
    # store_color_features(sys.argv[1])

    # Kmeans for each style
    df = pd.read_csv("../statistics/songs_on_server.csv", sep=";")

    for resolution in ["16/9","40/17"]:
        for style in ["rock","pop","hiphop","electro"] :
            print("Starting KMeans for style : %s"%style)
            subDf = df.loc[(df["style"] == style) & (df["resolution"] == resolution)]
            listFiles = []
            for index, row in subDf.iterrows():
                # Get all scenes of MVs with same style
                listFiles += glob.glob(sys.argv[1]+row["id"]+"/*.json")

            kmeans = compute_kmeans(listFiles)
            kmeans.to_csv("../statistics/kmeans_"+resolution[:2]+"_"+style+".csv",index=False)

            print("Finished KMeans. Time elapsed : %f---------------\n"%(time.time()-start))
            start = time.time()


if __name__ == "__main__":
    main()


