import argparse
import src.generate_mv as gen

'''
CLI interface
typo :
python main.py --input /path/to/music.mp3 --ouput /path/to/video.mp4
'''
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i','--input', nargs='?', required=True, help='audio input path')
    parser.add_argument('-o','--output', nargs='?', required=True, help='video output path')
    parser.add_argument('-g','--genre', default='', help='audio input genre (pop, rock, rnb, ...)')
    parser.add_argument('-d','--data', required=True, help='either csv path, or database folder path')

    args = parser.parse_args()
    gen.main(args)