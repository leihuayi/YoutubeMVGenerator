import numpy
import pandas as pd
import matplotlib.pyplot as plt

def scenes_analysis():
    dfLength = pd.read_csv("scenes_length.csv")
    dfNum = pd.read_csv("scenes_number.csv")
    dfVid = pd.read_csv("videos_length.csv")
    duration = list(dfLength["duration"])
    frames = list(dfLength["frames"])
    numScenes = list(dfNum["number"])
    video = list(dfVid["duration"])

    plt.subplot(131)
    plt.boxplot(numScenes)
    plt.title('Number of scenes per video')

    plt.subplot(132)
    plt.boxplot(duration)
    plt.title('Duration of scene (s)')

    plt.subplot(133)
    plt.boxplot(frames)
    plt.title('Number of frames per scene')
    plt.show()

    plt.subplot()
    plt.boxplot(video)
    plt.title('Length of video')
    plt.show()

if __name__ == "__main__":
    scenes_analysis()
