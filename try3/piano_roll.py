import tkinter as tk

class PianoRollCanvas(tk.Canvas):
    def __init__(self, master, steps=64, cell_width=24, cell_height=24, sidebar_width=96, beat_offset=0):
        self.steps = steps
        self.notes_total = 88  # Full piano: A0 (MIDI 21) to C8 (MIDI 108)
        self.cell_width = cell_width
        self.cell_height = cell_height
        self.sidebar_width = sidebar_width + beat_offset * cell_width
        self.beat_offset = beat_offset

        # Start at the top (C8) by default
        self.top_note = 0  # 0 = C8, 87 = A0

        # Initial size
        total_width = self.sidebar_width + steps * cell_width
        total_height = 24 * cell_height  # Initial, doesn't matter since it'll expand

        super().__init__(master, width=total_width, height=total_height, bg="#18191b", highlightthickness=0)

        self.notes_list = []
        self.drag_start = None
        self.drag_note = None
        self.drag_edge = None  # "start", "end", or None

        self.highlighted_col = None
        self._has_focus = False

        # Mousewheel bindings (cross-platform)
        self.bind("<Enter>", self._on_mouse_enter)
        self.bind("<Leave>", self._on_mouse_leave)
        self.bind("<Button-4>", self._on_linux_scroll)   # Linux scroll up
        self.bind("<Button-5>", self._on_linux_scroll)   # Linux scroll down
        self.bind_all("<MouseWheel>", self._on_mousewheel)  # Windows & Mac

        # Bind other events
        self.bind("<Button-1>", self.handle_left_click)
        self.bind("<B1-Motion>", self.handle_drag_motion)
        self.bind("<ButtonRelease-1>", self.handle_drag_release)
        self.bind("<Button-3>", self.handle_right_click)

        # Bind configure for dynamic resizing
        self.bind("<Configure>", self._on_resize)

        self.draw_grid()

    @property
    def notes_visible(self):
        # Number of notes that can fit in current canvas height
        return max(1, self.winfo_height() // self.cell_height)

    def _on_resize(self, event):
        self.draw_grid()

    def _on_mouse_enter(self, event):
        self._has_focus = True

    def _on_mouse_leave(self, event):
        self._has_focus = False

    def _on_mousewheel(self, event):
        if not self._has_focus:
            return
        if event.delta > 0:
            self.scroll_vertical(-3)
        elif event.delta < 0:
            self.scroll_vertical(3)

    def _on_linux_scroll(self, event):
        if not self._has_focus:
            return
        if event.num == 4:
            self.scroll_vertical(-3)
        elif event.num == 5:
            self.scroll_vertical(3)

    def scroll_vertical(self, delta):
        max_top = max(0, self.notes_total - self.notes_visible)
        new_top = self.top_note + delta
        if new_top < 0:
            new_top = 0
        if new_top > max_top:
            new_top = max_top
        if new_top != self.top_note:
            self.top_note = new_top
            self.draw_grid()

    def draw_grid(self):
        self.delete("all")
        notes_visible = self.notes_visible
        for vis_row in range(notes_visible):
            abs_row = self.top_note + vis_row
            if abs_row >= self.notes_total:
                continue
            y1 = vis_row * self.cell_height
            y2 = y1 + self.cell_height
            fg_piano = "#eb42e2" if self.is_row_playing(abs_row) else "#b6bdc2"
            bg_piano = "#22272c" if (abs_row % 2 == 0) else "#181a1c"
            self.create_rectangle(0, y1, self.sidebar_width, y2, fill=bg_piano, outline="#25292c")
            self.create_text(self.sidebar_width // 2, y1 + self.cell_height // 2, text=self.note_name(abs_row),
                             fill=fg_piano, font=("Segoe UI", 10, "bold"))
            for col in range(self.steps):
                x1 = self.sidebar_width + col * self.cell_width
                x2 = x1 + self.cell_width
                block_bg = "#20232b" if (col // 4) % 2 == 0 else "#23262e"
                if self.highlighted_col == col:
                    block_bg = self.mix_colors(block_bg, "#ffffff", 0.17)
                self.create_rectangle(x1, y1, x2, y2, fill=block_bg, outline="#111", width=1)
        # Gridlines
        grid_color = "#111"
        for vis_row in range(notes_visible + 1):
            y = vis_row * self.cell_height
            self.create_line(self.sidebar_width, y, self.sidebar_width + self.steps * self.cell_width, y, fill=grid_color)
        for col in range(self.steps + 1):
            x = self.sidebar_width + col * self.cell_width
            self.create_line(x, 0, x, notes_visible * self.cell_height, fill=grid_color)
        self.create_line(self.sidebar_width, 0, self.sidebar_width, notes_visible * self.cell_height, fill="#25292c")
        # Draw notes
        for note in self.notes_list:
            note_row = note['row']
            if self.top_note <= note_row < self.top_note + notes_visible:
                vis_row = note_row - self.top_note
                y1 = vis_row * self.cell_height
                y2 = y1 + self.cell_height
                x1 = self.sidebar_width + note['start'] * self.cell_width + 1
                x2 = self.sidebar_width + (note['end'] + 1) * self.cell_width - 1
                self.create_rectangle(x1, y1 + 2, x2, y2 - 2, fill="#eb42e2", outline="#222", width=2)

    def is_row_playing(self, abs_row):
        for note in self.notes_list:
            if note['row'] == abs_row:
                return True
        return False

    def note_name(self, abs_row):
        midi_note = 108 - abs_row  # 108 = C8, 21 = A0
        pitch_classes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        pitch_class = midi_note % 12
        octave = midi_note // 12 - 1
        return f"{pitch_classes[pitch_class]}{octave}"

    def find_note_at(self, abs_row, col):
        for note in self.notes_list:
            if note['row'] == abs_row and note['start'] <= col <= note['end']:
                return note
        return None

    def has_overlap(self, abs_row, start, end, exclude_note=None):
        for note in self.notes_list:
            if note is exclude_note:
                continue
            if note['row'] == abs_row and not (end < note['start'] or start > note['end']):
                return True
        return False

    def handle_left_click(self, event):
        col = (event.x - self.sidebar_width) // self.cell_width
        vis_row = event.y // self.cell_height
        abs_row = self.top_note + vis_row
        if 0 <= vis_row < self.notes_visible and 0 <= col < self.steps and 0 <= abs_row < self.notes_total:
            existing_note = self.find_note_at(abs_row, col)
            if existing_note:
                self.drag_note = existing_note
                self.drag_start = (abs_row, col)
                x1 = self.sidebar_width + self.drag_note['start'] * self.cell_width
                x2 = self.sidebar_width + (self.drag_note['end'] + 1) * self.cell_width
                click_x = event.x
                if abs(click_x - x1) < 6:
                    self.drag_edge = "start"
                elif abs(click_x - x2) < 6:
                    self.drag_edge = "end"
                else:
                    mid = (x1 + x2) / 2
                    self.drag_edge = "end" if click_x > mid else "start"
            else:
                if not self.has_overlap(abs_row, col, col):
                    new_note = {'row': abs_row, 'start': col, 'end': col}
                    self.notes_list.append(new_note)
                    self.drag_note = new_note
                    self.drag_start = (abs_row, col)
                    self.drag_edge = "end"
            self.draw_grid()

    def handle_drag_motion(self, event):
        if self.drag_note and self.drag_start and self.drag_edge:
            abs_row, original_col = self.drag_start
            col_now = (event.x - self.sidebar_width) // self.cell_width
            col_now = max(0, min(col_now, self.steps - 1))
            if self.drag_edge == "start":
                new_start = min(col_now, self.drag_note['end'])
                if not self.has_overlap(abs_row, new_start, self.drag_note['end'], exclude_note=self.drag_note):
                    self.drag_note['start'] = new_start
            elif self.drag_edge == "end":
                new_end = max(col_now, self.drag_note['start'])
                if not self.has_overlap(abs_row, self.drag_note['start'], new_end, exclude_note=self.drag_note):
                    self.drag_note['end'] = new_end
            self.draw_grid()

    def handle_drag_release(self, event):
        self.drag_start = None
        self.drag_note = None
        self.drag_edge = None

    def handle_right_click(self, event):
        col = (event.x - self.sidebar_width) // self.cell_width
        vis_row = event.y // self.cell_height
        abs_row = self.top_note + vis_row
        if 0 <= vis_row < self.notes_visible and 0 <= col < self.steps and 0 <= abs_row < self.notes_total:
            self.notes_list = [note for note in self.notes_list if not (note['row'] == abs_row and note['start'] <= col <= note['end'])]
            self.draw_grid()

    def highlight_column(self, col, highlight=True):
        if highlight:
            self.highlighted_col = col
        else:
            self.highlighted_col = None
        self.draw_grid()

    @staticmethod
    def mix_colors(color1, color2, alpha):
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip("#")
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        def rgb_to_hex(rgb):
            return "#%02x%02x%02x" % rgb
        rgb1 = hex_to_rgb(color1)
        rgb2 = hex_to_rgb(color2)
        mixed = tuple(int((1-alpha)*c1 + alpha*c2) for c1, c2 in zip(rgb1, rgb2))
        return rgb_to_hex(mixed)
