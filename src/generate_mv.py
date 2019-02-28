import random, os, json, time
import subprocess
import msaf
from warnings import filterwarnings
import pandas as pd
import tempfile, shutil
from .music_recognition import get_music_infos, convert_genre_to_style
from .feature_color import compute_kmeans, CLUSTERS, list_scenes

BOUNDARY_OFFSET = 0.50 # Delay in boundary delection
END_OFFSET = 3
NUM_CLUS_IN_VIDEO = 6
AUTHORIZED_GENRES = ['alternative','metal','rock','pop','hip-hop','R&B','dance','techno','house','indie','electro']
RESOLUTION_PROBABILITY = 0.3333 # Probability for resolution format (640x360 or 640x272)

'''
Changes the order in which appear group of videos from one MV in cluster
'''
def shuffle_mvs(df):
    dic = {}
    for index, row in df.iterrows():
        if os.path.dirname(row['file']) not in dic.keys():
            dic[os.path.dirname(row['file'])] = 1
        else:
            dic[os.path.dirname(row['file'])] += 1

    mvList = list(dic.keys())
    random.shuffle(mvList)
    res = []
    for mv in mvList:
        res.append(df[df['file'].str.startswith(mv)])
    return pd.concat(res).reset_index(drop=True)

'''
Arguments : 
df = dataframe (result of videos clustering)
boundaries = list of timestamps in seconds

assemble some videos using the result of df around the boundaries
'''
def assemble_videos(df, boundaries, tempDir):
    # Very often msaf detects 2 times the last boundary. Remove it if necessary
    if boundaries[-1]-boundaries[-2]<3:
        boundaries = boundaries[1:-1]
    else:
        boundaries = boundaries[1:]

    # Get NUM_CLUS_IN_VIDEO random clusters such as sum lengths more than whole music
    # with approximately same proportion of each

    # List of number of scenes and total length for each cluster
    clusLengths = [(i,len(df[df['cluster'] == i]), df[df['cluster']==i]['length'].sum()) for i in range(CLUSTERS)]

    limit = boundaries[-1]/NUM_CLUS_IN_VIDEO-10
    clusLengths = [x for x in clusLengths if x[2]>limit]
    selectedClus = random.sample(clusLengths,NUM_CLUS_IN_VIDEO)
    limit = 0
    while sum([x[2] for x in selectedClus])<boundaries[-1] and limit<1000:
        selectedClus = random.sample(clusLengths,NUM_CLUS_IN_VIDEO)
        limit += 1
    if limit == 1000:
        print("Could not find clusters covering the whole video.")
        return -1

    # Append videos of selected 5 clusters
    videoLength = 0
    numBound = 1
    numClus = 0

    clus = [shuffle_mvs(df[df['cluster'] == selectedClus[i][0]]) for i in range(NUM_CLUS_IN_VIDEO)] # files in each cluster
    indexes = [0]*NUM_CLUS_IN_VIDEO # keeps track if last used file index for each cluster

    with open('video_structure.txt','w') as vidList:
        while videoLength < boundaries[-1]-END_OFFSET:

            # When reaching next boundary
            while numBound < len(boundaries) and videoLength < boundaries[numBound]-BOUNDARY_OFFSET:

                if indexes[numClus] < len(clus[numClus]) :
                    filename = os.path.splitext(clus[numClus].iloc[indexes[numClus]]['file'])[0]
                    fileLength = clus[numClus].iloc[indexes[numClus]]['length']

                    if videoLength+fileLength>boundaries[-1]-END_OFFSET: # stop this algorithm for the last END_OFFSET seconds
                        break

                    
                    if os.path.exists(tempDir+os.path.basename(filename)+'.MTS'):
                        print('!!!! VERY STRANGE - duplicate at cluster %d, index %d, file %s !!!!'%(numClus, indexes[numClus], os.path.basename(filename)))
                    else:
                        # If going over boundary, cut scene
                        if videoLength + fileLength > boundaries[numBound]-BOUNDARY_OFFSET :
                            fileLength = boundaries[numBound]-BOUNDARY_OFFSET-videoLength
                            subprocess.call(['ffmpeg', '-loglevel', 'error', '-t', str(fileLength), '-i', filename+'.mp4', '-q', '0', tempDir+os.path.basename(filename)+'.MTS'])
                        else :
                            subprocess.call(['ffmpeg', '-loglevel', 'error', '-i', filename+'.mp4', '-q', '0', tempDir+os.path.basename(filename)+'.MTS'])
                    
                    vidList.write("file '"+tempDir+os.path.basename(filename)+".MTS'\n")
                    videoLength += fileLength
                    indexes[numClus]+=1
                    
                else:
                    numClus = (numClus+1)%NUM_CLUS_IN_VIDEO

            # next boundary
            if numBound<len(boundaries)-1:
                numClus = (numClus+1)%NUM_CLUS_IN_VIDEO
                numBound += 1

            else:
                break

        # find only one video to end for the last seconds
        indexes[numClus] %= len(clus[numClus])
        while fileLength < boundaries[-1]-videoLength and indexes != [0]*NUM_CLUS_IN_VIDEO:
            if indexes[numClus] == 0: # if reached end of cluster, go to next cluster
                numClus = (numClus+1)%NUM_CLUS_IN_VIDEO
                indexes[numClus] %= len(clus[numClus])
            else:
                fileLength = clus[numClus].iloc[indexes[numClus]]['length']
                filename = os.path.splitext(clus[numClus].iloc[indexes[numClus]]['file'])[0]
                indexes[numClus] = (indexes[numClus]+1)%len(clus[numClus])
        
        if indexes == [0]*NUM_CLUS_IN_VIDEO: # not found a video long enough -> no fade
            subprocess.call(['ffmpeg', '-y', '-loglevel', 'error', '-i', filename+'.mp4', '-q', '0', tempDir+os.path.basename(filename)+'.MTS'])
        else: # fade out last 2 sec
            print("Add fading effect.")
            subprocess.call(['ffmpeg', '-y', '-loglevel', 'error', '-i', filename+'.mp4', '-q', '0',
            '-vf', 'fade=t=out:st='+str(fileLength-2)+':d=2', tempDir+os.path.basename(filename)+'.MTS'])

        vidList.write("file '"+tempDir+os.path.basename(filename)+".MTS'\n")


