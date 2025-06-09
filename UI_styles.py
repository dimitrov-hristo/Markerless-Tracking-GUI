import tkinter as tk
import platform
import ctypes


class RoundedButton(tk.Frame):
    def __init__(self, parent, text="", command=None, state=tk.NORMAL, padding=(20, 6), radius=20, **kwargs):
        super().__init__(parent, bg=parent["bg"])

        self.command = command
        self._state = state
        self.radius = radius
        self.padding = padding

        self.bg_color = kwargs.get("bg", "#FFDB58") #"#7fdbca"
        self.active_bg = kwargs.get("activebackground", "#E6C045") #"#6cd1bb"
        self.disabled_bg = kwargs.get("disabledbackground", "#aaaaaa") #"#aaaaaa"
        self.fg_color = kwargs.get("fg", "#3f3f3f")
        self.font = kwargs.get("font", ("Segoe UI", 14, "bold"))

        # Create canvas
        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0, bg=parent["bg"])
        self.canvas.pack()

        # Text + background
        self.text_id = self.canvas.create_text(0, 0, text=text, font=self.font, fill="#3f3f3f", anchor="nw")
        self._draw_button()

        # Bindings
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Enter>", self._on_enter)
        self.canvas.bind("<Leave>", self._on_leave)

    def _draw_button(self):
        self.canvas.delete("round_rect")
        bbox = self.canvas.bbox(self.text_id)
        width = bbox[2] - bbox[0] + 2 * self.padding[0]
        height = bbox[3] - bbox[1] + 2 * self.padding[1]
        self.canvas.config(width=width, height=height)

        fill_color = self._get_bg()
        self.round_rect = self._create_round_rect(0, 0, width, height, self.radius,
                                                  fill=fill_color, outline="", tag="round_rect")
        self.canvas.tag_lower("round_rect")
        self.canvas.coords(self.text_id, self.padding[0], self.padding[1])

    def _create_round_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1 + r, y1, x2 - r, y1, x2, y1,
            x2, y1 + r, x2, y2 - r, x2, y2,
            x2 - r, y2, x1 + r, y2, x1, y2,
            x1, y2 - r, x1, y1 + r, x1, y1
        ]
        return self.canvas.create_polygon(points, smooth=True, **kwargs)

    def _get_bg(self):
        return self.bg_color if self._state == tk.NORMAL else self.disabled_bg

    def _on_click(self, event):
        if self._state == tk.NORMAL and self.command:
            self.command()

    def _on_enter(self, event):
        if self._state == tk.NORMAL:
            self.canvas.itemconfig(self.round_rect, fill=self.active_bg)

    def _on_leave(self, event):
        if self._state == tk.NORMAL:
            self.canvas.itemconfig(self.round_rect, fill=self.bg_color)

    def config(self, **kwargs):
        if "state" in kwargs:
            self._state = kwargs["state"]
            self._draw_button()
        if "text" in kwargs:
            self.canvas.itemconfig(self.text_id, text=kwargs["text"])
            self._draw_button()
        if "command" in kwargs:
            self.command = kwargs["command"]

    configure = config


def apply_button_style(button):
    button.config(
        bg="#7fdbca",
        fg="black",
        activebackground="#6cd1bb",
        activeforeground="black",
        relief="flat",
        bd=0,
        highlightthickness=0,
        padx=20,
        pady=8,
        font=("Segoe UI", 14, "bold"),
        cursor="hand2"
    )

    button.update_idletasks()
    width = button.winfo_reqwidth()
    button.config(width=width)
    button.pack(pady=10, ipadx=10, ipady=5)

def create_themed_radiobutton(parent, text, variable, value, command=None, font=("Segoe UI", 14)):
    return tk.Radiobutton(
        parent,
        text=text,
        variable=variable,
        value=value,
        command=command,
        bg="#1e1e1e",
        fg="white",
        activebackground="#1e1e1e",
        activeforeground="white",
        selectcolor="#2b2b2b",
        font=font
    )

def create_directory_selector(frame, textvariable, command, font=("Segoe UI", 14, "bold")):

    save_dir_entry = tk.Entry(
        frame, textvariable=textvariable,
        bg="#2b2b2b", fg="white", insertbackground="white",
        font=font, relief="flat",
        highlightthickness=1, highlightbackground="#444", highlightcolor="#6cd1bb"
    )

    save_dir_button = RoundedButton(
        frame,
        text="      Browse\nSaving Directory",
        command=command,
        font=font,
        padding=(12, 8)
    )

    return save_dir_entry, save_dir_button  # or return frame, entry, btn if you need access



