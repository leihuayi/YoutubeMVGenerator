# YoutubeMVGenerator

This python algorithm takes in input a music, and outputs a Music Video which fits the input music, made from segments of Youtube MVs.
This project was made in the wake of a Master Thesis in the Machine Learning department of Tsinghua University.

## Requirements

The best is to install the environment using conda.
* Python 3.5.6
* Librosa  `conda install -c conda-forge librosa`
* Pyscenedetect cd to folder then   `python setup.py install`
* Opencv    `pip install opencv-python`
* Msaf `pip install msaf`
* ACRCloud [Python SDK](https://github.com/acrcloud/acrcloud_sdk_python) `python -m pip install git+https://github.com/acrcloud/acrcloud_sdk_python`

## Generate a music video

### Requirements
For the algorithm to work, you must have a data folder containing, for each video :
* the video file (ex: video1.mp4)
* a folder of the name name (ex: video1/) containing :
    * all the video scenes from this video (ex: video1_001.mp4, video1_002.mp4, ...)
    * for each video scene file, a json file with 2 keys : its color histogram (array size 768) and its length in seconds

You also need a file statistics/songs_on_server.csv containing, for each video :
* the id (the file is named id.mp4)
* the style of the video (electro/hiphop/pop/rock)
* the resolution of the video (size within the black bars)

In the next section we explain how to create a database following these requirements.
Finally, you need to subscribe to an ACR Cloud API key and Last.FM API key if you want to use the genre recognition. Otherwise you can juste manually give the genre when running the algorithm.

### Running the algorithm

`main.py` takes 3 arguments, 2 required are the input and output path, the last one "genre" is optional and must be in the AUTHORIZED_GENRES list.

`python main.py --input /path/to/music.mp3 --output /path/to/output_video.mp4 (--genre pop)`

## Create the database
As explained above, the database must have a precise structure.
Here are the steps to easily create one.

1. Download Youtube videos in a data/ folder. You can use [youtube-dl](https://github.com/rg3/youtube-dl) for this.
2. Extract audio files from the videos. In bash :
`for file in data/*.mp4; do ffmpeg -i $file -ab 160k -ac 2 -ar 44100 -loglevel quiet -vn ${file%.*}.mp3; echo 'Extracted mp3 for' $file; done`
3. Create the `statistics/songs_on_server.csv` file by running the function `database_info_to_csv()` in `src/database_constitution.py`.
4. (Optional) Resize the videos so that they all have the same format by running the function `harmonize_video(video_path)` in `src/database_constitution.py`.
5. Extract the scenes for all the videos by running the function `find_scenes(video_path)` in `src/video_analysis.py`.
6. Store the color histogram and length for each scene in json file by running the function `store_color_features(data_path)` in `src/video_analysis.py`.



