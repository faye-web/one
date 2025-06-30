import os
import shutil

# ---- SET THESE ----
SAMPLES_DIR = "sounds/synth"  # <--- update to your actual folder path!
EXT = ".wav"
FIRST_CORRECT_NOTE = "a3"   # what the *first* sample should be called
FIRST_WRONG_NOTE  = "a1"    # what the first sample is *currently* called

# ---- Note mappings ----
# The order you have on disk
note_order = ['a', 'a#', 'b', 'c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#']

# Helper to convert note+octave to MIDI number
def note_to_midi(note, octave):
    base = {'c':0, 'c#':1, 'd':2, 'd#':3, 'e':4, 'f':5, 'f#':6, 'g':7, 'g#':8, 'a':9, 'a#':10, 'b':11}
    return (octave+1)*12 + base[note]

def midi_to_note_name(midi_num):
    names = note_order
    note = names[midi_num % 12]
    octave = midi_num // 12 - 1
    return f"{note}{octave}"

# --- Find starting MIDI for wrong/correct ---
def parse_note(note_str):
    if note_str[-2] == "#":
        name = note_str[:-1]
        octv = int(note_str[-1])
    else:
        name = note_str[:-1]
        octv = int(note_str[-1])
    return name.lower(), octv

wrong_name, wrong_oct = parse_note(FIRST_WRONG_NOTE)
correct_name, correct_oct = parse_note(FIRST_CORRECT_NOTE)

wrong_start_midi = note_to_midi(wrong_name, wrong_oct)
correct_start_midi = note_to_midi(correct_name, correct_oct)

# --- Gather & sort files by current wrong label ---
files = [f for f in os.listdir(SAMPLES_DIR) if f.endswith(EXT)]
files_sorted = []

# Gather all (e.g., a1, a#1, b1, ... g#5) in order
for octv in range(wrong_oct, 6):  # 6 because g#5 is in octave 5
    for note in note_order:
        fname = f"{note}{octv}{EXT}"
        if fname in files:
            files_sorted.append(fname)

# --- Rename each one ---
for i, old_file in enumerate(files_sorted):
    # The midi number it *should* be
    midi = correct_start_midi + i
    new_name = midi_to_note_name(midi) + EXT
    old_path = os.path.join(SAMPLES_DIR, old_file)
    new_path = os.path.join(SAMPLES_DIR, new_name)
    print(f"{old_file}  ->  {new_name}")
    shutil.move(old_path, new_path)

print("Done renaming files!")