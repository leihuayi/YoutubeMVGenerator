from __future__ import print_function
import os
import glob
import time, re
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
def detectCropFile(fpath):
    if os.path.exists(fpath):
        print("File to detect crop: %s " % fpath)
        p = subprocess.Popen(["ffmpeg", "-i", fpath, "-vf", "cropdetect=24:16:0", "-vframes", "1000", "-f", "rawvideo", "-y", "/dev/null"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        infos = p.stderr.read().decode('utf-8')
        allCrops = re.findall("crop=\S+", infos)
        mostCommonCrop = Counter(allCrops).most_common(1)
        strCrop = mostCommonCrop[0][0][5:].split(":")
        return(strCrop[0]+"x"+strCrop[1])
    else:
        return ""


def main():
    folder = "../data"

    df = pd.read_csv("../statistics/songs_on_server.csv", sep=";")
    df = df[df["style"].notnull()]
    df["resolution"] = ""
    listVideos = []
    for index, row in df.iterrows():
        # listVideos.append(folder+"/"+row["id"]+".mp4")
        res = detectCropFile(folder+"/"+row["id"]+".mp4")
        row["resolution"] = res
    print(df.to_string())
    df.to_csv("../statistics/songs_on_server.csv", sep=";", index=False)

    '''
    if len(listVideos)>0:
        for video in listVideos:
            find_scenes(video)
    else:
        print("No videos to analyze.")'''

if __name__ == "__main__":
    main()
