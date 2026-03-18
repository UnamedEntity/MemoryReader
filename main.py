import os
import tkinter as tk
from tkinter import ttk
from concurrent.futures import ThreadPoolExecutor
import threading
import ctypes
import sys

# ---------- ADMIN CHECK ----------

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def relaunch_as_admin():
    params = " ".join([f'"{arg}"' for arg in sys.argv])
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, params, None, 1
    )
    sys.exit()


class MemoryReader:
    def __init__(self, root):
        self.root = root
        self.root.title("Memory Analyzer")
        self.root.geometry("1000x650")

        self.current_path = "C:\\"
        self.executor = ThreadPoolExecutor(max_workers=6)
        self.cache = {}

        self.setup_ui()
        self.load_directories(self.current_path)

    # ---------- UI ----------

    def setup_ui(self):
        self.root.configure(bg="#1e1e1e")

        style = ttk.Style()
        style.theme_use("default")

        style.configure("Treeview",
                        background="#2b2b2b",
                        foreground="white",
                        fieldbackground="#2b2b2b",
                        rowheight=25)

        style.configure("Treeview.Heading",
                        background="#333333",
                        foreground="white")

        top_frame = tk.Frame(self.root, bg="#1e1e1e")
        top_frame.pack(fill="x", pady=5)

        self.path_label = tk.Label(top_frame, text=self.current_path,
                                   bg="#1e1e1e", fg="white")
        self.path_label.pack(side="left", padx=10)

        back_btn = tk.Button(top_frame, text="⬅ Back",
                             command=self.go_back,
                             bg="#444", fg="white")
        back_btn.pack(side="right", padx=10)

        self.progress = ttk.Progressbar(self.root, mode="indeterminate")
        self.progress.pack(fill="x", padx=10, pady=5)

        # ---------- MAIN TABLE ----------
        columns = ("Name", "Size")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings")

        self.tree.heading("Name", text="Name")
        self.tree.heading("Size", text="Size")

        self.tree.column("Name", anchor="w")
        self.tree.column("Size", width=120, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

        self.tree.bind("<Double-1>", self.on_click)

        # ---------- TREEMAP ----------
        self.canvas = tk.Canvas(self.root, bg="#1e1e1e", height=200)
        self.canvas.pack(fill="x", padx=10, pady=5)

        # ---------- LARGEST FILES ----------
        self.large_label = tk.Label(self.root, text="Top Largest Files",
                                   bg="#1e1e1e", fg="white")
        self.large_label.pack()

        self.large_list = tk.Listbox(self.root, bg="#2b2b2b",
                                    fg="white", height=6)
        self.large_list.pack(fill="x", padx=10)

    # ---------- NAVIGATION ----------

    def go_back(self):
        parent = os.path.dirname(self.current_path)
        if parent and parent != self.current_path:
            self.current_path = parent
            self.load_directories(parent)

    def on_click(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        item = selected[0]
        path = self.tree.item(item, "tags")[0]

        if os.path.isdir(path):
            self.current_path = path
            self.load_directories(path)

    # ---------- LOADING ----------

    def load_directories(self, path):
        self.start_loading("Scanning...")
        self.tree.delete(*self.tree.get_children())
        self.large_list.delete(0, tk.END)
        self.canvas.delete("all")

        threading.Thread(target=self.scan_directories,
                         args=(path,), daemon=True).start()

    def scan_directories(self, path):
        results = []
        all_files = []

        try:
            items = os.listdir(path)
        except PermissionError:
            items = []

        futures = {}

        for item in items:
            full_path = os.path.join(path, item)

            if os.path.isdir(full_path):
                if full_path in self.cache:
                    results.append((item, self.cache[full_path], full_path))
                else:
                    future = self.executor.submit(self.get_folder_size, full_path)
                    futures[future] = (item, full_path)
            else:
                try:
                    size = os.path.getsize(full_path)
                    results.append((item, size, full_path))
                    all_files.append((item, size))
                except:
                    continue

        for future, (item, full_path) in futures.items():
            try:
                size = future.result()
                self.cache[full_path] = size
                results.append((item, size, full_path))
            except:
                continue


        for dirpath, dirs, files in os.walk(path):
            for file in files:
                try:
                    full_path = os.path.join(dirpath, file)
                    size = os.path.getsize(full_path)
                    all_files.append((file, size))
                except:
                    continue

        largest = sorted(all_files, key=lambda x: x[1], reverse=True)[:10]

        results.sort(key=lambda x: x[1], reverse=True)

        self.root.after(0, lambda: self.display_results(results, largest))

    def display_results(self, results, largest):
        for name, size, path in results:
            ext = os.path.splitext(name)[1]

            color_map = {
                ".exe": "#ff5555",
                ".zip": "#ffaa00",
                ".mp4": "#55aaff",
                ".png": "#55ff55",
                ".txt": "#aaaaaa"
            }

            color = color_map.get(ext, "#ffffff")

            self.tree.insert(
                "", "end",
                values=(name, self.format_size(size)),
                tags=(path, ext)
            )

            self.tree.tag_configure(ext, foreground=color)

        self.show_largest(largest)
        self.draw_treemap(largest)

        self.stop_loading(f"{len(results)} items | {self.current_path}")

    # ---------- VISUALS ----------

    def show_largest(self, files):
        self.large_list.delete(0, tk.END)

        for name, size in files:
            self.large_list.insert(
                tk.END,
                f"{name} - {self.format_size(size)}"
            )

    def draw_treemap(self, files):
        self.canvas.update_idletasks()
        self.canvas.delete("all")

        total_size = sum(size for _, size in files)
        if total_size == 0:
            return

        x = 0
        width = self.canvas.winfo_width()

        for name, size in files:
            proportion = size / total_size
            rect_width = int(width * proportion)

            color = "#" + hex(abs(hash(name)) % 0xFFFFFF)[2:].zfill(6)

            self.canvas.create_rectangle(
                x, 0, x + rect_width, 200,
                fill=color, outline=""
            )

            x += rect_width

    # ---------- HELPERS ----------

    def get_folder_size(self, path):
        if path in self.cache:
            return self.cache[path]

        total = 0

        for dirpath, dirs, files in os.walk(path):
            for file in files:
                try:
                    total += os.path.getsize(os.path.join(dirpath, file))
                except:
                    continue

        self.cache[path] = total
        return total

    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024

    def start_loading(self, text):
        self.path_label.config(text=text)
        self.progress.start()

    def stop_loading(self, text):
        self.progress.stop()
        self.path_label.config(text)


# ---------- MAIN ----------

if __name__ == "__main__":
    if not is_admin():
        relaunch_as_admin()

    root = tk.Tk()
    app = MemoryReader(root)
    root.mainloop()
    