import argparse
import src.generate_mv as gen

'''
CLI interface
typo :
python main.py --input /path/to/music.mp3 --ouput /path/to/video.mp4
'''
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', nargs='?', required=True)
    parser.add_argument('--output', nargs='?', required=True)
    parser.add_argument('--genre', default='')

    args = parser.parse_args()
    gen.main(args)