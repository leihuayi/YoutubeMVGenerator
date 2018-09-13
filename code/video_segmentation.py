from __future__ import print_function
import os
import glob
import time

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
FILE_SCENE_LENGH = 'scenes_length.csv'
FILE_SCENE_NUMBER = 'scenes_number.csv'

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

            # Store scenes length for statistics
            with open(FILE_SCENE_LENGH,'a') as myfile:
               for i, scene in enumerate(scene_list):
                   myfile.write('%d, %f\n' % (scene[1].get_frames()-scene[0].get_frames(), (scene[1]-scene[0]).get_seconds()))
            
            # Store number of scenes for statistics
            with open(FILE_SCENE_NUMBER,'a') as myfile:
                myfile.write('%d\n'%len(scene_list))

            # Split the video
            # folder = os.path.splitext(video_path)[0]
            # if os.path.exists(folder):
            #     print('--- STOP : The folder for this video already exists, it is probably already split.')
            # else:
            #     print('Splitting the video. Put scenes in %s/%s'%(folder,VIDEO_SPLIT_TEMPLATE))
            #     os.mkdir(folder)
            #     video_splitter.split_video_ffmpeg([video_path], scene_list, folder+"/"+VIDEO_SPLIT_TEMPLATE+".mp4", os.path.basename(folder),suppress_output=True)
            
            print("-- Finished video splitting in {:.2f}s --".format(time.time() - start_time))
        else:
            print('Ffmpeg is not installed on your computer. Please install it before running this code')

    finally:
        video_manager.release()

    return scene_list

def main():
    for video in glob.glob('../data/*.mp4'):
        find_scenes(video)


if __name__ == "__main__":
    main()
