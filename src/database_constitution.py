import os, glob, sys
import time
import re
import pandas as pd

from music_recognition import get_music_infos
from video_analysis import detect_crop, get_video_length, resize_video, get_video_resolution

def differential(a,b):
    return (a-b)/a

'''
Harmonize videos on server
either put them display 640x360 or 640x272
'''
def harmonize_video(vidFile):
    print("\n--------- Harmonizing video %s --------"%vidFile )

    start_time = time.time()

    crop_width, crop_height = map(int,detect_crop(vidFile).split("x")) # Size of video within the black bars
    real_width, real_height = map(int,get_video_resolution(vidFile).split("x")) # Size of video uncliding the black bars


    # Make videos ratio 16/9 (640x360)
    if (crop_width/crop_height < 2):
        print("Video radio %.2f ---> format 16/9"%(crop_width/crop_height))
        
        # if too high : crop on top
        if (crop_width/crop_height) < 16/9-0.1:
            print("Cropping height ... ")
            resize_video(vidFile, "crop=%d:%d"%(crop_width,crop_width*9/16))

        # if too wide : crop on side
        elif (crop_width/crop_height) > 16/9+0.1:
            print("Cropping width ... ")
            resize_video(vidFile, "crop=%d:%d"%(crop_height*16/9,crop_height))

    
    # Make videos ratio 40/17 (640x272)
    else :
        print("Video radio %.2f ---> format 40/17"%(crop_width/crop_height))

        # if too high : crop on top
        if (crop_width/crop_height < 40/17-0.1):
            print("Cropping height ... ")
            resize_video(vidFile, "crop=%d:%d"%(crop_width,crop_width*17/40))

        # if too wide : crop on side
        elif (crop_width/crop_height > 40/17+0.1):
            print("Cropping width ... ")
            resize_video(vidFile, "crop=%d:%d"%(crop_height*40/17,crop_height))


    # If still have black bars that do not fit format 640x360 - 640x272 (allow error 0.025), remove them
    crop_width, crop_height = map(int,detect_crop(vidFile).split("x"))
    real_width, real_height = map(int,get_video_resolution(vidFile).split("x"))

    if (differential(real_width,crop_width)>0.025 or (differential(real_height,crop_height)>0.025 and 
        abs(differential(real_height, crop_height)-0.244)>0.025)): # format 640x272
        print("Removing remaining black bars ...")
        resize_video(vidFile, "crop=%d:%d"%(crop_width, crop_height))


    # Have final width 640
    real_width, real_height = map(int,get_video_resolution(vidFile).split("x"))

    if real_width != 640:
        print("Current width = %d. Scaling to have 640 ..."%real_width)
        resize_video(vidFile, "scale=640:-2")

    # Have final height 360
    real_width, real_height = map(int,get_video_resolution(vidFile).split("x"))

    if real_height > 360:
        print("Current height = %d. Scaling to have 360 ..."%real_height)
        resize_video(vidFile, "crop=640:360")

    elif real_height < 360:
        print("Current height = %d. Scaling to have 360 ..."%real_height)
        resize_video(vidFile, "pad=640:360:(ow-iw)/2:(oh-ih)/2")

    
    print("Finished video reformatting in %.2f s"%(time.time() - start_time))



''' 
give in input the folder where all videos are (must contain / at end)
the audio files of the videos should have been extracted beforehand with ffmpeg
and put in the same folder 
'''
def database_info_to_csv():
    data = []
    name, artist, genres, style, resolution, length = ("","","","","","")

    for vidFile in glob.glob(sys.argv[1]+"*.mp4"):

        # Audio infos
        audFile = vidFile[:-3]+"mp3"
        if os.path.exists(audFile):
            name, artist, genres, style = get_music_infos(audFile)
        else:
            print("Audio file does not exist for video %s. Writing blank"%vidFile)
        
        # Video infos
        resolution = detect_crop(vidFile)
        length = get_video_length(vidFile)

        data.append((os.path.splitext(os.path.basename(vidFile))[0], name, artist, genres, style, resolution, length))

    colNames = "id, name, artist, genres, style, resolution, length".split(", ")
    df = pd.DataFrame(data, columns=colNames)
    df.to_csv("infos_videos.csv", sep=";", float_format="%.3f", index=False)


if __name__ == "__main__":  
    for vidFile in glob.glob(sys.argv[1]+"*.mp4"):
        harmonize_video(vidFile)
