import tkinter as tk
from tkinter import ttk
from pydub import AudioSegment
import pygame
import os
from piano_roll import PianoRollCanvas

# ==== CONFIG ====
SOUNDS_DIR = "sounds"
STEPS = 64
DEFAULT_BPM = 120
REPEATS = 4

pygame.mixer.init()

# ==== STATE ====
class TrackRow:
    def __init__(self, parent, index, remove_callback, small_pixel):
        self.index = index
        self.folder_var = tk.StringVar()
        self.file_var = tk.StringVar()
        self.mute_var = tk.BooleanVar(value=False)
        self.buttons = []
        self.grid = [0] * STEPS
        self.frame = tk.Frame(parent)
        self.frame.grid(row=index, column=0, sticky="w")

        self.folder_dropdown = ttk.Combobox(self.frame, textvariable=self.folder_var, values=self.get_folders(), width=10, state="readonly")
        self.folder_dropdown.grid(row=0, column=0)

        self.file_dropdown = ttk.Combobox(self.frame, textvariable=self.file_var, values=[], width=15, state="readonly")
        self.file_dropdown.grid(row=0, column=1)

        self.folder_var.trace_add("write", self.update_file_list)
        self.folder_var.set(self.get_folders()[0])

        self.mute_button = tk.Checkbutton(self.frame, text="Mute", variable=self.mute_var, command=self.update_all_buttons)
        self.mute_button.grid(row=0, column=2)

        self.remove_button = tk.Button(self.frame, text="X", command=lambda: remove_callback(self), bg="salmon")
        self.remove_button.grid(row=0, column=3, padx=5)

        self.step_frame = tk.Frame(self.frame)
        self.step_frame.grid(row=0, column=4, padx=5)
        for col in range(STEPS):
            base_color = "white" if (col // 4) % 2 == 0 else "lightgray"
            btn = tk.Button(self.step_frame, image=small_pixel, bg=base_color,
                            command=lambda c=col: self.toggle_step(c))
            btn.image = small_pixel
            btn.grid(row=0, column=col, padx=0, pady=0, ipadx=0, ipady=0)
            self.buttons.append(btn)

    def get_folders(self):
        return [f for f in os.listdir(SOUNDS_DIR) if os.path.isdir(os.path.join(SOUNDS_DIR, f))]

    def update_file_list(self, *args):
        folder = self.folder_var.get()
        files = [f for f in os.listdir(os.path.join(SOUNDS_DIR, folder)) if f.endswith(".wav")]
        self.file_dropdown["values"] = files
        if files:
            self.file_var.set(files[0])

    def toggle_step(self, col):
        self.grid[col] = 1 - self.grid[col]
        self.update_button_color(col)

    def update_button_color(self, col, highlight=False):
        is_muted = self.mute_var.get()
        filled = self.grid[col] == 1
        base_color = "white" if (col // 4) % 2 == 0 else "lightgray"

        if is_muted:
            color = "black" if filled else base_color
        else:
            color = "green" if filled else base_color

        if highlight:
            if is_muted:
                color = "#505050" if filled else "#B0B0B0"
            else:
                color = "#00FF00" if filled else "#686464"

        self.buttons[col].configure(bg=color)

    def update_all_buttons(self):
        for col in range(STEPS):
            self.update_button_color(col)

    def highlight_column(self, col, highlight=True):
        self.update_button_color(col, highlight)

    def destroy(self):
        self.frame.destroy()

# ==== MAIN ====
class SequencerApp:
    def __init__(self, root):
        self.root = root
        root.title("Dynamic Beat Sequencer")

        self.track_rows = []
        self.playback_after_id = None
        self.is_playing = False

        self.small_pixel = tk.PhotoImage(width=20, height=40)

        self.bpm_label = tk.Label(root, text="BPM:")
        self.bpm_label.grid(row=0, column=0)
        self.bpm_entry = tk.Entry(root, width=5)
        self.bpm_entry.insert(0, str(DEFAULT_BPM))
        self.bpm_entry.grid(row=0, column=1)

        tk.Button(root, text="Add Row", command=self.add_row).grid(row=0, column=2)

        self.play_toggle_btn = tk.Button(root, text="Play", command=self.toggle_playback, bg="lightgreen")
        self.play_toggle_btn.grid(row=0, column=3)

        tk.Button(root, text="Export", command=self.show_export_dialog, bg="lightblue").grid(row=0, column=4)

        self.toggle_piano_button = tk.Button(root, text="Toggle Piano Roll", command=self.toggle_piano_roll, bg="lavender")
        self.toggle_piano_button.grid(row=0, column=5)

        self.track_frame = tk.Frame(root)
        self.track_frame.grid(row=1, column=0, columnspan=6, pady=10)

        self.piano_visible = False
        self.piano_roll_frame = tk.Frame(root)
        self.piano_roll = PianoRollCanvas(self.piano_roll_frame, steps=STEPS)
        self.piano_roll.pack()

        self.add_row()

    def toggle_playback(self):
        if self.is_playing:
            self.stop_playback()
            self.play_toggle_btn.configure(text="Play", bg="lightgreen")
        else:
            self.play_sequence()
            self.play_toggle_btn.configure(text="Stop", bg="salmon")

    def toggle_piano_roll(self):
        if self.piano_visible:
            self.piano_roll_frame.grid_forget()
            self.piano_visible = False
        else:
            self.piano_roll_frame.grid(row=2, column=0, columnspan=6)
            self.piano_visible = True

    def add_row(self):
        index = len(self.track_rows)
        row = TrackRow(self.track_frame, index, self.remove_row, self.small_pixel)
        self.track_rows.append(row)

    def remove_row(self, row):
        if row in self.track_rows:
            row.destroy()
            self.track_rows.remove(row)
            self.refresh_rows()

    def refresh_rows(self):
        for i, row in enumerate(self.track_rows):
            row.index = i
            row.frame.grid(row=i, column=0)

    def play_sequence(self):
        if self.is_playing:
            return

        try:
            bpm = int(self.bpm_entry.get())
            if bpm <= 0:
                raise ValueError
        except ValueError:
            print("Invalid BPM")
            return

        beat_duration_ms = int(60000 / bpm / 2)
        self.sounds = []

        for row in self.track_rows:
            path = os.path.join(SOUNDS_DIR, row.folder_var.get(), row.file_var.get())
            try:
                self.sounds.append(pygame.mixer.Sound(path))
            except:
                self.sounds.append(None)

        self.is_playing = True

        def step(col=0):
            if not self.is_playing:
                for row in self.track_rows:
                    row.highlight_column((col - 1) % STEPS, highlight=False)
                return

            for row_index in range(min(len(self.track_rows), len(self.sounds))):
                row = self.track_rows[row_index]
                row.highlight_column((col - 1) % STEPS, highlight=False)
                row.highlight_column(col, highlight=True)

                if row.grid[col] and not row.mute_var.get():
                    sound = self.sounds[row_index]
                    if sound:
                        sound.play()

            next_col = (col + 1) % STEPS
            self.playback_after_id = self.root.after(beat_duration_ms, lambda: step(next_col))

        step()

    def stop_playback(self):
        if self.is_playing:
            self.is_playing = False
            if self.playback_after_id:
                self.root.after_cancel(self.playback_after_id)
            for row in self.track_rows:
                for col in range(STEPS):
                    row.highlight_column(col, highlight=False)
            self.play_toggle_btn.configure(text="Play", bg="lightgreen")

    def show_export_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Export Options")

        tk.Label(dialog, text="Filename:").grid(row=0, column=0)
        filename_entry = tk.Entry(dialog)
        filename_entry.insert(0, "nba.wav")
        filename_entry.grid(row=0, column=1)

        tk.Label(dialog, text="Bars:").grid(row=1, column=0)
        bars_entry = tk.Entry(dialog)
        bars_entry.insert(0, str(REPEATS))
        bars_entry.grid(row=1, column=1)

        def do_export():
            filename = filename_entry.get()
            try:
                bars = int(bars_entry.get())
                if bars <= 0:
                    raise ValueError
            except ValueError:
                print("Invalid bar count")
                return
            dialog.destroy()
            self.export_sequence(filename, bars)

        tk.Button(dialog, text="Export", command=do_export, bg="lightblue").grid(row=2, column=0, columnspan=2, pady=5)

    def export_sequence(self, filename="nba.wav", bars=REPEATS):
        try:
            bpm = int(self.bpm_entry.get())
            if bpm <= 0:
                raise ValueError
        except ValueError:
            print("Invalid BPM")
            return

        beat_duration_ms = 60000 / bpm / 2
        total_duration = int(beat_duration_ms * STEPS)
        loop = AudioSegment.silent(duration=total_duration)

        for row in self.track_rows:
            if row.mute_var.get():
                continue
            path = os.path.join(SOUNDS_DIR, row.folder_var.get(), row.file_var.get())
            try:
                sound = AudioSegment.from_file(path)
            except:
                continue
            for col in range(STEPS):
                if row.grid[col]:
                    pos = int(col * beat_duration_ms)
                    loop = loop.overlay(sound, position=pos)

        loop = loop * bars
        os.makedirs("zoutputs", exist_ok=True)
        output_path = os.path.join("zoutputs", filename)
        loop.export(output_path, format="wav")
        print(f"Exported to {output_path}")

# ==== RUN ====
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("2400x1200")
    app = SequencerApp(root)
    root.mainloop()