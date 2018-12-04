from acrcloud.recognizer import ACRCloudRecognizer
import os, sys, glob
import pandas as pd
import requests, json

authorizedGenres = ["rock","pop","hip-hop","rnb","dance"]

"""
Recognize music fingerprint using ACR API
"""
def recognize_music(filePath,config, start):
    config["timeout"] = 10 # seconds

    re = ACRCloudRecognizer(config)

    # recognize by file path, and skip 'start' seconds from from the beginning of sys.argv[1].
    result = json.loads(re.recognize_by_file(filePath, start, start+10))

    if 'metadata' in result.keys():
        result = result['metadata']['music'][0]

        if 'genres' in result.keys():
            # TODO : check if genres in required list
            return (result['title'],result['artists'][0]['name'],','.join([g['name'] for g in result['genres']]))
        else:
            return (result['title'],result['artists'][0]['name'],'')
    else:
        return ('','','')


"""
Get music genre using Last.fm API
"""
def get_music_genre(title,artist,config):
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


def recognize_database_genres():
    listMusics = []

    for f in glob.glob(sys.argv[1]+"*.mp3"):
        print("Recognizing genre for : "+f)

        with open('acr_config.json', 'r') as conf:
            config = json.load(conf) # Load host, key, secret from json file

        # Recognize the input music. The shortest music in database lasts 70 sec
        musicInput = ('','','')
        musicGenre = ''
        start = 20

        while musicInput[1] == '' and start < 70: # Did not recognize the music
            musicInput = recognize_music(f, config, start)
            start += 10

        if musicInput[1] != '': # Artist recognized

            if musicInput[2] == '': # Did not find the genre
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

        listMusics.append((os.path.splitext(os.path.basename(f))[0],musicInput[0],musicInput[1],musicGenre))

    df = pd.DataFrame(listMusics, columns=['id','name','artist','genres'])
    df.to_csv("../statistics/songs_on_server_test.csv", sep=";")


if __name__ == "__main__":
    recognize_database_genres()

        

    