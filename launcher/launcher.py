"""Pacman AI Arena — a standalone Tk desktop launcher."""

import argparse
import os
import queue
import signal
import subprocess
import sys
import threading
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox, ttk
from pathlib import Path

from launcher_core import (
    DIFFICULTIES,
    MODE_MULTI,
    MODE_RL,
    MODE_SEARCH,
    MODES,
    LaunchConfig,
    algorithms_for,
    build_launch_spec,
    difficulty_profile,
    layouts_for,
)


COLORS = {
    "bg": "#07111f",
    "panel": "#0e1b2d",
    "panel2": "#13243a",
    "border": "#203957",
    "text": "#edf6ff",
    "muted": "#89a1bb",
    "yellow": "#ffd447",
    "cyan": "#38d9ff",
    "pink": "#ff5d8f",
    "green": "#44e5a2",
    "red": "#ff647c",
}

FONT_CANDIDATES = (
    "Noto Sans CJK SC",
    "WenQuanYi Micro Hei",
    "Microsoft YaHei",
    "SimHei",
    "Droid Sans Fallback",
)
MONO_FONT_CANDIDATES = (
    "Noto Sans Mono CJK SC",
    "WenQuanYi Micro Hei Mono",
    "Noto Sans CJK SC",
)

GHOST_LABELS = {
    "随机移动（简单）": "RandomGhost",
    "主动追踪（困难）": "DirectionalGhost",
}
GHOST_NAMES = {value: key for key, value in GHOST_LABELS.items()}

LAYOUT_NAMES = {
    "smallClassic": "小型经典（smallClassic）",
    "mediumClassic": "中型经典（mediumClassic）",
    "trickyClassic": "复杂经典（trickyClassic）",
    "contestClassic": "竞赛地图（contestClassic）",
    "capsuleClassic": "能量豆地图（capsuleClassic）",
    "openClassic": "开放地图（openClassic）",
    "originalClassic": "原版经典（originalClassic）",
    "powerClassic": "强化地图（powerClassic）",
    "tinyMaze": "微型迷宫（tinyMaze）",
    "smallMaze": "小型迷宫（smallMaze）",
    "mediumMaze": "中型迷宫（mediumMaze）",
    "bigMaze": "大型迷宫（bigMaze）",
    "openMaze": "开放迷宫（openMaze）",
    "tinyCorners": "微型四角（tinyCorners）",
    "mediumCorners": "中型四角（mediumCorners）",
    "bigCorners": "大型四角（bigCorners）",
    "smallSearch": "小型全食物（smallSearch）",
    "mediumSearch": "中型全食物（mediumSearch）",
    "bigSearch": "大型全食物（bigSearch）",
    "trickySearch": "复杂搜索（trickySearch）",
    "smallGrid": "小型训练场（smallGrid）",
    "mediumGrid": "中型训练场（mediumGrid）",
}
LAYOUT_IDS = {value: key for key, value in LAYOUT_NAMES.items()}


class PacmanLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Pacman AI Arena")
        self.geometry("1120x760")
        self.minsize(980, 690)
        self.configure(bg=COLORS["bg"])
        self.process = None
        self.game_python = os.environ.get(
            "PACMAN_GAME_PYTHON", sys.executable
        )
        self.output_queue = queue.Queue()
        self._difficulty_buttons = {}
        self._configure_fonts()
        self._build_style()
        self._build_ui()
        self._set_mode(MODE_MULTI)
        self._apply_difficulty("标准")
        self.after(100, self._drain_output)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configure_fonts(self):
        available = set(tkfont.families(self))
        self.ui_family = next(
            (name for name in FONT_CANDIDATES if name in available),
            "TkDefaultFont",
        )
        self.mono_family = next(
            (name for name in MONO_FONT_CANDIDATES if name in available),
            self.ui_family,
        )
        for font_name in (
            "TkDefaultFont", "TkTextFont", "TkMenuFont",
            "TkHeadingFont", "TkCaptionFont", "TkSmallCaptionFont",
            "TkIconFont", "TkTooltipFont",
        ):
            try:
                tkfont.nametofont(font_name).configure(
                    family=self.ui_family
                )
            except tk.TclError:
                pass
        self.option_add("*Font", (self.ui_family, 10))
        self.option_add(
            "*TCombobox*Listbox.font", (self.ui_family, 10)
        )
        self.option_add("*Menu.font", (self.ui_family, 10))

    def _font(self, size, bold=False, mono=False):
        return (
            self.mono_family if mono else self.ui_family,
            size,
            "bold" if bold else "normal",
        )

    def _build_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Arena.TCombobox",
            fieldbackground=COLORS["panel2"],
            background=COLORS["panel2"],
            foreground=COLORS["text"],
            arrowcolor=COLORS["cyan"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["border"],
            darkcolor=COLORS["border"],
            padding=8,
            font=self._font(10),
        )
        style.map(
            "Arena.TCombobox",
            fieldbackground=[("readonly", COLORS["panel2"])],
            foreground=[("readonly", COLORS["text"])],
            selectbackground=[("readonly", COLORS["panel2"])],
            selectforeground=[("readonly", COLORS["text"])],
        )
        style.configure(
            "Arena.TSpinbox",
            fieldbackground=COLORS["panel2"],
            foreground=COLORS["text"],
            arrowcolor=COLORS["cyan"],
            bordercolor=COLORS["border"],
            padding=7,
            font=self._font(10),
        )
        style.configure(
            "Arena.Horizontal.TScale",
            background=COLORS["panel"],
            troughcolor=COLORS["panel2"],
            bordercolor=COLORS["panel"],
            lightcolor=COLORS["cyan"],
            darkcolor=COLORS["cyan"],
        )

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_header()

        body = tk.Frame(self, bg=COLORS["bg"])
        body.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 18))
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        self.controls = self._card(body)
        self.controls.grid(row=0, column=0, sticky="nsew", padx=(0, 9))
        self.preview = self._card(body)
        self.preview.grid(row=0, column=1, sticky="nsew", padx=(9, 0))
        self._build_controls()
        self._build_preview()

    def _build_header(self):
        header = tk.Frame(self, bg=COLORS["bg"], height=116)
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(18, 14))
        header.grid_columnconfigure(1, weight=1)

        logo = tk.Canvas(
            header, width=76, height=76, bg=COLORS["bg"],
            highlightthickness=0
        )
        logo.grid(row=0, column=0, rowspan=2, padx=(0, 18))
        logo.create_arc(
            7, 7, 69, 69, start=38, extent=284,
            fill=COLORS["yellow"], outline=""
        )
        logo.create_oval(39, 18, 46, 25, fill=COLORS["bg"], outline="")
        for x, color in ((8, COLORS["pink"]), (31, COLORS["cyan"]),
                         (54, COLORS["green"])):
            logo.create_oval(x, 65, x + 8, 73, fill=color, outline="")

        tk.Label(
            header, text="吃豆人 AI 综合演示平台", bg=COLORS["bg"],
            fg=COLORS["text"], font=self._font(25, bold=True)
        ).grid(row=0, column=1, sticky="sw")
        tk.Label(
            header,
            text="搜索 · 博弈 · 强化学习 — 在一个控制台中启动",
            bg=COLORS["bg"], fg=COLORS["muted"],
            font=self._font(11)
        ).grid(row=1, column=1, sticky="nw", pady=(4, 0))

        self.status_pill = tk.Label(
            header, text="●  准备就绪", bg="#12352f", fg=COLORS["green"],
            padx=14, pady=8, font=self._font(10, bold=True)
        )
        self.status_pill.grid(row=0, column=2, rowspan=2, sticky="e")

    def _card(self, parent):
        return tk.Frame(
            parent, bg=COLORS["panel"],
            highlightbackground=COLORS["border"], highlightthickness=1,
        )

    def _section_title(self, parent, text, row):
        label = tk.Label(
            parent, text=text.upper(), bg=COLORS["panel"],
            fg=COLORS["cyan"], font=self._font(9, bold=True)
        )
        label.grid(row=row, column=0, columnspan=4, sticky="w", pady=(4, 9))

    def _field_label(self, parent, text, row, column):
        tk.Label(
            parent, text=text, bg=COLORS["panel"], fg=COLORS["muted"],
            font=self._font(9)
        ).grid(row=row, column=column, sticky="w", pady=(0, 5))

    def _build_controls(self):
        frame = self.controls
        frame.configure(padx=24, pady=20)
        for column in range(4):
            frame.grid_columnconfigure(column, weight=1)

        self._section_title(frame, "01 选择游戏模式", 0)
        self.mode_var = tk.StringVar()
        self.mode_combo = ttk.Combobox(
            frame, textvariable=self.mode_var, values=MODES,
            state="readonly", style="Arena.TCombobox"
        )
        self.mode_combo.grid(
            row=1, column=0, columnspan=4, sticky="ew", pady=(0, 15)
        )
        self.mode_combo.bind(
            "<<ComboboxSelected>>",
            lambda _event: self._set_mode(self.mode_var.get())
        )

        self._section_title(frame, "02 难度分级", 2)
        self.difficulty_var = tk.StringVar(value="标准")
        difficulty_row = tk.Frame(frame, bg=COLORS["panel"])
        difficulty_row.grid(
            row=3, column=0, columnspan=4, sticky="ew", pady=(0, 16)
        )
        for index, level in enumerate(DIFFICULTIES):
            difficulty_row.grid_columnconfigure(index, weight=1)
            button = tk.Button(
                difficulty_row, text=level, relief="flat", bd=0,
                cursor="hand2", command=lambda item=level:
                self._apply_difficulty(item),
                font=self._font(10, bold=True), pady=9,
            )
            button.grid(
                row=0, column=index, sticky="ew",
                padx=(0 if index == 0 else 4, 0)
            )
            self._difficulty_buttons[level] = button

        self._section_title(frame, "03 智能体与地图", 4)
        self._field_label(frame, "智能体 / 搜索方式", 5, 0)
        self._field_label(frame, "地图", 5, 2)
        self.algorithm_var = tk.StringVar()
        self.algorithm_combo = ttk.Combobox(
            frame, textvariable=self.algorithm_var, state="readonly",
            style="Arena.TCombobox"
        )
        self.algorithm_combo.grid(
            row=6, column=0, columnspan=2, sticky="ew", padx=(0, 8)
        )
        self.layout_var = tk.StringVar()
        self.layout_combo = ttk.Combobox(
            frame, textvariable=self.layout_var, state="readonly",
            style="Arena.TCombobox"
        )
        self.layout_combo.grid(
            row=6, column=2, columnspan=2, sticky="ew", padx=(8, 0)
        )

        self._field_label(frame, "幽灵行为", 7, 0)
        self._field_label(frame, "幽灵数量", 7, 2)
        self.ghost_var = tk.StringVar(
            value=GHOST_NAMES["DirectionalGhost"]
        )
        self.ghost_combo = ttk.Combobox(
            frame, textvariable=self.ghost_var,
            values=tuple(GHOST_LABELS),
            state="readonly", style="Arena.TCombobox"
        )
        self.ghost_combo.grid(
            row=8, column=0, columnspan=2, sticky="ew",
            padx=(0, 8), pady=(0, 13)
        )
        self.ghosts_var = tk.IntVar(value=2)
        self.ghosts_spin = ttk.Spinbox(
            frame, from_=0, to=4, textvariable=self.ghosts_var,
            style="Arena.TSpinbox"
        )
        self.ghosts_spin.grid(
            row=8, column=2, columnspan=2, sticky="ew",
            padx=(8, 0), pady=(0, 13)
        )

        self._section_title(frame, "04 高级参数", 9)
        self._field_label(frame, "搜索深度", 10, 0)
        self._field_label(frame, "展示局数", 10, 1)
        self._field_label(frame, "训练局数", 10, 2)
        self._field_label(frame, "动画间隔", 10, 3)

        self.depth_var = tk.IntVar(value=2)
        self.games_var = tk.IntVar(value=1)
        self.training_var = tk.IntVar(value=500)
        self.speed_var = tk.DoubleVar(value=0.07)
        self.depth_spin = ttk.Spinbox(
            frame, from_=1, to=5, textvariable=self.depth_var,
            width=7, style="Arena.TSpinbox"
        )
        self.games_spin = ttk.Spinbox(
            frame, from_=1, to=100, textvariable=self.games_var,
            width=7, style="Arena.TSpinbox"
        )
        self.training_spin = ttk.Spinbox(
            frame, from_=0, to=100000, increment=100,
            textvariable=self.training_var, width=9,
            style="Arena.TSpinbox"
        )
        self.speed_spin = ttk.Spinbox(
            frame, from_=0, to=1, increment=0.01,
            textvariable=self.speed_var, width=8,
            style="Arena.TSpinbox"
        )
        for column, widget in enumerate((
            self.depth_spin, self.games_spin,
            self.training_spin, self.speed_spin
        )):
            widget.grid(
                row=11, column=column, sticky="ew",
                padx=(0 if column == 0 else 5, 0 if column == 3 else 5)
            )

        self.fixed_seed_var = tk.BooleanVar(value=False)
        self.fixed_seed = tk.Checkbutton(
            frame, text="固定随机种子（便于公平对比）",
            variable=self.fixed_seed_var, bg=COLORS["panel"],
            fg=COLORS["muted"], activebackground=COLORS["panel"],
            activeforeground=COLORS["text"], selectcolor=COLORS["panel2"],
            font=self._font(9)
        )
        self.fixed_seed.grid(
            row=12, column=0, columnspan=4, sticky="w", pady=(13, 0)
        )

        watched = (
            self.algorithm_var, self.layout_var, self.ghost_var,
            self.ghosts_var, self.depth_var, self.games_var,
            self.training_var, self.speed_var, self.fixed_seed_var,
        )
        for variable in watched:
            variable.trace_add("write", lambda *_args: self._update_preview())

    def _build_preview(self):
        frame = self.preview
        frame.configure(padx=22, pady=20)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(3, weight=1)

        tk.Label(
            frame, text="当前游戏配置", bg=COLORS["panel"],
            fg=COLORS["pink"], font=self._font(9, bold=True)
        ).grid(row=0, column=0, sticky="w")
        self.summary_label = tk.Label(
            frame, text="", justify="left", wraplength=360,
            bg=COLORS["panel"], fg=COLORS["text"],
            font=self._font(15, bold=True)
        )
        self.summary_label.grid(row=1, column=0, sticky="ew", pady=(9, 16))

        self.command_box = tk.Text(
            frame, height=5, wrap="word", bg="#081422", fg=COLORS["cyan"],
            insertbackground=COLORS["cyan"], relief="flat", padx=12, pady=12,
            font=self._font(9, mono=True)
        )
        self.command_box.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        self.command_box.configure(state="disabled")

        log_frame = tk.Frame(
            frame, bg="#06101c", highlightbackground=COLORS["border"],
            highlightthickness=1
        )
        log_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 15))
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)
        tk.Label(
            log_frame, text="  实时运行日志", bg="#06101c",
            fg=COLORS["muted"], font=self._font(8, bold=True)
        ).grid(row=0, column=0, sticky="w", pady=7)
        self.log = tk.Text(
            log_frame, wrap="word", bg="#06101c", fg="#b8c9db",
            relief="flat", padx=10, pady=5,
            font=self._font(8, mono=True),
            state="disabled"
        )
        self.log.grid(row=1, column=0, sticky="nsew")

        actions = tk.Frame(frame, bg=COLORS["panel"])
        actions.grid(row=4, column=0, sticky="ew")
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=1)
        self.launch_button = tk.Button(
            actions, text="▶  启动游戏", command=self._launch,
            bg=COLORS["yellow"], fg="#172033", activebackground="#ffe16f",
            activeforeground="#172033", relief="flat", bd=0,
            cursor="hand2", pady=12, font=self._font(11, bold=True)
        )
        self.launch_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.stop_button = tk.Button(
            actions, text="■  终止", command=self._stop,
            bg=COLORS["panel2"], fg=COLORS["muted"],
            activebackground=COLORS["red"], activeforeground=COLORS["text"],
            relief="flat", bd=0, cursor="hand2", pady=12,
            font=self._font(11, bold=True), state="disabled"
        )
        self.stop_button.grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def _set_mode(self, mode):
        self.mode_var.set(mode)
        algorithms = algorithms_for(mode)
        layouts = [
            LAYOUT_NAMES.get(layout_id, layout_id)
            for layout_id in layouts_for(mode)
        ]
        self.algorithm_combo.configure(values=algorithms)
        self.layout_combo.configure(values=layouts)
        self.algorithm_var.set(algorithms[0])
        if mode == MODE_SEARCH:
            self.ghost_combo.configure(state="disabled")
            self.ghosts_spin.configure(state="disabled")
            self.depth_spin.configure(state="disabled")
            self.games_spin.configure(state="disabled")
            self.training_spin.configure(state="disabled")
        elif mode == MODE_RL:
            self.ghost_combo.configure(state="readonly")
            self.ghosts_spin.configure(state="normal")
            self.depth_spin.configure(state="disabled")
            self.games_spin.configure(state="normal")
            self.training_spin.configure(state="normal")
        else:
            self.ghost_combo.configure(state="readonly")
            self.ghosts_spin.configure(state="normal")
            self.depth_spin.configure(state="normal")
            self.games_spin.configure(state="normal")
            self.training_spin.configure(state="disabled")
        self._apply_difficulty(self.difficulty_var.get())

    def _apply_difficulty(self, level):
        self.difficulty_var.set(level)
        for name, button in self._difficulty_buttons.items():
            selected = name == level
            button.configure(
                bg=COLORS["cyan"] if selected else COLORS["panel2"],
                fg="#081422" if selected else COLORS["muted"],
                activebackground=COLORS["cyan"] if selected
                else COLORS["border"],
            )
        if not self.mode_var.get():
            return
        profile = difficulty_profile(level, self.mode_var.get())
        self.layout_var.set(
            LAYOUT_NAMES.get(profile["layout"], profile["layout"])
        )
        self.ghost_var.set(
            GHOST_NAMES.get(profile["ghost"], profile["ghost"])
        )
        self.ghosts_var.set(profile["ghosts"])
        self.depth_var.set(profile["depth"])
        self.training_var.set(profile["training"])
        self.speed_var.set(profile["speed"])
        self._update_preview()

    def _current_spec(self):
        config = LaunchConfig(
            mode=self.mode_var.get(),
            algorithm=self.algorithm_var.get(),
            layout=LAYOUT_IDS.get(
                self.layout_var.get(), self.layout_var.get()
            ),
            ghost=GHOST_LABELS.get(
                self.ghost_var.get(), self.ghost_var.get()
            ),
            ghosts=int(self.ghosts_var.get()),
            depth=int(self.depth_var.get()),
            games=int(self.games_var.get()),
            training=int(self.training_var.get()),
            speed=float(self.speed_var.get()),
            fixed_seed=bool(self.fixed_seed_var.get()),
        )
        return build_launch_spec(
            config, python_executable=self.game_python
        )

    def _update_preview(self):
        if not hasattr(self, "command_box") or not self.algorithm_var.get():
            return
        try:
            spec = self._current_spec()
            self.summary_label.configure(
                text="{} · {}\n地图：{}　难度：{}".format(
                    self.mode_var.get(),
                    self.algorithm_var.get(),
                    self.layout_var.get(),
                    self.difficulty_var.get(),
                )
            )
            command = spec.display_command
        except (ValueError, tk.TclError) as error:
            self.summary_label.configure(text="请检查参数")
            command = str(error)
        self.command_box.configure(state="normal")
        self.command_box.delete("1.0", "end")
        self.command_box.insert("1.0", command)
        self.command_box.configure(state="disabled")

    def _launch(self):
        if self.process and self.process.poll() is None:
            messagebox.showinfo("游戏正在运行", "请先结束当前游戏。")
            return
        try:
            spec = self._current_spec()
        except (ValueError, tk.TclError) as error:
            messagebox.showerror("参数无效", str(error))
            return

        self._append_log("\n$ " + spec.display_command + "\n")
        environment = os.environ.copy()
        environment["PYTHONUNBUFFERED"] = "1"
        try:
            self.process = subprocess.Popen(
                spec.command,
                cwd=str(spec.cwd),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=environment,
                start_new_session=True,
            )
        except OSError as error:
            messagebox.showerror("启动失败", str(error))
            self._set_running(False)
            return

        self._set_running(True)
        threading.Thread(
            target=self._read_process, daemon=True
        ).start()

    def _read_process(self):
        process = self.process
        if process.stdout:
            for line in process.stdout:
                self.output_queue.put(("line", line))
        return_code = process.wait()
        self.output_queue.put(("done", return_code))

    def _drain_output(self):
        try:
            while True:
                kind, payload = self.output_queue.get_nowait()
                if kind == "line":
                    self._append_log(payload)
                else:
                    self._append_log(
                        "\n[游戏结束，退出码 {}]\n".format(payload)
                    )
                    self._set_running(False)
        except queue.Empty:
            pass
        self.after(100, self._drain_output)

    def _append_log(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _set_running(self, running):
        self.launch_button.configure(
            state="disabled" if running else "normal"
        )
        self.stop_button.configure(
            state="normal" if running else "disabled"
        )
        if running:
            self.status_pill.configure(
                text="●  游戏运行中", bg="#173449", fg=COLORS["cyan"]
            )
        else:
            self.status_pill.configure(
                text="●  准备就绪", bg="#12352f", fg=COLORS["green"]
            )

    def _stop(self):
        if not self.process or self.process.poll() is not None:
            return
        try:
            os.killpg(self.process.pid, signal.SIGTERM)
        except (OSError, AttributeError):
            self.process.terminate()
        self._append_log("\n[已请求终止游戏]\n")

    def _on_close(self):
        if self.process and self.process.poll() is None:
            if not messagebox.askyesno(
                "退出 Pacman AI Arena", "游戏仍在运行，确定终止并退出吗？"
            ):
                return
            self._stop()
        self.destroy()


def _ensure_chinese_capable_tk():
    """
    Conda's Linux Tk build may only expose legacy X11 fonts.

    If that happens, transparently reopen the launcher with the system Tk,
    which can see fontconfig's CJK fonts. The originally selected Python is
    retained for child Pacman processes, so Conda dependencies still work.
    """
    if (not sys.platform.startswith("linux")
            or os.environ.get("PACMAN_LAUNCHER_REEXEC") == "1"):
        return

    probe = tk.Tk()
    probe.withdraw()
    available = set(tkfont.families(probe))
    probe.destroy()
    if any(name in available for name in FONT_CANDIDATES):
        return

    system_python = Path("/usr/bin/python3")
    if not system_python.exists():
        return
    environment = os.environ.copy()
    environment["PACMAN_LAUNCHER_REEXEC"] = "1"
    environment["PACMAN_GAME_PYTHON"] = sys.executable
    os.execve(
        str(system_python),
        [str(system_python), str(Path(__file__).resolve())] + sys.argv[1:],
        environment,
    )


def main():
    _ensure_chinese_capable_tk()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true",
        help="validate the default setup without opening a window"
    )
    args = parser.parse_args()
    if args.dry_run:
        profile = difficulty_profile("标准", MODE_MULTI)
        spec = build_launch_spec(
            LaunchConfig(
                mode=MODE_MULTI,
                algorithm=algorithms_for(MODE_MULTI)[0],
                layout=profile["layout"],
                ghost=profile["ghost"],
                ghosts=profile["ghosts"],
                depth=profile["depth"],
                speed=profile["speed"],
            ),
            python_executable=os.environ.get(
                "PACMAN_GAME_PYTHON", sys.executable
            ),
        )
        print(spec.display_command)
        return
    PacmanLauncher().mainloop()


if __name__ == "__main__":
    main()
