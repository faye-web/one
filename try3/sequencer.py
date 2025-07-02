import tkinter as tk
from tkinter import ttk
import os
import io
import pygame
from draggable_panel import DraggablePanel
from piano_roll import PianoRollCanvas

SOUNDS_DIR = "sounds"
STEPS = 64
DEFAULT_BPM = 120

pygame.mixer.init(frequency=44100, size=-16, channels=2)
from pydub import AudioSegment

def midi_to_note_name(midi_num):
    names = ['c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#', 'a', 'a#', 'b']
    note = names[midi_num % 12]
    octave = midi_num // 12 - 1
    return f"{note}{octave}".lower()

def synth_sample_path(midi_num, synth_folder="synth"):
    note_name = midi_to_note_name(midi_num)
    fname = f"{note_name}.wav"
    fullpath = os.path.join(SOUNDS_DIR, synth_folder, fname)
    return fullpath

class TrackRow:
    def __init__(self, parent, index, remove_callback, piano_roll_callback, cell_width=20, cell_height=20, steps=64):
        self.index = index
        self.steps = steps
        self.cell_width = cell_width
        self.cell_height = cell_height
        self.grid = [0] * self.steps
        self.current_play_col = None
        self.piano_roll_notes = []
        self.is_piano_roll = False

        self.frame = tk.Frame(parent, bg="#18191b")
        self.frame.grid(row=index, column=0, sticky="w", pady=0)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox", fieldbackground="#22272c", background="#22272c", foreground="#b6bdc2", borderwidth=0)
        style.map("TCombobox", fieldbackground=[('readonly', "#22272c")], background=[('readonly', "#22272c")])

        self.instrument_var = tk.StringVar(value="Drum Pad")
        self.instrument_dropdown = ttk.Combobox(
            self.frame, textvariable=self.instrument_var, values=["Drum Pad", "Piano Roll"], width=9, state="readonly", style="TCombobox"
        )
        self.instrument_dropdown.grid(row=0, column=0, padx=(2,2))
        self.instrument_var.trace_add("write", self.on_instrument_change)

        self.folder_var = tk.StringVar()
        self.file_var = tk.StringVar()
        self.mute_var = tk.BooleanVar(value=False)

        self.folder_dropdown = ttk.Combobox(
            self.frame, textvariable=self.folder_var, values=self.get_folders(), width=8, state="readonly", style="TCombobox")
        self.folder_dropdown.grid(row=0, column=1, padx=(2,2))
        self.folder_var.trace_add("write", self.update_file_list)

        self.file_dropdown = ttk.Combobox(
            self.frame, textvariable=self.file_var, values=[], width=10, state="readonly", style="TCombobox")
        self.file_dropdown.grid(row=0, column=2, padx=(2,2))

        self.file_placeholder = ttk.Combobox(
            self.frame,
            values=["(by note)"],
            state="disabled",
            width=10,
            style="TCombobox"
        )
        self.file_placeholder.set("(by note)")
        self.file_placeholder.grid(row=0, column=2, padx=(2,2))
        self.file_placeholder.grid_remove()

        folders = self.get_folders()
        if folders:
            self.folder_var.set(folders[0])

        self.mute_button = tk.Checkbutton(
            self.frame, text="Mute", variable=self.mute_var, bg="#18191b", fg="#b6bdc2", selectcolor="#444",
            command=self.draw_grid)
        self.mute_button.grid(row=0, column=3)

        self.piano_roll_button = tk.Button(
            self.frame, text="PR", command=lambda: piano_roll_callback(self), bg="#25292c", fg="#fff", width=2, bd=0, relief="flat", activebackground="#444"
        )
        self.piano_roll_button.grid(row=0, column=4, padx=2)

        self.remove_button = tk.Button(
            self.frame, text="X", command=lambda: remove_callback(self), bg="#25292c", fg="#ff6161", width=2, bd=0, relief="flat", activebackground="#333")
        self.remove_button.grid(row=0, column=5, padx=2)

        self.canvas = tk.Canvas(self.frame,
            width=cell_width*steps,
            height=cell_height,
            bg="#18191b",
            highlightthickness=0,
        )
        self.canvas.grid(row=0, column=6, padx=(6,0))
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.draw_grid()

        self.pr_panel = None
        self.on_instrument_change()

    def get_folders(self):
        if not os.path.isdir(SOUNDS_DIR):
            return []
        return [f for f in os.listdir(SOUNDS_DIR) if os.path.isdir(os.path.join(SOUNDS_DIR, f))]

    def update_file_list(self, *args):
        folder = self.folder_var.get()
        path = os.path.join(SOUNDS_DIR, folder)
        if not os.path.isdir(path):
            self.file_dropdown["values"] = []
            return
        files = [f for f in os.listdir(path) if f.endswith(".wav")]
        self.file_dropdown["values"] = files
        if files:
            self.file_var.set(files[0])

    def on_instrument_change(self, *args):
        instrument = self.instrument_var.get()
        folders = self.get_folders()
        if instrument == "Drum Pad":
            self.is_piano_roll = False
            self.piano_roll_button.config(state="disabled", bg="#18191b", fg="#888", cursor="X_cursor")
            # Restore ALL folders as choices, not just synth!
            self.folder_dropdown["values"] = folders
            if folders and self.folder_var.get() not in folders:
                self.folder_var.set(folders[0])
            self.folder_dropdown.grid()
            self.file_dropdown.grid()
            self.file_placeholder.grid_remove()
            self.update_file_list()
        else:  # "Piano Roll"
            self.is_piano_roll = True
            self.piano_roll_button.config(state="normal", bg="#25292c", fg="#fff", cursor="")
            # Force folder to "synth" if present, restrict choices
            if "synth" in folders:
                self.folder_var.set("synth")
                self.folder_dropdown["values"] = ["synth"]
            else:
                self.folder_dropdown["values"] = folders  # fallback
            self.folder_dropdown.grid()
            self.file_dropdown.grid_remove()
            self.file_placeholder.grid()
        self.draw_grid()

    def draw_grid(self):
        self.canvas.delete("all")
        instrument = self.instrument_var.get()
        is_muted = self.mute_var.get()
        if instrument == "Piano Roll":
            fill_color = "#000" if is_muted else "#23262e"
            text_color = "#444" if is_muted else "#eb42e2"
            self.canvas.create_rectangle(
                0, 0, self.steps * self.cell_width, self.cell_height,
                fill=fill_color, outline="#111317", width=1
            )
            self.canvas.create_text(
                (self.steps * self.cell_width)//2, self.cell_height//2,
                text="Piano Roll Active",
                fill=text_color, font=("Segoe UI", 12, "bold")
            )
            return
        for col in range(self.steps):
            x1 = col * self.cell_width
            x2 = x1 + self.cell_width
            y1 = 0
            y2 = self.cell_height
            if is_muted:
                fill = "#444" if self.grid[col] else "#000"
            else:
                bg = "#20232b" if (col // 4) % 2 == 0 else "#23262e"
                fill = "#19ffe6" if self.grid[col] else bg
            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=fill,
                outline="#111317",
                width=1
            )

    def on_canvas_click(self, event):
        if self.instrument_var.get() == "Piano Roll":
            return
        col = event.x // self.cell_width
        if 0 <= col < self.steps:
            self.grid[col] = 1 - self.grid[col]
            self.draw_grid()

    def highlight_column(self, col, highlight=True):
        self.canvas.delete("highlight")
        if highlight and 0 <= col < self.steps and self.instrument_var.get() == "Drum Pad":
            x1 = col * self.cell_width
            x2 = x1 + self.cell_width
            y1 = 0
            y2 = self.cell_height
            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill="#2c2c2c",
                outline="#d3d3d3",
                width=2,
                stipple="gray50",
                tags="highlight"
            )

    def clear_highlight(self):
        self.canvas.delete("highlight")

    def destroy(self):
        self.frame.destroy()


