import numpy
import pandas as pd
import matplotlib.pyplot as plt

def scenes_analysis():
    dfLength = pd.read_csv("scenes_length.csv")
    dfNum = pd.read_csv("scenes_number.csv")
    dfVid = pd.read_csv("songs_on_server.csv", sep=";")
    duration = list(dfLength["duration"])
    frames = list(dfLength["frames"])
    numScenes = list(dfNum["number"])
    vidLength = list(dfVid["length"])

    fig = plt.figure()

    plt.subplot(131)
    plt.boxplot(numScenes,0,'')
    plt.title('Number of scenes per video')

    plt.subplot(132)
    plt.boxplot(duration, 0, '')
    plt.title('Duration of scene (s)')

    plt.subplot(133)
    plt.boxplot(frames,0,'')
    B=plt.title('Number of frames per scene')
    plt.show()

    plt.subplot()
    plt.boxplot(vidLength,0,'')
    plt.title('Length of video')
    plt.show()

    plt.close(fig)

if __name__ == "__main__":
    scenes_analysis()
