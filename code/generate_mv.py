import os, sys, json, glob
import argparse
import msaf, librosa
from music_recognition import recognizeMusic, getMusicGenre, authorizedGenres

def main(args):
    print('Loading music : %s ...'%args.input)

    # Check music length
    audioSeries, samplingRate = librosa.load(args.input)
    musicLength = librosa.get_duration(y=audioSeries, sr=samplingRate)
    if musicLength<30 :
        print("The music must be longer than 30 seconds in order to make a quality music video.\n")
        return -1
    else:
        print("Length : %f s\n"%musicLength)

    # Find music genre
    musicGenre = args.genre
    if musicGenre == '': # No genre given, must find it

        with open('acr_config.json', 'r') as f:
            config = json.load(f) # Load host, key, secret from json file

        # Recognize the input music
        musicInput = recognizeMusic(args.input, config)

        if musicInput == -1: # Did not recognize the music
            print("The algorithm did not manage the recognize the music genre.\n"
            "Please try with another music, or manually add genre with the argument --genre <name of genre>.")
            return -1

        else:
            if musicInput[2] == '': # Recognized, but did not find the genre
                # Use APi to find genre knowing music title and artist
                tags = getMusicGenre(musicInput[0],musicInput[1], config)
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


    # Get major changes in music
    print("Identifying music key changes...")
    sonified_file = args.input+"_boundaries.wav"
    sr = 44100
    boundaries, labels = msaf.process(args.input, boundaries_id="olda", sonify_bounds=True, out_bounds=sonified_file, out_sr=sr)

    print("Key changes at (%s) seconds\n"%" , ".join(map("{:.2f}".format, boundaries)))

    # Join music scenes while respecting the clustering and the input music rythm
    print("Building the music video around these boundaries...\n")

    # TODO : append with ffmpeg


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', nargs='?', required=True)
    parser.add_argument('--genre', default='')

    args = parser.parse_args()
    main(args)