import msaf
import librosa
import librosa.display

file_name = "../Tests/9bZkp7q19f0"

# Choose an audio file and listen to it
audio_file = file_name+".mp3"

y, sr = librosa.load(audio_file)
librosa.display.waveplot(y, sr)

# Segment the file using the default MSAF parameters
boundaries, labels = msaf.process(audio_file)
print(boundaries)

# Sonify boundaries
sonified_file = file_name+"_boundaries.wav"
sr = 44100
boundaries, labels = msaf.process(audio_file, sonify_bounds=True, out_bounds=sonified_file, out_sr=sr)

# Listen to results
audio = librosa.load(sonified_file, sr=sr)[0]
librosa.display.waveplot(audio)
