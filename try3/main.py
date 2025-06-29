# main.py
import tkinter as tk
from sequencer import SequencerApp
from draggable_panel import DraggablePanel

def main():
    root = tk.Tk()
    root.title("Custom DAW Workspace")
    root.geometry("1920x1080")
    root.configure(bg="#18191b")

    seq_panel = DraggablePanel(
        root, title="Sequencer",
        x=60, y=50, width=1800, height=210,
        min_width=900, min_height=120,
    )
    seq_app = SequencerApp(root, seq_panel.body, cell_width=20, cell_height=20)
    root.mainloop()

if __name__ == "__main__":
    main()
