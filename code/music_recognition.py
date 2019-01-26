from acrcloud.recognizer import ACRCloudRecognizer
import os, sys, glob
import pandas as pd
import requests, json

'''
Recognize music fingerprint using ACR API
'''
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


'''
Get music genre using Last.fm API
'''
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


'''
Use above functions to classify a music
The music should be greater than 60 sec
'''
def get_music_infos(f):

    print("Recognizing genre for : "+f)

    with open('apis_config.json', 'r') as conf:
        config = json.load(conf) # Load host, key, secret from json file

    # Recognize the input music 
    musicInput = ('','','')
    musicGenre = ''
    start = 20

    while musicInput[1] == '' and start < 60: # Did not recognize the music
        musicInput = recognize_music(f, config, start)
        start += 10

    if musicInput[1] != '': # Artist recognized

        if musicInput[2] == '': # Did not find the genre
            # Use APi to find genre knowing music title and artist
            tags = get_music_genre(musicInput[0],musicInput[1], config)
            if len(tags) != 0:
                musicGenre = ','.join(tags)
        else:
            musicGenre = musicInput[2]

    musicStyle = convert_genre_to_style(musicGenre)
    return((musicInput[0],musicInput[1],musicGenre,musicStyle))


'''
Remove silent MVs (mp3 could not be extracted)
'''
def del_silent():
    listVid = glob.glob(sys.argv[1]+"*.mp4")
    listSong = glob.glob(sys.argv[1]+"*.mp3")
    for v in listVid:
        if v[:-1]+"3" not in listSong:
            print(v)
            os.remove(v)


'''
Classify genre given by recognize_database_genre into one of 4 styles : 
rock / hiphop / electro / pop
'''
def convert_genre_to_style(genre):
    genre = genre.lower()
    if "alternative" in genre or "rock" in genre or "metal" in genre:
        return "rock"
    elif "hip hop" in genre or "hip-hop" in genre or "rnb" in genre or "r&b" in genre or "rap" in genre:
        return "hiphop"
    elif "electro" in genre or "dance" in genre or "techno" in genre or "house" in genre:
        return "electro"
    elif "pop" in genre or "indie" in genre:
        return "pop"
    else:
        return ""


if __name__ == "__main__":
    print(get_music_infos(sys.argv[1]))

        

    