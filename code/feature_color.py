import cv2
import numpy as np
import matplotlib.pyplot as plt
import time
import os
from scipy.stats import itemfreq
from sklearn.cluster import KMeans

CLUSTERS = 5

def centroid_histogram(clt):
	# grab the number of different clusters and create a histogram
	# based on the number of pixels assigned to each cluster
	numLabels = np.arange(0, len(np.unique(clt.labels_)) + 1)
	(hist, _) = np.histogram(clt.labels_, bins = numLabels)
 
	# normalize the histogram, such that it sums to one
	hist = hist.astype("float")
	hist /= hist.sum()
 
	# return the histogram
	return hist

def plot_colors(stats, hist):
    # initialize the bar chart representing the relative frequency
    # of each of the colors
    bar = np.zeros((50, 300, 3), dtype = "uint8")
    startX = 0

    # loop over the percentage of each cluster and the color of
    # each cluster
    for (percent, color) in zip(stats, hist):
        # plot the relative percentage of each cluster
        endX = startX + (percent * 300)
        color = color.astype("uint8").tolist()
        #color = [col[2],col[1],col[0]]
        cv2.rectangle(bar, (int(startX), 0), (int(endX), 50), color, -1)
        startX = endX

    # return the bar chart
    return bar

# Function to average the dominant color analysis on several frames
def extract_frames(path): 

    samplings = [5, 10, 15, 20]
    extract = 10

    # Path to video file
    if os.path.exists("/home/manu/Documents/Thesis/Tests/"+path):

        vidObj = cv2.VideoCapture("/home/manu/Documents/Thesis/Tests/"+path) 
        numFrames = int(vidObj.get(cv2.CAP_PROP_FRAME_COUNT))

        if numFrames<12:
            print("Scene too short. No analyzing")

        else:
            print("Analyzing video %s : %d frames ..."%(path,numFrames))

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
                if count%extract==deviate and count<numFrames:
                    numImg = (count-deviate)//extract
                    print("New image: %d"%numImg)

                    if numImg==0:
                        imgBase = cv2.resize(image, (0,0), fx=0.1, fy=0.1)
                    
                    else:
                        img = cv2.resize(image, (0,0), fx=0.1, fy=0.1)
                        imgBase = np.concatenate((imgBase, img), axis=1)

                count += 1 # Keeps track of number of frames
            
            imgBase = cv2.cvtColor(imgBase, cv2.COLOR_BGR2RGB)
            bar = extract_feature(imgBase)

            # Draws the result
            fig = plt.figure()
            plt.subplot(211)
            plt.imshow(imgBase)
            plt.axis("off")
            plt.subplot(212)
            plt.imshow(bar)
            plt.axis("off")
            plt.show()
            plt.close(fig)

def extract_feature(img):
    # reshape the image to be a list of pixels
    img = img.reshape((img.shape[0] * img.shape[1], 3))

    # cluster the pixel intensities
    clt = KMeans(n_clusters = CLUSTERS)
    clt.fit(img)

    # build a histogram of clusters and then create a figure
    # representing the number of pixels labeled to each color
    hist = centroid_histogram(clt)
    
    # show our color bar
    return plot_colors(hist, clt.cluster_centers_)

def main():
    vidName = "9bZkp7q19f0"
    scenes = ["003", "007", "008", "018", "021", "022", "051 ","079"]

    for s in scenes :
        extract_frames(vidName+"/"+vidName+"-"+ s +".mp4")

if __name__ == "__main__":
    main()

