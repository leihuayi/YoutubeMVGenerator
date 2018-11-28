from acrcloud.recognizer import ACRCloudRecognizer
import requests, json

authorizedGenres = ["rock","pop","hip-hop","rnb","dance"]

"""
Recognize music fingerprint using ACR API
"""
def recognizeMusic(filePath,config):
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