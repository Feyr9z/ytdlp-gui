import tkinter as tk
import subprocess
import threading
import queue

log_queue = queue.Queue()
is_downloading =False

def download():
    global is_downloading

    if is_downloading:
        return

    url = entry.get().strip()
    if not url:
        return

    is_downloading = True
    button.config(state="disable")
    log.delete("1.0", "end")

    def worker():
        process = subprocess.Popen(
            ["yt-dlp", url],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        for line in process.stdout:
            log_queue.put(line)

        is_downloading = False
        log_queue.put("__DONE__")

    threading.Thread(target=worker, daemon=True).start()

def update_log():
    while not log_queue.empty():
        msg = log_queue.get()

        if msg == "__DONE__":
            button.config(state="normal")
            log.insert("end", "\nDownload Finish\n")
        else:
            log.insert("end", msg)

        log.see("end")

    root.after(100, update_log)


root = tk.Tk()
root.title("YT-DLP GUI")

entry = tk.Entry(root, width=50)
entry.pack(fill="x", padx=10, pady=10)

button = tk.Button(root, text="Download", command=download)
button.pack(pady=5)

log = tk.Text(root, height=15)
log.pack(fill="both", expand=True, padx=10, pady=5)

update_log()
root.mainloop()
