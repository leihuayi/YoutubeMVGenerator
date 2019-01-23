from __future__ import print_function
import os, glob, shutil
import time
import re
import pandas as pd
import subprocess
from collections import Counter

# Standard PySceneDetect imports:
from scenedetect.video_manager import VideoManager
from scenedetect.scene_manager import SceneManager

# For caching detection metrics and saving/loading to a stats file
from scenedetect.stats_manager import StatsManager

# For content-aware scene detection:
from scenedetect.detectors.content_detector import ContentDetector

# For splitting video:
import scenedetect.video_splitter as video_splitter

VIDEO_SPLIT_TEMPLATE = '$VIDEO_NAME-$SCENE_NUMBER'
FILE_SCENE_LENGH = '../statistics/scenes_length.csv'
FILE_SCENE_NUMBER = '../statistics/scenes_number.csv'


'''
Split video into scenes (one camera movement)
'''
def find_scenes(video_path):
    start_time = time.time()
    print("Analyzing video "+video_path)

    # type: (str) -> List[Tuple[FrameTimecode, FrameTimecode]]
    video_manager = VideoManager([video_path])
    stats_manager = StatsManager()

    # Pass StatsManager to SceneManager to accelerate computing time
    scene_manager = SceneManager(stats_manager)

    # Add ContentDetector algorithm (each detector's constructor
    # takes detector options, e.g. threshold).
    scene_manager.add_detector(ContentDetector())
    base_timecode = video_manager.get_base_timecode()

    # We save our stats file to {VIDEO_PATH}.stats.csv.
    stats_file_path = '%s.stats.csv' % (video_path)

    scene_list = []

    folder = os.path.splitext(video_path)[0]

    if os.path.exists(folder):
        print('--- STOP : The folder for this video already exists, it is probably already split.')

    else:
        try:
            # If stats file exists, load it.
            if os.path.exists(stats_file_path):
                # Read stats from CSV file opened in read mode:
                with open(stats_file_path, 'r') as stats_file:
                    stats_manager.load_from_csv(stats_file, base_timecode)
            
            if video_splitter.is_ffmpeg_available():
                # Set downscale factor to improve processing speed.
                video_manager.set_downscale_factor()

                # Start video_manager.
                video_manager.start()

                # Perform scene detection on video_manager.
                scene_manager.detect_scenes(frame_source=video_manager)

                # Obtain list of detected scenes.
                scene_list = scene_manager.get_scene_list(base_timecode)
                # Each scene is a tuple of (start, end) FrameTimecodes.

                print('%s scenes obtained' % len(scene_list))

                if len(scene_list)>0:
                    # STATISTICS : Store scenes length
                    with open(FILE_SCENE_LENGH,'a') as myfile:
                       for i, scene in enumerate(scene_list):
                           myfile.write('%s, %d, %f\n' % (os.path.basename(video_path), scene[1].get_frames()-scene[0].get_frames(), (scene[1]-scene[0]).get_seconds()))
                    
                    # STATISTICS : Store number of scenes
                    with open(FILE_SCENE_NUMBER,'a') as myfile:
                        myfile.write('%d\n'%len(scene_list))

                    # Split the video
                    print('Splitting the video. Put scenes in %s/%s'%(folder,VIDEO_SPLIT_TEMPLATE))
                    os.mkdir(folder)
                    video_splitter.split_video_ffmpeg([video_path], scene_list, folder+"/"+VIDEO_SPLIT_TEMPLATE+".mp4", os.path.basename(folder),suppress_output=True)
            
                print("-- Finished video splitting in {:.2f}s --".format(time.time() - start_time))
            else:
                print('Ffmpeg is not installed on your computer. Please install it before running this code')

        finally:
            video_manager.release()

    return scene_list


'''
Get video width and height
'''
def detect_crop(video_path):
    if os.path.exists(video_path):
        print("File to detect crop: %s " % video_path)
        p = subprocess.Popen(["ffmpeg", "-i", video_path, "-vf", "cropdetect=24:16:0", "-vframes", "1500", "-f", "rawvideo", "-y", "/dev/null"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        infos = p.stderr.read().decode('utf-8')
        allCrops = re.findall("crop=\S+", infos)
        mostCommonCrop = Counter(allCrops).most_common(1)
        strCrop = mostCommonCrop[0][0][5:].split(":")
        return(strCrop[0]+"x"+strCrop[1])
    else:
        return ""


'''
Crop a video along given dimensions
'''
def crop(video_path, dimension):
    if os.path.exists(video_path):
        start_time = time.time()
        temp_path = os.path.splitext(video_path)[0]+"_temp"+os.path.splitext(video_path)[1]
        os.rename(video_path,temp_path)
        try:
           subprocess.call(["ffmpeg", "-loglevel", "error",  "-i", temp_path, "-vf", "crop="+dimension, video_path])
           print("-- Finished video cropping in {:.2f}s --".format(time.time() - start_time))

           # remove original video
           os.remove(temp_path)

        except:
            print("Problem while running ffmpeg")
            os.rename(temp_path,video_path)



'''
Resize videos to 640 in width
'''
def resize_video(video_path):
    if os.path.exists(video_path):
        start_time = time.time()
        temp_path = os.path.splitext(video_path)[0]+"_temp"+os.path.splitext(video_path)[1]
        os.rename(video_path,temp_path)
        try:
            subprocess.call(["ffmpeg", "-loglevel", "error",  "-i", temp_path, "-vf", "scale=640:-2", video_path])
            print("-- Finished video resizing in {:.2f}s --".format(time.time() - start_time))

            # delete original video
            os.remove(temp_path)
            
        except:
            print("Problem while running ffmpeg")
            os.rename(temp_path,video_path)


'''
Get video length
'''
def get_video_length(video_path):
    if os.path.exists(video_path):
        duration = subprocess.check_output(['ffprobe', '-i', video_path, '-show_entries', 'format=duration', '-v', 'quiet', '-of', 'csv=%s' % ("p=0")])
        return duration.decode('utf-8')[:-1] # remove \n at end
    else:
        return ""


def main():
    folder = "../data"

    df = pd.read_csv("../statistics/songs_on_server.csv", sep=";")

    listVideos = []
    vid_path = ""
    for index, row in df.iterrows():
        vid_path = folder+"/"+row["id"]+".mp4"
        # listVideos.append(vid_path)
        height = int(row["resolution"][4:])

        if height<350 and height>320:
            crop(vid_path,"%d:%d"%(height*16/9,height))
            resize_video(vid_path)
            res = detect_crop(vid_path)
            df.loc[index,"resolution"] = res
            print(res)

    df.to_csv("../statistics/songs_on_server.csv", sep=";", index=False)

    '''
    if len(listVideos)>0:
        for video in listVideos:
            find_scenes(video)
    else:
        print("No videos to analyze.")'''

if __name__ == "__main__":
    main()