'''
Generator function for printing out progress info
'''
def log_progress():
    while True:
        progress = yield
        print(progress)


'''
Main steps for building the mv
args : input, output, video genre (optionnal)
callback.send : function that gives feedback to user
'''
def main(args, callback=log_progress()):
    if callback is not None:  # Prime the generator
        next(callback)

    start = time.time()
    print('Analyzing music %s...'%args.input)

    if not os.path.exists(args.input):
        raise FileNotFoundError
    elif not os.path.isdir(args.data) and not args.data[-4:] == '.csv':
        if not os.path.exists(args.data):
            raise FileNotFoundError
        else:
            raise Exception('The data path must either be a .csv file or a folder')

    # 1. Get major changes in music
    callback.send('(1/3) Identifying significant rythm changes in music...\n This will take about a minute.')

    filterwarnings('ignore')
    boundaries, labels = msaf.process(args.input, boundaries_id='olda')

    if boundaries[-1] < 60 or boundaries[-1]>400:
        callback.send('Error : Please chose a music lasting between 60 and 400 seconds for getting a quality MV.')
        return -1
        
    callback.send('Key changes found at \n(%s) seconds\n'%' , '.join(map('{:.2f}'.format, boundaries)))

    if args.data[-4:] == '.csv':
        # 2. Find music genre and style (music video style = larger category of genre)
        musicGenre = args.genre
        musicStyle = ''
        if musicGenre == '': # No genre given, must find it

            title, artist, musicGenre, musicStyle = get_music_infos(args.input)

            if musicStyle == '':
                callback.send('Error : The algorithm did not manage to recognize the music genre.\n'
                                    'Please try with another music, or manually add genre with the argument --genre <name of genre> \n'
                                    'with genre in ('+','.join(AUTHORIZED_GENRES)+').')
                return -1
        else:
            musicStyle = convert_genre_to_style(musicGenre)
            if musicStyle == '':
                callback.send('Error : This genre is not authorized. Please input one of the following ('+\
                ','.join(AUTHORIZED_GENRES)+') or let the algorithm find the genre.')
                return -1


        # 3. With the music genre, find appropriate videos in database
        callback.send('(2/3) Music genre identified : %s. Fetching matching videos in database...\n'%musicGenre)
        
        # use k-means clustering result on scenes extracted from Music Videos with same genre and chose one resolution
        resolution = random.random()
        if resolution < RESOLUTION_PROBABILITY :
            resolution = '40'
        else:
            resolution = '16'
        clusterResult = pd.read_csv('statistics/kmeans_'+resolution+'_'+musicStyle+'.csv')

    else:
        # use k-means clustering result on scenes extracted from Music Videos with same genre
        listFiles = list_scenes(args.data,'json')
        callback.send('(2/3) Generating K-Means for the database...')
        clusterResult = compute_kmeans(listFiles)

    # 4. Join music scenes while respecting the clustering and the input music rythm
    callback.send('(3/3) Building the music video around these boundaries...\n This won \'t take long.\n')

    # Select and order videos for music clip
    tempDir = tempfile.mkdtemp('_music_video_build')+'/'
    print("Building the video file in folder %s"%tempDir)
    assemble_videos(clusterResult, boundaries, tempDir)

    # Concatenate videos
    subprocess.call(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', 'video_structure.txt',
    '-c', 'copy', '-an', tempDir+'temp_video.MTS'])

    # Put input music on top of resulting video
    extension = os.path.splitext(args.output)[1]
    if extension != '.avi' and extension != '.mkv':
        args.output = os.path.splitext(args.output)[0]+'.mp4'
        if extension != '.mp4' :
            print('No format within (avi,mkv,mp4) given. Using default mp4 ...')

    # copies video stream and replace audio of arg 0 by arg 1
    subprocess.call(['ffmpeg', '-y', '-loglevel', 'error', '-i', tempDir+'temp_video.MTS', '-i', args.input,
    '-c:v' ,'copy', '-map', '0:v:0', '-map', '1:a:0', args.output])

    print('Video file %s written.\n'%args.output)
    callback.send('--- Finished building the music video in %f seconds. ---'%(time.time()-start))

    # Delete temp files
    shutil.rmtree(tempDir)

    # Copy video to folder generated
    if os.path.exists('generatedmvs'):
        shutil.copyfile(args.output, 'generatedmvs/'+time.strftime('%Y-%m-%d_%H-%M-%S', time.gmtime())+'.mp4')

    if callback is not None:  # Close the generator
        callback.close()


