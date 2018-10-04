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

def plot_colors(stats, clusters):
    # initialize the bar chart representing the relative frequency
    # of each of the colors
    bar = np.zeros((50, 300, 3), dtype = "uint8")
    startX = 0

    # loop over the percentage of each cluster and the color of
    # each cluster
    zipped = zip(stats, [c.astype("uint8").tolist() for c in clusters])
    zipped = sorted(zipped, key=lambda x:x[1])

    for (percent, color) in zipped:
        # plot the relative percentage of each cluster
        endX = startX + (percent * 300)
        #color = [col[2],col[1],col[0]]
        cv2.rectangle(bar, (int(startX), 0), (int(endX), 50), color, -1)
        startX = endX

    # return the bar chart
    return bar

# Function to average the dominant color analysis on several frames
def extract_frames(path): 

    samplings = [5, 10, 15, 20, 25, 30, 35, 40]
    fig = plt.figure()

    for i in range(8):
        sampling = samplings[i]

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
                    if count%sampling==deviate and count<numFrames:
                        numImg = (count-deviate)//sampling
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
                plt.subplot(8,2,i*2+1)
                plt.imshow(imgBase)
                plt.axis("off")
                plt.title(sampling,rotation='vertical',x=-0.1,y=0.5)
                plt.subplot(8,2,(i+1)*2)
                plt.imshow(bar)
                plt.axis("off")
                
                
    plt.savefig("/home/manu/Documents/Thesis/statistics/%s-%d.png"%(path, numFrames))
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
    scenes = ["008", "018", "021", "031", "032", "041", "044","049", "077", "082", "117"]

    for s in scenes :
        extract_frames("%s/%s-%s.mp4"%(vidName,vidName,s))

if __name__ == "__main__":
    main()