class SequencerApp:
    def __init__(self, root, parent, cell_width=20, cell_height=20):
        self.root = root
        self.parent = parent
        self.track_rows = []
        self.playback_after_id = None
        self.is_playing = False
        self.cell_width = cell_width
        self.cell_height = cell_height
        self.pr_panels = {}

        tk.Label(parent, text="BPM:", fg="#b6bdc2", bg="#18191b").grid(row=0, column=0, padx=2)
        self.bpm_entry = tk.Entry(parent, width=5, bg="#22272c", fg="#fff", insertbackground="#19ffe6", borderwidth=0, highlightthickness=0)
        self.bpm_entry.insert(0, str(DEFAULT_BPM))
        self.bpm_entry.grid(row=0, column=1, padx=2)

        tk.Button(parent, text="Add Row", command=self.add_row, bg="#25292c", fg="#b6fdc2", bd=0, activebackground="#20232b").grid(row=0, column=2, padx=2)
        self.play_toggle_btn = tk.Button(parent, text="Play", command=self.toggle_playback, bg="#222", fg="#19ffe6", bd=0, activebackground="#25292c")
        self.play_toggle_btn.grid(row=0, column=3, padx=2)
        tk.Button(parent, text="Export", command=self.show_export_dialog, bg="#25292c", fg="#b6bdc2", bd=0).grid(row=0, column=4, padx=2)

        self.track_frame = tk.Frame(parent, bg="#18191b")
        self.track_frame.grid(row=1, column=0, columnspan=5, pady=4, sticky="w")

        self.add_row()

    def add_row(self):
        index = len(self.track_rows)
        row = TrackRow(
            self.track_frame, index, self.remove_row, self.open_piano_roll,
            cell_width=self.cell_width, cell_height=self.cell_height
        )
        self.track_rows.append(row)

    def remove_row(self, row):
        if row in self.pr_panels:
            panel = self.pr_panels.pop(row)
            panel.destroy()
        if row in self.track_rows:
            row.destroy()
            self.track_rows.remove(row)
            self.refresh_rows()

    def refresh_rows(self):
        for i, row in enumerate(self.track_rows):
            row.index = i
            row.frame.grid(row=i, column=0, pady=1)

    def open_piano_roll(self, row):
        if row.instrument_var.get() != "Piano Roll":
            return

        panel = self.pr_panels.get(row)
        if panel:
            if not panel.winfo_ismapped():
                panel.restore_panel()
            panel.lift()
            return

        panel = DraggablePanel(
            self.root, title=f"Piano Roll: {row.folder_var.get()}",
            x=120 + row.index*40, y=290 + row.index*40, width=900, height=350,
            min_width=600, min_height=120,
        )

        pr_canvas = PianoRollCanvas(
            panel.body, steps=STEPS, cell_width=self.cell_width,
            cell_height=self.cell_height, sidebar_width=90,
        )

        pr_canvas.notes_list = [dict(n) for n in row.piano_roll_notes]
        pr_canvas.draw_grid()
        pr_canvas.pack(fill="both", expand=True)
        panel.pr_canvas = pr_canvas
        row.pr_panel = panel
        self.pr_panels[row] = panel

        def on_destroy(event=None):
            if row in self.pr_panels:
                del self.pr_panels[row]
            row.pr_panel = None
        panel.bind("<Destroy>", on_destroy)

        def on_unmap(event=None):
            if hasattr(panel, 'pr_canvas') and panel.pr_canvas:
                row.piano_roll_notes = [dict(n) for n in panel.pr_canvas.notes_list]
        panel.bind("<Unmap>", on_unmap)

    def toggle_playback(self):
        if self.is_playing:
            self.stop_playback()
            self.play_toggle_btn.configure(text="Play", bg="#222", fg="#19ffe6")
        else:
            self.play_sequence()
            self.play_toggle_btn.configure(text="Stop", bg="#ff6161", fg="#fff")

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
        beat_duration_ms = float(60000 / bpm / 2)

        # --- SYNC PIANO ROLL NOTES ---
        for row, panel in self.pr_panels.items():
            if hasattr(panel, 'pr_canvas') and panel.pr_canvas:
                row.piano_roll_notes = [dict(n) for n in panel.pr_canvas.notes_list]

        self.sounds = []
        self.pr_note_cache = []
        for row in self.track_rows:
            if row.is_piano_roll:
                self.sounds.append(None)
                self.pr_note_cache.append([dict(n) for n in row.piano_roll_notes])
            else:
                path = os.path.join(SOUNDS_DIR, row.folder_var.get(), row.file_var.get())
                try:
                    self.sounds.append(pygame.mixer.Sound(path))
                except Exception as e:
                    print(f"Failed to load sound: {path}. Error: {e}")
                    self.sounds.append(None)
                self.pr_note_cache.append(None)
        self.is_playing = True

        def step(col=0):
            for row_index, row in enumerate(self.track_rows):
                if row.is_piano_roll:
                    if row in self.pr_panels and hasattr(self.pr_panels[row], 'pr_canvas') and self.pr_panels[row].pr_canvas:
                        notes = [dict(n) for n in self.pr_panels[row].pr_canvas.notes_list]
                    else:
                        notes = [dict(n) for n in row.piano_roll_notes]
                    for note in notes:
                        if note['start'] == col and not row.mute_var.get():
                            steps_long = note['end'] - note['start'] + 1
                            ms_long = float(steps_long * beat_duration_ms)
                            midi_num = 108 - note['row']
                            folder = row.folder_var.get()
                            sample_path = synth_sample_path(midi_num, folder)
                            if not os.path.isfile(sample_path):
                                print(f"  File does not exist: {sample_path}")
                                continue
                            try:
                                seg = AudioSegment.from_file(sample_path)
                            except Exception as e:
                                print(f"  Couldn't load {sample_path}: {e}")
                                continue
                            BUFFER_MS = 1000
                            note_sound = seg[:int(ms_long + BUFFER_MS)]
                            buf = io.BytesIO()
                            note_sound.export(buf, format="wav")
                            buf.seek(0)
                            try:
                                sample = pygame.mixer.Sound(file=buf)
                                sample.play()
                            except Exception as e:
                                print(f"  Playback failed: {e}")
                else:
                    row.highlight_column(col)
                    if row.grid[col] and not row.mute_var.get():
                        sound = self.sounds[row_index]
                        if sound:
                            sound.play()
                # VISUAL PLAYHEAD for Piano Roll:
                if hasattr(row, "pr_panel") and row.pr_panel and hasattr(row.pr_panel, "pr_canvas"):
                    row.pr_panel.pr_canvas.set_playhead(col)
            next_col = (col + 1) % STEPS
            self.playback_after_id = self.root.after(int(beat_duration_ms), lambda: step(next_col))
        step()

    def stop_playback(self):
        if self.is_playing:
            self.is_playing = False
            if self.playback_after_id:
                self.root.after_cancel(self.playback_after_id)
            for row in self.track_rows:
                if not row.is_piano_roll:
                    row.clear_highlight()
                if hasattr(row, "pr_panel") and row.pr_panel and hasattr(row.pr_panel, "pr_canvas"):
                    row.pr_panel.pr_canvas.clear_playhead()
            self.play_toggle_btn.configure(text="Play", bg="#222", fg="#19ffe6")

    def show_export_dialog(self):
        import tkinter.simpledialog
        filename = tkinter.simpledialog.askstring("Export", "Filename (e.g. nba.wav):", initialvalue="nba.wav")
        if not filename:
            return
        bars = tkinter.simpledialog.askinteger("Export", "Bars:", initialvalue=4, minvalue=1)
        if not bars:
            return
        self.export_sequence(filename, bars)

    def export_sequence(self, filename, bars):
        from pydub import AudioSegment
        try:
            bpm = int(self.bpm_entry.get())
            if bpm <= 0:
                raise ValueError
        except ValueError:
            print("Invalid BPM")
            return
        beat_duration_ms = float(60000 / bpm / 2)
        total_duration = int(beat_duration_ms * STEPS)
        loop = AudioSegment.silent(duration=total_duration)
        for row in self.track_rows:
            if row.is_piano_roll or row.mute_var.get():
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

