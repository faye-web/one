# playback.py

from pydub import AudioSegment
import os
from .settings import STEPS, REPEATS, OUTPUT_DIR, OUTPUT_FILENAME

def play_sequence(grid, selected_samples, bpm, tracks):
    try:
        bpm = int(bpm)
        if bpm <= 0:
            raise ValueError
    except ValueError:
        print("Invalid BPM. Please enter a positive number.")
        return

    beat_duration_ms = 60000 / bpm / 2
    total_duration = int(beat_duration_ms * STEPS)
    loop = AudioSegment.silent(duration=total_duration)

    for row_index, track in enumerate(tracks):
        sample_name = selected_samples[row_index].get()
        sample_path = os.path.join("sounds", track["folder"], sample_name)

        try:
            sound = AudioSegment.from_file(sample_path)
        except Exception as e:
            print(f"Error loading {sample_path}: {e}")
            continue

        for col in range(STEPS):
            if grid[row_index][col]:
                position = int(col * beat_duration_ms)
                loop = loop.overlay(sound, position=position)

    loop = loop * REPEATS
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)
    loop.export(output_path, format="wav")
    print(f"Exported to {output_path}")
