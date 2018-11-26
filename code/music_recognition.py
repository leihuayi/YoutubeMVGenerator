import os, sys, json, glob
from acrcloud.recognizer import ACRCloudRecognizer
from acrcloud.recognizer import ACRCloudRecognizeType
import pandas as pd

if __name__ == '__main__':
    '''This module can recognize ACRCloud by most of audio/video file. 
        Audio: mp3, wav, m4a, flac, aac, amr, ape, ogg ...
        Video: mp4, mkv, wmv, flv, ts, avi ...'''

    with open('acr_config.json', 'r') as f:
        config = json.load(f) # Load host, key, secret from json file
        config["timeout"] = 10 # seconds

    re = ACRCloudRecognizer(config)
    musics = []

    for f in glob.glob(sys.argv[1]+"*.mp3") :
        #recognize by file path, and skip 0 seconds from from the beginning of sys.argv[1].
        result = json.loads(re.recognize_by_file(f, 20, 30))
        if 'metadata' in result.keys():
            result = result['metadata']['music'][0]
            
            # print(json.dumps(result))
            if 'genres' in result.keys():
                musics.append((os.path.splitext(os.path.basename(f))[0],result['title'],result['artists'][0]['name'],",".join([g['name'] for g in result['genres']])))
            else:
                musics.append((os.path.splitext(os.path.basename(f))[0],result['title'],result['artists'][0]['name'],""))
        else:
            musics.append((os.path.splitext(os.path.basename(f))[0],"","",""))
        
    df = pd.DataFrame(musics)
    df.columns = ['id','name','artist','genres']
    df.to_csv("../statistics/songs_on_server.csv",sep=";")
