from pydub import AudioSegment
from pydub.playback import play


kick = AudioSegment.from_file("./sounds/kick.wav")
#high-clean-hi-hat
hh = AudioSegment.from_file("./sounds/highhat.wav")

loop = AudioSegment.silent(duration=60 / 150 * 1000 * 4 * 4)  # 4 bars, 4 beats per bar, 150 bpm

def place_sound_on_grid(track, sound, bpm, bar, beats):
    beat_duration = 60000 / bpm  # ms per beat
    bar_start = (bar - 1) * beat_duration * 4  # assuming 4/4 time

    for beat in beats:
        position = int(bar_start + (beat - 1) * beat_duration)
        track = track.overlay(sound, position=position)

    return track

beats = [i * 0.25 + 1 for i in range(16)]
loop = place_sound_on_grid(loop, kick, 150, [1,2,3,4], [1,2,3,4])
loop = place_sound_on_grid(loop, hh, 150, [1,2,3,4], beats)

loop.export("./zoutputs/hh2.wav", format="wav")