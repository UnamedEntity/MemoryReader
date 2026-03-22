import os
import tkinter as tk
from tkinter import ttk
import shutil
from tkinter import messagebox
from concurrent.futures import ThreadPoolExecutor
import threading
import ctypes
import sys
import math

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

# ---------- APP ----------
class MemoryReader:
    def __init__(self, root):
        self.root = root
        self.root.title("Memory Analyzer")
        self.root.geometry("1100x700")

        self.current_path = "C:\\"
        self.executor = ThreadPoolExecutor(max_workers=8)
        self.cache = {}        # folder_path -> size (bytes)
        self.file_cache = {}   # file_path -> size (optional pre-cache)
        self.rect_map = {}     # canvas rect id -> (path, name, size)
        self.tooltip = None

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
                        rowheight=24)
        style.configure("Treeview.Heading",
                        background="#333333",
                        foreground="white")

        # Top frame: path, back, cache button
        top_frame = tk.Frame(self.root, bg="#1e1e1e")
        top_frame.pack(fill="x", padx=8, pady=6)

        self.path_label = tk.Label(top_frame, text=self.current_path,
                                   bg="#1e1e1e", fg="white")
        self.path_label.pack(side="left", padx=6)

        back_btn = tk.Button(top_frame, text="⬅ Back", command=self.go_back,
                             bg="#444", fg="white")
        back_btn.pack(side="right", padx=6)

        delete_btn = tk.Button(top_frame, text="🗑 Delete",
                       command=self.delete_selected,
                       bg="#aa3333", fg="white")

        delete_btn.pack(side="right", padx=6)

        cache_btn = tk.Button(top_frame, text="Cache folder (background)",
                              command=lambda: threading.Thread(
                                  target=self.cache_current_branch, daemon=True).start(),
                              bg="#2d6b2d", fg="white")
        cache_btn.pack(side="right", padx=6)

        # Progress bar
        self.progress = ttk.Progressbar(self.root, mode="indeterminate")
        self.progress.pack(fill="x", padx=10, pady=4)

        # Middle: left = tree, right = largest & info
        middle = tk.Frame(self.root, bg="#1e1e1e")
        middle.pack(fill="both", expand=True, padx=8, pady=6)

        # Tree (left)
        left_frame = tk.Frame(middle, bg="#1e1e1e")
        left_frame.pack(side="left", fill="both", expand=True)

        columns = ("Name", "Size")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Size", text="Size")
        self.tree.column("Name", anchor="w")
        self.tree.column("Size", width=140, anchor="center")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self.on_click)

        # Right panel (largest list & treemap)
        right_frame = tk.Frame(middle, width=380, bg="#1e1e1e")
        right_frame.pack(side="right", fill="y")

        # Treemap canvas
        self.canvas = tk.Canvas(right_frame, bg="#111111", height=220)
        self.canvas.pack(fill="x", padx=6, pady=6)
        # root binding resize to redraw treemap
        self.canvas.bind("<Configure>", lambda e: self.redraw_treemap())

        # Largest items label + listbox
        lbl = tk.Label(right_frame, text="Largest (scanned items)",
                       bg="#1e1e1e", fg="white")
        lbl.pack(anchor="w", padx=6)

        self.large_list = tk.Listbox(right_frame, bg="#2b2b2b", fg="white", height=12)
        self.large_list.pack(fill="both", padx=6, pady=6, expand=True)
        self.large_list.bind("<Double-1>", self.on_largest_double)

        # Bottom status
        self.status_label = tk.Label(self.root, text="Ready", bg="#1e1e1e", fg="white")
        self.status_label.pack(fill="x", padx=8, pady=4)

    # ---------- Navigation ----------
    def go_back(self):
        parent = os.path.dirname(self.current_path.rstrip(os.sep))
        if parent and parent != self.current_path:
            self.current_path = parent
            self.load_directories(parent)

    def on_click(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        item = selected[0]
        tags = self.tree.item(item, "tags")
        if not tags:
            return
        path = tags[0]
        if os.path.isdir(path):
            self.current_path = path
            self.load_directories(path)

    def on_largest_double(self, event):
        sel = self.large_list.curselection()
        if not sel:
            return
        text = self.large_list.get(sel[0])
        if " ||| " in text:
            _, path = text.split(" ||| ", 1)
            if os.path.isdir(path):
                self.current_path = path
                self.load_directories(path)

    # ---------- Loading / Scanning ----------
    def load_directories(self, path):
        self.start_loading("Scanning: " + path)
        self.tree.delete(*self.tree.get_children())
        self.large_list.delete(0, tk.END)
        self.canvas.delete("all")
        self.rect_map.clear()
        threading.Thread(target=self.scan_directories, args=(path,), daemon=True).start()

    def scan_directories(self, path):
        results = []   # tuples (name, size, full_path, is_dir)
        all_files = [] # list of (name, size, full_path) to compute largest files if needed

        try:
            items = os.listdir(path)
        except PermissionError:
            items = []
        except FileNotFoundError:
            items = []

        futures = {}
        files_added = []

        for item in items:
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                if full_path in self.cache:
                    results.append((item, self.cache[full_path], full_path, True))
                else:
                    future = self.executor.submit(self.get_folder_size, full_path)
                    futures[future] = (item, full_path)
            else:
                try:
                    size = os.path.getsize(full_path)
                    results.append((item, size, full_path, False))
                    files_added.append((item, size, full_path))
                except Exception:
                    continue

        # collect folder futures (map each future carefully)
        for future, (item, full_path) in futures.items():
            try:
                size = future.result()
                self.cache[full_path] = size
                results.append((item, size, full_path, True))
            except Exception:
                continue

        # Optionally walk deeper to gather files for largest list in current path
        # but only if the folder is not huge — we will go one level deeper for all files
        for dirpath, dirs, files in os.walk(path):
            for f in files:
                try:
                    fp = os.path.join(dirpath, f)
                    size = os.path.getsize(fp)
                    all_files.append((f, size, fp))
                except Exception:
                    continue

        # Prepare largest list: show largest **folders** first (scanned) then files
        # We'll show top 12 items sorted by size
        combined = [(n, s, p, isdir) for (n, s, p, isdir) in results]  # already has folders+files
        combined_files = list(all_files)
        combined_files_sorted = sorted(combined_files, key=lambda x: x[1], reverse=True)
        largest_files = combined_files_sorted[:50]  # used for treemap & drilldown files

        results.sort(key=lambda x: x[1], reverse=True)
        self.root.after(0, lambda: self.display_results(results, largest_files))

    def display_results(self, results, largest_files):
        # populate tree
        for name, size, path, is_dir in results:
            tag = path
            # tag with path for click navigation
            self.tree.insert("", "end", values=(name, self.format_size(size)), tags=(tag,))

        # largest list: show top scanned folders first
        folder_items = [ (n,s,p) for (n,s,p,isdir) in results if isdir ]
        top_folders = folder_items[:12]
        self.large_list.delete(0, tk.END)
        for name, size, path in top_folders:
            # store path hidden in the string so double-click finds it
            display = f"{name} - {self.format_size(size)} ||| {path}"
            self.large_list.insert(tk.END, display)

        # treemap: use largest_files (files found within this branch)
        self.treemap_items = [(name, size, fp) for (name, size, fp) in largest_files]
        self.draw_treemap(self.treemap_items)

        self.stop_loading(f"{len(results)} items | {self.current_path}")

    # ---------- Treemap & interactivity ----------
    def draw_treemap(self, items):
        self.canvas.delete("all")
        self.rect_map.clear()
        if not items:
            return

        total_size = sum(size for _, size, _ in items)
        if total_size <= 0:
            return

        width = max(100, self.canvas.winfo_width())
        height = max(50, self.canvas.winfo_height())
        x = 0

        # simple 1-row treemap (proportional width)
        for name, size, full_path in items:
            w = max(2, int(width * (size / total_size)))
            color = "#" + hex(abs(hash(full_path)) % 0xFFFFFF)[2:].zfill(6)
            rect = self.canvas.create_rectangle(x, 0, x + w, height, fill=color, outline="")
            # save mapping
            self.rect_map[rect] = (full_path, name, size)
            # attach bindings
            self.canvas.tag_bind(rect, "<Enter>", lambda e, r=rect: self.on_rect_enter(e, r))
            self.canvas.tag_bind(rect, "<Leave>", lambda e, r=rect: self.on_rect_leave(e, r))
            self.canvas.tag_bind(rect, "<Button-1>", lambda e, r=rect: self.on_rect_click(e, r))
            x += w

    def redraw_treemap(self):
        # redraw using last treemap items
        if hasattr(self, "treemap_items"):
            self.draw_treemap(self.treemap_items)

    def on_rect_enter(self, event, rect_id):
        path, name, size = self.rect_map.get(rect_id, ("", "", 0))
        text = f"{name}\n{self.format_size(size)}\n{path}"
        self.show_tooltip(event.x_root, event.y_root, text)

    def on_rect_leave(self, event, rect_id):
        self.hide_tooltip()

    def on_rect_click(self, event, rect_id):
        path, name, size = self.rect_map.get(rect_id, ("", "", 0))
        # if rectangle represents a file, navigate to its parent folder
        if os.path.isfile(path):
            folder = os.path.dirname(path)
            if os.path.isdir(folder):
                self.current_path = folder
                self.load_directories(folder)
        elif os.path.isdir(path):
            self.current_path = path
            self.load_directories(path)

    def show_tooltip(self, x, y, text):
        self.hide_tooltip()
        self.tooltip = tk.Toplevel(self.root)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.attributes("-topmost", True)
        label = tk.Label(self.tooltip, text=text, justify="left",
                         bg="#333333", fg="white", bd=1, padx=6, pady=4)
        label.pack()
        self.tooltip.geometry(f"+{x + 12}+{y + 12}")

    def hide_tooltip(self):
        if self.tooltip:
            try:
                self.tooltip.destroy()
            except Exception:
                pass
            self.tooltip = None

    # ---------- Caching helpers ----------
    def cache_current_branch(self):
        """Walk current_path and fill file_cache & cache with sizes.
           This runs in background, may take a long time on big drives.
        """
        base = self.current_path
        self.start_loading("Caching: " + base)
        local_file_count = 0
        for dirpath, dirs, files in os.walk(base):
            for f in files:
                try:
                    fp = os.path.join(dirpath, f)
                    if fp not in self.file_cache:
                        sz = os.path.getsize(fp)
                        self.file_cache[fp] = sz
                        local_file_count += 1
                except Exception:
                    continue
            if local_file_count % 500 == 0:
                self.root.after(0, lambda c=local_file_count: self.status_label.config(text=f"Cached files: {c}"))
        try:
            entries = os.listdir(base)
        except Exception:
            entries = []
        futures = {}
        for e in entries:
            full = os.path.join(base, e)
            if os.path.isdir(full):
                futures[self.executor.submit(self.get_folder_size, full)] = full
        for fut, path in futures.items():
            try:
                _ = fut.result()
            except Exception:
                continue
        self.root.after(0, lambda: self.stop_loading(f"Cached {local_file_count} files | {base}"))

    # ---------- Faster folder-size using scandir (iterative) ----------
    def get_folder_size(self, path):
        if path in self.cache:
            return self.cache[path]

        total = 0
        stack = [path]
        while stack:
            p = stack.pop()
            try:
                with os.scandir(p) as it:
                    for entry in it:
                        try:
                            if entry.is_dir(follow_symlinks=False):
                                stack.append(entry.path)
                            elif entry.is_file(follow_symlinks=False):
                                try:
                                    total += entry.stat(follow_symlinks=False).st_size
                                except Exception:
                                    continue
                        except Exception:
                            continue
            except Exception:
                continue

        self.cache[path] = total
        return total

    # ---------- Utilities ----------
    def format_size(self, size):
        if size is None:
            return "—"
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"



    def perform_delete(self, path):
        try:
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)

            # Remove from cache
            if path in self.cache:
                del self.cache[path]

            self.load_directories(self.current_path)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete:\n{e}")


    def delete_selected(self):
        selected = self.tree.selection()

        if not selected:
            sel = self.large_list.curselection()
            if sel:
                text = self.large_list.get(sel[0])
                if " ||| " in text:
                    _, path = text.split(" ||| ", 1)
                    self.confirm_delete(path)
            return

        item = selected[0]
        tags = self.tree.item(item, "tags")

        if not tags:
            return

        path = tags[0]
        self.confirm_delete(path)

    def confirm_delete(self, path):
        name = os.path.basename(path)

        result = messagebox.askyesno(
                "Confirm Delete",
                f"Are you sure you want to delete:\n\n{name}\n\nThis cannot be undone."
            )
        # Block deletion of system folders
        if path.startswith("C:\\Windows") or path.startswith("C:\\Program Files"):
            messagebox.showwarning("Blocked", "Cannot delete system folders.")
            return
           
        if result:
            self.perform_delete(path)

    def start_loading(self, text):
        self.path_label.config(text=text)
        try:
            self.progress.start()
        except Exception:
            pass
        self.status_label.config(text="Working...")

    def stop_loading(self, text):
        try:
            self.progress.stop()
        except Exception:
            pass
        self.path_label.config(text=text)
        self.status_label.config(text="Ready")

# ---------- MAIN ----------
if __name__ == "__main__":
    if not is_admin():
        relaunch_as_admin()

    root = tk.Tk()
    app = MemoryReader(root)
    root.mainloop()