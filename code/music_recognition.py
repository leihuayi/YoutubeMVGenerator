from acrcloud.recognizer import ACRCloudRecognizer
import os, sys, glob
import pandas as pd
import requests, json

authorizedGenres = ["rock","pop","hiphop","electro"]

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
Use above functions to classify all musics from MVs in database
'''
def recognize_database_genres():
    listMusics = []

    for f in glob.glob(sys.argv[1]+"*.mp3"):
    # for f in open("../toanalyze.txt").readlines():
        f = sys.argv[1]+f
        if f[-1] == "\n":
            f = f[:-1]
        print("Recognizing genre for : "+f)

        if os.path.exists(f) and os.path.splitext(f)[1] == ".mp3":
            with open('apis_config.json', 'r') as conf:
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
                    if len(tags) != 0:
                        musicGenre = ','.join(tags)
                else:
                    musicGenre = musicInput[2]

            listMusics.append((os.path.splitext(os.path.basename(f))[0],musicInput[0],musicInput[1],musicGenre))
        else:
            print("mp3 does not exist")

    df = pd.DataFrame(listMusics, columns=['id','name','artist','genres'])
    df.to_csv("../statistics/songs_on_server.csv", sep=";", index=False)


'''
Remove silent MVs (mp3 could not be extracted)
'''
def del_not_song():
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


'''
Classify database genres
'''
def convert_db_genres():
    filePath = "../statistics/songs_on_server.csv"
    df = pd.read_csv(filePath, sep=";")
    df['genres'] = df['genres'].fillna('')
    df['style'] = ''
    for index, row in df.iterrows():
        row['style'] = convert_genre_to_style(row['genres'])
    df.to_csv(filePath, sep=";", index=False)


if __name__ == "__main__":
    convert_db_genres()

        

    