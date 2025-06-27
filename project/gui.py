import tkinter as tk
from .settings import TRACKS, STEPS, DEFAULT_BPM
from .playback import play_sequence

def run_gui():
    # ==== GUI STATE ====
    grid = [[0 for _ in range(STEPS)] for _ in range(len(TRACKS))]
    buttons = [[None for _ in range(STEPS)] for _ in range(len(TRACKS))]
    selected_samples = [tk.StringVar() for _ in range(len(TRACKS))]

    # ==== TOGGLE CELL FUNCTION ====
    def toggle_cell(row, col):
        grid[row][col] = 1 - grid[row][col]
        color = "green" if grid[row][col] else ("white" if (col // 4) % 2 == 0 else "lightgray")
        buttons[row][col].configure(bg=color)

    # ==== GUI SETUP ====
    root = tk.Tk()
    root.title("Mini Step Sequencer")

    # BPM Control
    bpm_label = tk.Label(root, text="BPM:")
    bpm_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
    bpm_entry = tk.Entry(root, width=5)
    bpm_entry.insert(0, str(DEFAULT_BPM))
    bpm_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    # Track Rows
    for row, track in enumerate(TRACKS):
        row_offset = row + 1

        label = tk.Label(root, text=track["name"], width=6, anchor="e")
        label.grid(row=row_offset, column=0, padx=5, pady=2)

        selected_samples[row].set(track["options"][0])
        dropdown = tk.OptionMenu(root, selected_samples[row], *track["options"])
        dropdown.grid(row=row_offset, column=1, padx=5)

        frame = tk.Frame(root)
        frame.grid(row=row_offset, column=2, columnspan=STEPS)
        for col in range(STEPS):
            base_color = "white" if (col // 4) % 2 == 0 else "lightgray"
            btn = tk.Button(
                frame,
                width=1,
                height=2,
                bg=base_color,
                command=lambda r=row, c=col: toggle_cell(r, c)
            )
            btn.grid(row=0, column=col, padx=1, pady=1)
            buttons[row][col] = btn

    # Export Button
    play_button = tk.Button(
        root,
        text="Export Beat",
        command=lambda: play_sequence(grid, selected_samples, int(bpm_entry.get()), TRACKS),
        bg="lightblue"
    )
    play_button.grid(row=len(TRACKS) + 2, columnspan=STEPS + 3, pady=10)

    root.mainloop()

# Optional: allow direct running
if __name__ == "__main__":
    run_gui()
