import os, sys, json, glob
import argparse
import random
import subprocess
import msaf, librosa
import pandas as pd
from music_recognition import recognize_music, get_music_genre, authorizedGenres
from feature_color import compute_kmeans, CLUSTERS, list_scenes

def build_mv(df, boundaries):
    # Get 5 random clusters such as sum lengths more than whole music
    # with approximately same proportion of each

    # List of number of scenes and total length for each cluster
    clusLengths = [(i,len(df[df['cluster'] == i]), df[df['cluster']==i]['length'].sum()) for i in range(CLUSTERS)]

    limit = boundaries[-1]/5-10
    clusLengths = [x for x in clusLengths if x[2]>limit]
    selectedClus = random.sample(clusLengths,5)
    # TODO : add ending condition in case
    while sum([x[2] for x in selectedClus])<boundaries[-1]:
        selectedClus = random.sample(clusLengths,5)

    # Append videos of selected 5 clusters
    videoLength = 0
    numBound = 1
    numClus = 0

    clus = [df[df['cluster'] == selectedClus[i][0]] for i in range(5)]
    indexes = [0]*5

    with open('video_structure.txt','w') as vidList:
        while videoLength < boundaries[-1]:

            while numBound < len(boundaries) and videoLength < (boundaries[numBound]-0.05):

                if indexes[numClus] < len(clus[numClus]) :
                    filename = os.path.splitext(clus[numClus].iloc[indexes[numClus]]['file'])[0]
                    if not os.path.exists(filename+".MTS"):
                        subprocess.call(["ffmpeg", "-loglevel", "panic", "-i", filename+".mp4", "-q", "0", filename+".MTS"])
                    vidList.write("file '"+filename+"'.MTS\n")
                    videoLength += clus[numClus].iloc[indexes[numClus]]['length']
                    indexes[numClus]+=1
                else:
                    numClus = (numClus+1)%5

            # next boundary
            numClus = (numClus+1)%5
            numBound += 1


def main(args):
    print('Loading music : %s ...'%args.input)

    # Check music length
    # audioSeries, samplingRate = librosa.load(args.input)
    # musicLength = librosa.get_duration(y=audioSeries, sr=samplingRate)
    # if musicLength<30 :
    #     print("The music must be longer than 30 seconds in order to make a quality music video.\n")
    #     return -1
    # else:
    #     print("Length : %f s\n"%musicLength)

    # Find music genre
    musicGenre = args.genre
    if musicGenre == '': # No genre given, must find it

        with open('acr_config.json', 'r') as conffile:
            config = json.load(conffile) # Load host, key, secret from json file

        # Recognize the input music
        musicInput = recognize_music(args.input, config, 20)

        if musicInput[1] == '': # Did not recognize the music
            print("The algorithm did not manage the recognize the music genre.\n"
            "Please try with another music, or manually add genre with the argument --genre <name of genre>.")
            return -1

        else:
            if musicInput[2] == '': # Recognized, but did not find the genre
                # Use APi to find genre knowing music title and artist
                tags = get_music_genre(musicInput[0],musicInput[1], config)
                if len(tags) == 0:
                    print("The algorithm did not manage the recognize the music genre.\n"
                    "Please try with another music, or manually add genre with the argument --genre <name of genre>.")
                    return -1
                else:
                    musicGenre = ','.join(tags)
            else:
                musicGenre = musicInput[2]

    else:
        if musicGenre not in authorizedGenres:
            print("This genre is not authorized. Please input one of the following ("+\
            ",".join(authorizedGenres)+") or let the algorithm find the genre.")
            return -1


    # With the music genre, find appropriate videos in database
    print("Music genre identified : %s. Fetching matching videos in database...\n"%musicGenre)
    
    # TODO : call k-means clustering on scenes extracted from Music Videos with same genre
    listFilesSameGenre = list_scenes("/home/manu/Documents/Thesis/Tests", "json")
    clusterResult = compute_kmeans(listFilesSameGenre)

    # Get major changes in music
    print("Identifying music key changes...")
    sonified_file = args.input+"_boundaries.wav"
    sr = 44100
    boundaries, labels = msaf.process(args.input, boundaries_id="olda", sonify_bounds=True, out_bounds=sonified_file, out_sr=sr)

    print("Key changes at (%s) seconds\n"%" , ".join(map("{:.2f}".format, boundaries)))

    # Join music scenes while respecting the clustering and the input music rythm
    print("Building the music video around these boundaries...\n")

    # TODO : append with ffmpeg
    build_mv(clusterResult, boundaries)
    # Concatenate videos
    subprocess.call("ffmpeg -loglevel panic -f concat -safe 0 -i video_structure.txt -c copy temp_video.MTS".split(" "))
    # Put input music on top of resulting video
    subprocess.call(["ffmpeg", "-i", "temp_video.MTS", "-i" ,args.input, "-c:v" ,"copy", "-map", "0:v:0", "-map", "1:a:0", args.output])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', nargs='?', required=True)
    parser.add_argument('--output', nargs='?', required=True)
    parser.add_argument('--genre', default='')

    args = parser.parse_args()
    main(args)