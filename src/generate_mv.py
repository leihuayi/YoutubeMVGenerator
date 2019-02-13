import random, os, json, time
import subprocess
import msaf
import warnings
import pandas as pd
from .music_recognition import get_music_infos, convert_genre_to_style
from .feature_color import compute_kmeans, CLUSTERS, list_scenes

BOUNDARY_OFFSET = 0.50 # Delay in boundary delection
AUTHORIZED_GENRES = ['alternative','metal','rock','pop','hip-hop','R&B','dance','techno','house','indie','electro']

'''
Arguments : 
df = dataframe (result of videos clustering)
boundaries = list of timestamps in seconds

assemble some videos using the result of df around the boundaries
'''
def assemble_videos(df, boundaries):
    boundaries = boundaries[1:-1]
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
        while videoLength < boundaries[-1]-BOUNDARY_OFFSET:

            # When reaching next boundary
            while numBound < len(boundaries) and videoLength < boundaries[numBound]-BOUNDARY_OFFSET:

                if indexes[numClus] < len(clus[numClus]) :
                    filename = os.path.splitext(clus[numClus].iloc[indexes[numClus]]['file'])[0]
                    fileLength = clus[numClus].iloc[indexes[numClus]]['length']
                    if not os.path.exists(filename+'.MTS'):
                        # If going over boundary, cut scene
                        if videoLength + fileLength < boundaries[numBound]-BOUNDARY_OFFSET :
                            subprocess.call(['ffmpeg', '-loglevel', 'error', '-i', filename+'.mp4', '-q', '0', filename+'.MTS'])
                        else :
                            fileLength = boundaries[numBound]-BOUNDARY_OFFSET-videoLength
                            subprocess.call(['ffmpeg', '-loglevel', 'error', '-t', str(fileLength), '-i', filename+'.mp4', '-q', '0', filename+'.MTS'])
                    vidList.write("file '"+filename+".MTS'\n")
                    videoLength += fileLength
                    indexes[numClus]+=1
                else:
                    numClus = (numClus+1)%5

            # next boundary
            numClus = (numClus+1)%5
            numBound += 1


'''
Main steps for building the mv
args : input, output, video genre (optionnal)
callback : function that gives feedback to user
'''
def main(args, callback=lambda str: print(str)):
    start = time.time()

    if not os.path.exists(args.input):
        raise FileNotFoundError
    elif not os.path.isdir(args.data) and not args.data[-4:] == '.csv':
        raise Exception('The data path must either be a .csv file or a folder')

    # 1. Get major changes in music
    callback('Identifying key changes in %s...'%args.input)

    warnings.filterwarnings('ignore')
    boundaries, labels = msaf.process(args.input, boundaries_id='olda')

    if boundaries[-1] < 60:
        print('Music shorter than 60 seconds, please chose a longer music for getting a quality MV.')
        return -1
        
    callback('Key changes at (%s) seconds\n'%' , '.join(map('{:.2f}'.format, boundaries)))

    if args.data[-4:] == '.csv':
        # 2. Find music genre and style (music video style = larger category of genre)
        musicGenre = args.genre
        musicStyle = ''
        if musicGenre == '': # No genre given, must find it

            title, artist, musicGenre, musicStyle = get_music_infos(args.input)

            if musicStyle == '':
                print('The algorithm did not manage the recognize the music genre.\n'
                                    'Please try with another music, or manually add genre with the argument --genre <name of genre> \n'
                                    'with genre in ('+','.join(AUTHORIZED_GENRES)+').')
                return -1
        else:
            musicStyle = convert_genre_to_style(musicGenre)
            if musicStyle == '':
                print('This genre is not authorized. Please input one of the following ('+\
                ','.join(AUTHORIZED_GENRES)+') or let the algorithm find the genre.')
                return -1


        # 3. With the music genre, find appropriate videos in database
        callback('Music genre identified : %s. Fetching matching videos in database...\n'%musicGenre)
        
        # use k-means clustering result on scenes extracted from Music Videos with same genre
        clusterResult = pd.read_csv('../statistics/kmeans_'+musicStyle+'.csv')

    else:
        # use k-means clustering result on scenes extracted from Music Videos with same genre
        listFiles = list_scenes(args.data,'json')
        clusterResult = compute_kmeans(listFiles)

    # 4. Join music scenes while respecting the clustering and the input music rythm
    callback('Building the music video around these boundaries...\n')

    # Select and order videos for music clip
    assemble_videos(clusterResult, boundaries)

    # Concatenate videos
    subprocess.call('ffmpeg -loglevel error -f concat -safe 0 -i video_structure.txt -c copy -an temp_video.MTS'.split(' '))

    # Put input music on top of resulting video
    extension = os.path.splitext(args.output)[1]
    if extension != '.avi' and extension != '.mkv':
        args.output = os.path.splitext(args.output)[0]+'.mp4'
        if extension != '.mp4' :
            print('No format within (avi,mkv,mp4) given. Using default mp4 ...')

    # fade out
    '''
    fade = ('','')
    if boundaries[-2]-boundaries[-3]<10:
        fade = (str(boundaries[-3]*25),str(boundaries[-2]-boundaries[-3]))
    else:
        fade = (str((boundaries[-2]-1)*25),'25')

    subprocess.call([('ffmpeg -loglevel error -i temp_video.MTS -vf fade=out:%s:%s temp_video.MTS'%(fade[0],fade[1])).split(' ')])'''

    # copies video stream and replace audio of arg 0 by arg 1
    subprocess.call(['ffmpeg', '-loglevel', 'error', '-i', 'temp_video.MTS', '-i' ,args.input, 
    '-c:v' ,'copy', '-map', '0:v:0', '-map', '1:a:0',  args.output])




    callback('--- Finished building the music video in %f seconds. ---'%(time.time()-start))

    # Delete temp files
    os.remove('temp_video.MTS')
    with open('video_structure.txt','r') as vidList: # delete MTS videos
        for vidFile in vidList:
            os.remove(vidFile[6:-2])
    os.remove('video_structure.txt')

