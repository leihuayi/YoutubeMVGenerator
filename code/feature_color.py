import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import itemfreq
from sklearn.cluster import KMeans


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

def plot_colors(hist, centroids):
	# initialize the bar chart representing the relative frequency
	# of each of the colors
	bar = np.zeros((50, 300, 3), dtype = "uint8")
	startX = 0
 
	# loop over the percentage of each cluster and the color of
	# each cluster
	for (percent, color) in zip(hist, centroids):
		# plot the relative percentage of each cluster
		endX = startX + (percent * 300)
		cv2.rectangle(bar, (int(startX), 0), (int(endX), 50),
			color.astype("uint8").tolist(), -1)
		startX = endX
	
	# return the bar chart
	return bar

# Function to extract frames 
def extract_frame(path): 
    # Path to video file 
    vidObj = cv2.VideoCapture(path) 

    # Used as counter variable 
    count = 5
    numFrames = int(vidObj.get(cv2.CAP_PROP_FRAME_COUNT))
    print(numFrames)
    extract = (numFrames-10)//5

    # checks whether frames were extracted 
    success = 1
  
    while success: 
        success, image = vidObj.read() 
        if count%extract==0:
            extract_feature(image)
  
        count += 1

def extract_feature(image):
    # load the image and convert it from BGR to RGB
    img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    plt.figure()
    plt.axis("off")
    plt.imshow(img)

    # reshape the image to be a list of pixels
    img = img.reshape((img.shape[0] * img.shape[1], 3))

    # cluster the pixel intensities
    clt = KMeans(n_clusters = 5)
    clt.fit(img)

    # build a histogram of clusters and then create a figure
    # representing the number of pixels labeled to each color
    hist = centroid_histogram(clt)
    
    # show our color bar
    bar = plot_colors(hist, clt.cluster_centers_)
    plt.figure()
    plt.axis("off")
    plt.imshow(bar)
    plt.show()


def main():
    extract_frame("/home/manu/Documents/Thesis/Tests/aJOTlE1K90k/aJOTlE1K90k-002.mp4")

if __name__ == "__main__":
    main()
