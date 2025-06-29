import tkinter as tk

class DraggablePanel(tk.Frame):
    def __init__(
        self, parent, title="Panel",
        x=50, y=50, width=400, height=300,
        min_width=200, min_height=100, **kwargs
    ):
        super().__init__(
            parent,
            bg="#222",
            bd=0,
            highlightbackground="#555",  # subtle border
            highlightcolor="#888",
            highlightthickness=2,
            relief="ridge",
            **kwargs
        )
        # Store placement info for minimize/restore
        self._last_place_info = {"x": x, "y": y, "width": width, "height": height}

        self.place(x=x, y=y, width=width, height=height)

        self.min_width = min_width
        self.min_height = min_height

        # -- Drag state --
        self._drag_start_x = 0
        self._drag_start_y = 0

        # -- Resize state --
        self._resize_dir = None
        self._resize_start_x = 0
        self._resize_start_y = 0
        self._orig_width = width
        self._orig_height = height

        # --- Header (move area) ---
        self.header = tk.Frame(self, bg="#292929", height=28)
        self.header.pack(fill="x", side="top")
        self.header.pack_propagate(False)

        self.title_label = tk.Label(
            self.header, text=title, bg="#292929", fg="white",
            font=("Segoe UI", 10, "bold"), padx=12, pady=2, anchor="w"
        )
        self.title_label.pack(side="left")

        # Minimize button
        self.minimize_btn = tk.Button(
            self.header, text="_", command=self.hide_panel,
            bg="#292929", fg="#bbb", bd=0, padx=7, pady=0,
            font=("Segoe UI", 11, "bold"), activebackground="#222", relief="flat"
        )
        self.minimize_btn.pack(side="right")

        # Drag events (header only)
        self.header.bind("<ButtonPress-1>", self.start_move)
        self.header.bind("<B1-Motion>", self.do_move)
        self.header.configure(cursor="fleur")

        # --- Main area ---
        self.body = tk.Frame(self, bg="#232323")
        self.body.pack(fill="both", expand=True)

        # --- Resize edges/corner ---
        edge_thickness = 7

        # Right edge
        self.edge_e = tk.Frame(self, bg="#222", cursor="sb_h_double_arrow", width=edge_thickness)
        self.edge_e.place(relx=1.0, rely=0, anchor="ne", relheight=1.0, y=self.header.winfo_reqheight())
        self.edge_e.bind("<ButtonPress-1>", lambda e: self.start_resize(e, "e"))
        self.edge_e.bind("<B1-Motion>", lambda e: self.do_resize(e, "e"))

        # Bottom edge
        self.edge_s = tk.Frame(self, bg="#222", cursor="sb_v_double_arrow", height=edge_thickness)
        self.edge_s.place(relx=0, rely=1.0, anchor="sw", relwidth=1.0)
        self.edge_s.bind("<ButtonPress-1>", lambda e: self.start_resize(e, "s"))
        self.edge_s.bind("<B1-Motion>", lambda e: self.do_resize(e, "s"))

        # Corner (bottom right)
        self.corner_se = tk.Frame(self, bg="#292929", cursor="bottom_right_corner",
                                 width=edge_thickness+2, height=edge_thickness+2)
        self.corner_se.place(relx=1.0, rely=1.0, anchor="se")
        self.corner_se.bind("<ButtonPress-1>", lambda e: self.start_resize(e, "se"))
        self.corner_se.bind("<B1-Motion>", lambda e: self.do_resize(e, "se"))

        # Keep resize handles correct when panel size changes
        self.bind("<Configure>", self._on_configure)

    def _on_configure(self, event=None):
        header_height = self.header.winfo_height() or 28
        self.edge_e.place(relx=1.0, rely=0, anchor="ne", relheight=1.0, y=header_height)
        self.edge_s.place(relx=0, rely=1.0, anchor="sw", relwidth=1.0)
        self.corner_se.place(relx=1.0, rely=1.0, anchor="se")
        # Update geometry for restore
        self._last_place_info = {
            "x": self.winfo_x(),
            "y": self.winfo_y(),
            "width": self.winfo_width(),
            "height": self.winfo_height(),
        }

    # --- Moving logic ---
    def start_move(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def do_move(self, event):
        dx = event.x - self._drag_start_x
        dy = event.y - self._drag_start_y
        x = self.winfo_x() + dx
        y = self.winfo_y() + dy
        # Clamp to workspace
        if self.master:
            x = max(0, min(x, self.master.winfo_width() - self.winfo_width()))
            y = max(0, min(y, self.master.winfo_height() - self.winfo_height()))
        self.place(x=x, y=y)

    # --- Resizing logic ---
    def start_resize(self, event, direction):
        self._resize_dir = direction
        self._resize_start_x = event.x_root
        self._resize_start_y = event.y_root
        self._orig_width = self.winfo_width()
        self._orig_height = self.winfo_height()
        self._orig_x = self.winfo_x()
        self._orig_y = self.winfo_y()

    def do_resize(self, event, direction):
        dx = event.x_root - self._resize_start_x
        dy = event.y_root - self._resize_start_y

        new_width = self._orig_width
        new_height = self._orig_height

        if direction == "e":
            new_width = max(self.min_width, self._orig_width + dx)
        elif direction == "s":
            new_height = max(self.min_height, self._orig_height + dy)
        elif direction == "se":
            new_width = max(self.min_width, self._orig_width + dx)
            new_height = max(self.min_height, self._orig_height + dy)

        self.place(width=new_width, height=new_height)

    # --- Minimize / Restore ---
    def hide_panel(self):
        """Minimize: Hide the panel from view (without destroying)."""
        self.place_forget()

    def restore_panel(self):
        """Restore: Show the panel again at its last location/size."""
        info = getattr(self, "_last_place_info", None)
        if info:
            self.place(**info)
        else:
            self.place(x=50, y=50, width=400, height=300)
