import tkinter as tk
from tkinter import ttk
import subprocess
import threading
import queue
import re

log_queue = queue.Queue()
is_downloading = False
log_visible = False
has_log_output = False
process = None


progress_pattern = re.compile(r"(\d+(?:\.\d+)?)%")

def is_valid_url(url: str) -> bool:
    return url.startswith("http") and len(url) > 10

def download():
    global is_downloading, has_log_output

    if is_downloading:
        return

    url = entry.get().strip()
    if not is_valid_url(url):
        status_label.config(text="Invalid URL", fg="red")
        return

    is_downloading = True
    has_log_output = False

    button.config(state="disabled")
    cancel_btn.config(state="normal")
    toggle_btn.config(state="disabled")
    copy_btn.config(state="disabled")
    progress['value'] = 0
    status_label.config(text="Downloading ...", fg="black")
    log.delete("1.0", "end")

    for child in preset_frame.winfo_children():
        child.config(state="disabled")

    def worker():
        global is_downloading, has_log_output, process

        cmd = ["yt-dlp", url]

        if output_mode.get() == "audio":
            cmd += ["-x", "--audio-format", "mp3"]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        log_queue.put(("log", f"[INFO] Mode: {output_mode.get()}\n"))

        assert process.stdout is not None
        for line in process.stdout:
            if not is_downloading:
                break

            has_log_output = True
            log_queue.put(("log", line))

            match = progress_pattern.search(line)

            if match:
                percent = float(match.group(1))
                log_queue.put(("progress", percent))

        exit_code = process.wait()


        if not is_downloading:
            log_queue.put(("done_cancel", None))
        elif exit_code == 0:
            log_queue.put(("done_success", None))
        else:
            log_queue.put(("done_error", None))

        is_downloading = False

    threading.Thread(target=worker, daemon=True).start()

def cancel_download():
    global process, is_downloading

    if process and is_downloading:
        is_downloading = False
        try:
            process.terminate()
        except Exception:
            pass

def update_ui():
    while not log_queue.empty():
        msg_type, value = log_queue.get()

        if msg_type == "log":
            log.insert("end", value)
            log.see("end")
            toggle_btn.config(state="normal")

            if not is_downloading:
                copy_btn.config(state="normal")


        elif msg_type == "progress":
             progress['value'] = value

        elif msg_type == "done_success":
             progress['value'] = 100
             button.config(state="normal")
             cancel_btn.config(state="disabled")
             copy_btn.config(state="normal")
             status_label.config(text="Completed", fg="green")
             log.insert("end", "Download completed successfully.\n")

             for child in preset_frame.winfo_children():
                 child.config(state="normal")


        elif msg_type == "done_cancel":
             button.config(state="normal")
             cancel_btn.config(state="disabled")
             copy_btn.config(state="normal")
             status_label.config(text="Cancelled", fg="orange")
             log.insert("end", '\nDownload Cancelled')

             for child in preset_frame.winfo_children():
                 child.config(state="normal")


        elif msg_type == "done_error":
             button.config(state="normal")
             cancel_btn.config(state="disabled")
             copy_btn.config(state="normal")
             status_label.config(text="Error occurred", fg="red")
             log.insert("end", "\nDownload failed.\n")

             for child in preset_frame.winfo_children():
                 child.config(state="normal")


    root.after(100, update_ui)

def toggle_log():
    global log_visible

    if not has_log_output:
        return

    if log_visible:
        log.pack_forget()
        toggle_btn.config(text="Show Log")
        log_visible = False
    else:
        log.pack(fill="both", expand=True, padx=10, pady=5)
        toggle_btn.config(text="Hide Log")
        log_visible = True

def copy_log():
    text = log.get("1.0", "end").strip()
    if not text:
        return
    root.clipboard_clear()
    root.clipboard_append(text)
    status_label.config(text="Log copied to clipboard", fg="blue")

root = tk.Tk()
root.title("YT-DLP GUI")
output_mode = tk.StringVar(value="video")

entry = tk.Entry(root, width=100)
entry.pack(fill="x", padx=10, pady=5)

preset_frame = tk.Frame(root)
preset_frame.pack(pady=5)

tk.Radiobutton(
    preset_frame,
    text="Video",
    variable=output_mode,
    value="video"
).pack(side="left", padx=5)

tk.Radiobutton(
    preset_frame,
    text="Audio(MP3)",
    variable=output_mode,
    value="audio"
).pack(side="left", padx=5)

button = tk.Button(
    root,
    text="Download",
    command=download
)

button.pack(pady=5)

cancel_btn = tk.Button(
    root,
    text="Cancel",
    command=lambda: cancel_download(),
    state="disabled"
)

cancel_btn.pack(pady=5)

progress = ttk.Progressbar(
    root,
    orient="horizontal",
    length=400,
    mode="determinate",
    maximum=100
)
progress.pack(padx=10, pady=5)

status_label = tk.Label(root, text="IDLE", fg="blue")
status_label.pack(pady=2)

control_frame = tk.Frame(root)
control_frame.pack(pady=5)

toggle_btn = tk.Button(
    control_frame,
    text="Show Log",
    command=toggle_log,
    state="disabled"
    )

toggle_btn.pack(side="left", padx=5)

copy_btn = tk.Button(
    control_frame,
    text="Copy Log",
    command=copy_log,
    state="disabled"
)

copy_btn.pack(side="left", padx=5)

log = tk.Text(root, height=12, width=50)

update_ui()
root.mainloop()
