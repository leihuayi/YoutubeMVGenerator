import os, sys, json, glob
from acrcloud.recognizer import ACRCloudRecognizer
import argparse
import requests

authorizedGenres = ["rock","pop","hip-hop","rnb","dance"]

"""
Recognize music fingerprint using ACR API
"""
def recognize_music(filePath,config):
    config["timeout"] = 10 # seconds

    re = ACRCloudRecognizer(config)

    #recognize by file path, and skip 20 seconds from from the beginning of sys.argv[1].
    result = json.loads(re.recognize_by_file(filePath, 20, 30))

    if 'metadata' in result.keys():
        result = result['metadata']['music'][0]

        if 'genres' in result.keys():
            # TODO : check if genres in required list
            return (result['title'],result['artists'][0]['name'],",".join([g['name'] for g in result['genres']]))
        else:
            return (result['title'],result['artists'][0]['name'],"")
    else:
        return -1


"""
Get music genre using Last.fm API
"""
def getMusicGenre(title,artist,config):
    params = (
        ('method', 'track.getTopTags'),
        ('api_key', config['api_key']),
        ('artist', artist),
        ('track', title),
        ('format', 'json'),
    )

    tags = []
    # First try to get track genre, else get artist genre
    reqs = ['track','artist']

    while len(tags) == 0 and len(reqs) > 0:
        response = requests.get('http://ws.audioscrobbler.com/2.0/', params=params).json()
        reqs.pop(0)

        if ('error' not in response.keys() and 'toptags' in response.keys() and
        'tag' in response['toptags'] and len(response['toptags']['tag'])) > 0:

            tagList = response['toptags']['tag']
            # get top 3 tags
            i=0
            while i < min(len(tagList),3):
                tags.append(tagList[i]['name'])
                i+=1

            # TODO : check if tags are in required list
        else:
            params= (
                ('method', 'artist.getTopTags'),
                ('api_key', config['api_key']),
                ('artist', artist),
                ('format', 'json'),
            )

    return tags


def main(args):
    print('Input music : %s\n'%args.input)
    musicGenre = args.genre

    if musicGenre == '': # No genre given, must find it

        with open('acr_config.json', 'r') as f:
            config = json.load(f) # Load host, key, secret from json file

        # Recognize the input music
        musicInput = recognize_music(args.input, config)

        if musicInput == -1: # Did not recognize the music
            print("The algorithm did not manage the recognize the music genre.\n"
            "Please try with another music, or manually add genre with the argument --genre <name of genre>.")
            return -1

        else:
            if musicInput[2] == '': # Recognized, but did not find the genre

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
    print("Music genre identified : %s. Fetching matching videos in database..."%musicGenre)
    
    # TODO : call k-means clustering on scenes extracted from Music Videos with same genre

    # Get major changes in music
    print("Identifying music key changes")

    # TODO

    # Join music scenes while respecting the clustering and the input music rythm
    print("Building the music video...")

    # TODO : append with ffmpeg


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', nargs='?', required=True)
    parser.add_argument('--genre', default='')

    args = parser.parse_args()
    main(args)