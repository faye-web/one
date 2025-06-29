import tkinter as tk

class PianoRollCanvas(tk.Canvas):
    def __init__(self, master, steps=64, notes=24, cell_width=26, cell_height=40, sidebar_width=140, beat_offset=8):
        self.steps = steps
        self.notes = notes
        self.cell_width = cell_width
        self.cell_height = cell_height
        self.sidebar_width = sidebar_width + beat_offset * cell_width  # Shift entire roll right
        self.beat_offset = beat_offset

        total_width = self.sidebar_width + steps * cell_width
        total_height = notes * cell_height

        super().__init__(master, width=total_width, height=total_height, bg="white")

        self.notes_list = []  # List of dicts: {'row': int, 'start': int, 'end': int}
        self.drag_start = None
        self.drag_note = None

        self.bind("<Button-1>", self.handle_left_click)
        self.bind("<B1-Motion>", self.handle_drag_motion)
        self.bind("<ButtonRelease-1>", self.handle_drag_release)
        self.bind("<Button-3>", self.handle_right_click)

        self.draw_grid()

    def draw_grid(self):
        self.delete("all")
        for row in range(self.notes):
            y1 = row * self.cell_height
            y2 = y1 + self.cell_height

            # Draw piano key background and labels
            self.create_rectangle(0, y1, self.sidebar_width, y2, fill="lightgray" if self.is_minor_key(row) else "white", outline="black")
            self.create_text(self.sidebar_width // 2, y1 + self.cell_height // 2, text=self.note_name(row), anchor="center")

            for col in range(self.steps):
                x1 = self.sidebar_width + col * self.cell_width
                x2 = x1 + self.cell_width
                base_color = "white" if self.is_minor_key(row) else "lightgray"
                if (col // 4) % 2 == 1:
                    base_color = "lightgray" if base_color == "white" else "white"
                self.create_rectangle(x1, y1, x2, y2, fill=base_color, outline="black")

        for note in self.notes_list:
            y1 = note['row'] * self.cell_height
            y2 = y1 + self.cell_height
            x1 = self.sidebar_width + note['start'] * self.cell_width
            x2 = self.sidebar_width + (note['end'] + 1) * self.cell_width
            self.create_rectangle(x1, y1, x2, y2, fill="green", outline="black")

    def is_minor_key(self, row):
        pitch_class = (self.notes - 1 - row) % 12
        return pitch_class in [1, 3, 6, 8, 10]  # C#, D#, F#, G#, A#

    def note_name(self, row):
        pitch_classes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        pitch_class = (self.notes - 1 - row) % 12
        octave = (self.notes - 1 - row) // 12 + 3  # Starting from octave 3
        return f"{pitch_classes[pitch_class]}{octave}"

    def find_note_at(self, row, col):
        for note in self.notes_list:
            if note['row'] == row and note['start'] <= col <= note['end']:
                return note
        return None

    def has_overlap(self, row, start, end, exclude_note=None):
        for note in self.notes_list:
            if note is exclude_note:
                continue
            if note['row'] == row and not (end < note['start'] or start > note['end']):
                return True
        return False

    def handle_left_click(self, event):
        col = (event.x - self.sidebar_width) // self.cell_width
        row = event.y // self.cell_height
        if 0 <= row < self.notes and 0 <= col < self.steps:
            existing_note = self.find_note_at(row, col)
            if existing_note:
                self.drag_note = existing_note
                self.drag_start = (row, col)
            else:
                if not self.has_overlap(row, col, col):
                    new_note = {'row': row, 'start': col, 'end': col}
                    self.notes_list.append(new_note)
                    self.drag_note = new_note
                    self.drag_start = (row, col)
            self.draw_grid()

    def handle_drag_motion(self, event):
        if self.drag_note and self.drag_start:
            row, original_col = self.drag_start
            col_now = (event.x - self.sidebar_width) // self.cell_width
            col_now = max(0, min(col_now, self.steps - 1))

            if col_now < self.drag_note['start']:
                if not self.has_overlap(row, col_now, self.drag_note['start'] - 1, exclude_note=self.drag_note):
                    self.drag_note['start'] = col_now
            elif col_now > self.drag_note['end']:
                if not self.has_overlap(row, self.drag_note['end'] + 1, col_now, exclude_note=self.drag_note):
                    self.drag_note['end'] = col_now
            elif col_now < original_col:
                if not self.has_overlap(row, col_now, self.drag_note['end'] - 1, exclude_note=self.drag_note):
                    self.drag_note['start'] = col_now
            elif col_now > original_col:
                if not self.has_overlap(row, self.drag_note['start'] + 1, col_now, exclude_note=self.drag_note):
                    self.drag_note['end'] = col_now

            self.draw_grid()

    def handle_drag_release(self, event):
        self.drag_start = None
        self.drag_note = None

    def handle_right_click(self, event):
        col = (event.x - self.sidebar_width) // self.cell_width
        row = event.y // self.cell_height
        if 0 <= row < self.notes and 0 <= col < self.steps:
            self.notes_list = [note for note in self.notes_list if not (note['row'] == row and note['start'] <= col <= note['end'])]
            self.draw_grid()