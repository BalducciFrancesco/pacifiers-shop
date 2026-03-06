from __future__ import annotations

import queue
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from .downloader import DownloadRequest, run_download
from .routing import choose_tool


class MainWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.worker_thread: threading.Thread | None = None
        self.worker_running = False
        self.is_busy = False
        self.events: queue.Queue[tuple[str, str | int]] = queue.Queue()
        self.icon_image: tk.PhotoImage | None = None
        self.log_visible = False
        self.compact_height = 0
        self.log_height = 520

        self.root.title("PacifierShop")
        self.root.geometry("620x220")
        self.root.minsize(560, 120)

        self.url_var = tk.StringVar()
        self.folder_var = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.url_var.trace_add("write", self._on_url_change)
        self.quality_var = tk.StringVar(value="max")

        container = ttk.Frame(self.root, padding=(12, 12, 12, 8))
        container.grid(row=0, column=0, sticky="nsew")
        self.container = container
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(5, weight=0)

        icon_path = self._resource_path("resources", "pacifier.png")
        if icon_path.exists():
            self.icon_image = tk.PhotoImage(file=str(icon_path))
            ttk.Label(container, image=self.icon_image).grid(row=0, column=0, columnspan=2, pady=(0, 8))

        ttk.Label(container, text="Media URL").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=(0, 6))
        url_row = ttk.Frame(container)
        url_row.grid(row=1, column=1, sticky="ew", pady=(0, 6))
        url_row.columnconfigure(0, weight=1)
        self.url_input = ttk.Entry(url_row, textvariable=self.url_var)
        self.url_input.grid(row=0, column=0, sticky="ew")
        self.quality_input = ttk.Combobox(
            url_row,
            textvariable=self.quality_var,
            values=("max", "efficient"),
            state="readonly",
            width=12,
        )
        self.quality_input.grid(row=0, column=1, padx=(8, 0))

        ttk.Label(container, text="Output folder").grid(row=2, column=0, sticky="w", padx=(0, 10), pady=(0, 6))
        folder_row = ttk.Frame(container)
        folder_row.grid(row=2, column=1, sticky="ew", pady=(0, 6))
        folder_row.columnconfigure(0, weight=1)
        self.folder_input = ttk.Entry(folder_row, textvariable=self.folder_var)
        self.folder_input.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.choose_folder_btn = ttk.Button(folder_row, text="Browse...", width=12, command=self.choose_folder)
        self.choose_folder_btn.grid(row=0, column=1)

        self.download_btn = ttk.Button(container, text="make this boredom stop please", command=self.start_download)
        self.download_btn.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 4))

        self.log_toggle_btn = ttk.Button(container, text="Show Log", command=self.toggle_log_view)
        self.log_toggle_btn.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 2))

        self.log_output = ScrolledText(container, wrap="none")
        self.log_output.configure(state="disabled")
        self.log_output.grid(row=5, column=0, columnspan=2, sticky="nsew")
        self.log_output.grid_remove()

        self.progress_bar = ttk.Progressbar(self.root, mode="indeterminate", maximum=100)
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=3)
        self.progress_bar.grid_remove()
        self._update_download_btn_state()
        self.root.after_idle(self._refresh_compact_height)

    def choose_folder(self) -> None:
        current = self.folder_var.get().strip() or str(Path.home())
        folder = filedialog.askdirectory(title="Choose output folder", initialdir=current)
        if folder:
            self.folder_var.set(folder)

    def _resource_path(self, *parts: str) -> Path:
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            base = Path(getattr(sys, "_MEIPASS"))
        else:
            base = Path(__file__).resolve().parents[2]
        return base.joinpath(*parts)

    def _refresh_compact_height(self) -> None:
        if self.log_visible:
            return
        self.root.update_idletasks()
        target = max(self.container.winfo_reqheight() + 8, 120)
        self.compact_height = target
        width = max(self.root.winfo_width(), 560)
        self.root.geometry(f"{width}x{target}")
        self.root.minsize(560, target)

    def append_log(self, text: str) -> None:
        self.log_output.configure(state="normal")
        self.log_output.insert(tk.END, f"{text}\n")
        self.log_output.see(tk.END)
        self.log_output.configure(state="disabled")

    def _on_url_change(self, *_args: object) -> None:
        self._update_download_btn_state()

    def _valid_url(self, url: str) -> bool:
        if not url:
            return False
        try:
            choose_tool(url)
        except ValueError:
            return False
        return True

    def _update_download_btn_state(self) -> None:
        enabled = (not self.is_busy) and self._valid_url(self.url_var.get().strip())
        self.download_btn.configure(state="normal" if enabled else "disabled")

    def toggle_log_view(self) -> None:
        self.log_visible = not self.log_visible
        if self.log_visible:
            self.log_output.grid()
            self.log_toggle_btn.configure(text="Hide Log")
            self.log_toggle_btn.grid_configure(pady=(0, 6))
            self.container.rowconfigure(5, weight=1)
        else:
            self.log_output.grid_remove()
            self.log_toggle_btn.configure(text="Show Log")
            self.log_toggle_btn.grid_configure(pady=(0, 2))
            self.container.rowconfigure(5, weight=0)
            self._refresh_compact_height()
        width = max(self.root.winfo_width(), 560)
        target_height = self.log_height if self.log_visible else self.compact_height
        self.root.geometry(f"{width}x{target_height}")

    def _set_busy(self, busy: bool) -> None:
        self.is_busy = busy
        state = "disabled" if busy else "normal"
        self.url_input.configure(state=state)
        self.folder_input.configure(state=state)
        self.quality_input.configure(state="disabled" if busy else "readonly")
        self.choose_folder_btn.configure(state=state)
        self._update_download_btn_state()
        if busy:
            self.progress_bar.grid()
            self.progress_bar.start(40)
        else:
            self.progress_bar.stop()
            self.progress_bar.grid_remove()

    def start_download(self) -> None:
        url = self.url_var.get().strip()
        output_dir = self.folder_var.get().strip()

        if not self._valid_url(url):
            return

        if not output_dir:
            messagebox.showwarning("Missing folder", "Please choose an output folder.")
            return

        route = choose_tool(url)

        request = DownloadRequest(
            url=url,
            output_dir=Path(output_dir),
            tool=route.tool,
            quality=self.quality_var.get(),
        )
        self.append_log("=" * 72)
        self.append_log(f"Quality: {request.quality}")
        self.append_log(f"Output: {request.output_dir}")

        self._set_busy(True)
        self.worker_running = True
        self.worker_thread = threading.Thread(target=self._run_download, args=(request,), daemon=True)
        self.worker_thread.start()
        self.root.after(50, self._poll_events)

    def _run_download(self, request: DownloadRequest) -> None:
        code = run_download(request, lambda line: self.events.put(("log", line)))
        self.events.put(("done", code))

    def _poll_events(self) -> None:
        max_events_per_tick = 80
        processed = 0
        while processed < max_events_per_tick:
            try:
                kind, payload = self.events.get_nowait()
            except queue.Empty:
                break
            processed += 1

            if kind == "log":
                self.append_log(str(payload))
            elif kind == "done":
                self.on_done(int(payload))

        if self.worker_running:
            self.root.after(20, self._poll_events)

    def on_done(self, code: int) -> None:
        self.worker_running = False
        self._set_busy(False)
        if code == 0:
            self.append_log("Download finished successfully.")
            messagebox.showinfo("PacifierShop", "Download complete.")
        else:
            self.append_log(f"Download failed with exit code {code}.")
            messagebox.showerror("PacifierShop", f"Download failed (exit code {code}).")


def main() -> None:
    root = tk.Tk()
    style = ttk.Style(root)
    if sys.platform == "darwin" and "aqua" in style.theme_names():
        style.theme_use("aqua")
    MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
