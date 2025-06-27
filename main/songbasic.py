from pydub import AudioSegment
from pydub.playback import play
import time

# #loud-house-kick_137bpm_F_major
# kick = AudioSegment.from_file("./sounds/kick.wav")

# #high-clean-hi-hat
# hh = AudioSegment.from_file("./sounds/highhat.wav")

# #capital-clap-snap-2_C_minor
# snap = AudioSegment.from_file("./sounds/snap.wav")

#loud-house-kick_137bpm_F_major
kick = AudioSegment.from_file("./sounds/kick2.wav")

#high-clean-hi-hat
hh = AudioSegment.from_file("./sounds/highhat.wav")

#capital-clap-snap-2_C_minor
snap = AudioSegment.from_file("./sounds/snarevirus.wav")


bars = 4

bpm = 150
beat_duration = 60 / bpm * 1000  # duration of one beat in milliseconds
loop = AudioSegment.silent(duration=beat_duration * (4 * bars))


for i in range(4 * bars):
        loop = loop.overlay(kick, position=i * beat_duration)
        
for i in range(4 * bars):
        for j in range(4):
            position = 1 + i * beat_duration + (j * beat_duration / 4)
            loop = loop.overlay(hh, position=position)
            
for i in range(4 * bars):
        position = (i * 4 + 2) * beat_duration  # beat 3 of each bar
        loop = loop.overlay(snap, position=position)
        
loop.export("./zoutputs/yeah.wav", format="wav")