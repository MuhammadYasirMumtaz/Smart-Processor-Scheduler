import tkinter as tk
from tkinter import ttk, messagebox, Canvas
import datetime
import time
import threading
import queue as thread_queue
import winsound

class ManagedProcess:
    def __init__(self, pid, name, sleep_time, priority, queue):
        self.pid = pid
        self.name = name
        self.sleep_time = sleep_time
        self.priority = priority
        self.queue = queue
        self.status = "Waiting"
        self.start_time = None
        self.end_time = None
        self.progress = 0
        self.remaining = sleep_time
        self.thread = None
        self.pause_event = threading.Event()
        self.pause_event.set()

    def run(self):
        self.start_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.queue.put(("gantt_start", self.pid, time.time()))
        while self.remaining > 0:
            self.pause_event.wait()
            time.sleep(1)
            self.remaining -= 1
            self.progress = int(100 * (self.sleep_time - self.remaining) / self.sleep_time)
            self.queue.put(("update", self.pid, self.progress))
        self.end_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.status = "Completed"
        self.queue.put(("completed", self.pid))
        self.queue.put(("gantt_end", self.pid, time.time()))

    def start(self):
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def pause(self):
        self.pause_event.clear()

    def resume(self):
        self.pause_event.set()

class SchedulerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi Process Alarm Scheduler")
        self.process_list = []
        self.running_processes = []
        self.paused_processes = []
        self.pid_counter = 1
        self.max_running = 2
        self.queue = thread_queue.Queue()
        self.preemptive_enabled = tk.BooleanVar(value=False)
        self.selected_pid = None
        self.gantt_data = {}

        self.build_scrollable_ui()
        self.update_gui()

    def build_scrollable_ui(self):
        canvas = Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        self.scroll_frame = ttk.Frame(canvas)

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.setup_ui(self.scroll_frame)

    def setup_ui(self, frame):
        ttk.Label(frame, text="Add New Process", font=('Helvetica', 12, 'bold')).pack(anchor='w')
        form = ttk.Frame(frame)
        form.pack(anchor='w', pady=5)
        ttk.Label(form, text="Name:").grid(row=0, column=0)
        self.name_entry = ttk.Entry(form, width=15)
        self.name_entry.grid(row=0, column=1)

        ttk.Label(form, text="Time (s):").grid(row=0, column=2)
        self.sleep_entry = ttk.Entry(form, width=5)
        self.sleep_entry.grid(row=0, column=3)

        ttk.Label(form, text="Priority:").grid(row=0, column=4)
        self.priority_box = ttk.Combobox(form, values=list(range(1, 11)), width=3)
        self.priority_box.grid(row=0, column=5)
        self.priority_box.set(5)

        ttk.Button(form, text="Add", command=self.add_process).grid(row=0, column=6, padx=5)
        ttk.Checkbutton(form, text="Primitive (Preemptive)", variable=self.preemptive_enabled).grid(row=0, column=7)

        ttk.Label(frame, text="Sorting Options", font=('Helvetica', 12, 'bold')).pack(anchor='w', pady=(10, 0))
        sort_frame = ttk.Frame(frame)
        sort_frame.pack(anchor='w')
        self.sort_var = tk.StringVar(value="priority")
        ttk.Radiobutton(sort_frame, text="Priority", variable=self.sort_var, value="priority").pack(side=tk.LEFT)
        ttk.Radiobutton(sort_frame, text="Status", variable=self.sort_var, value="status").pack(side=tk.LEFT)
        ttk.Radiobutton(sort_frame, text="Start Time", variable=self.sort_var, value="start_time").pack(side=tk.LEFT)

        ttk.Label(frame, text="All Processes", font=('Helvetica', 12, 'bold')).pack(anchor='w', pady=(10, 0))
        self.process_table = tk.Text(frame, height=10, width=150)
        self.process_table.pack()

        ttk.Label(frame, text="Process Information", font=('Helvetica', 12, 'bold')).pack(anchor='w', pady=(10, 0))
        info_frame = ttk.Frame(frame)
        info_frame.pack()
        self.info_table = tk.Text(info_frame, height=5, width=150, wrap=tk.WORD)
        self.info_scroll = ttk.Scrollbar(info_frame, command=self.info_table.yview)
        self.info_table.configure(yscrollcommand=self.info_scroll.set)
        self.info_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.info_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        change_frame = ttk.Frame(frame)
        change_frame.pack(anchor='w', pady=5)
        ttk.Label(change_frame, text="Change Priority for PID:").pack(side=tk.LEFT)
        self.pid_change_entry = ttk.Entry(change_frame, width=5)
        self.pid_change_entry.pack(side=tk.LEFT)
        ttk.Label(change_frame, text=" to ").pack(side=tk.LEFT)
        self.new_priority_entry = ttk.Entry(change_frame, width=5)
        self.new_priority_entry.pack(side=tk.LEFT)
        ttk.Button(change_frame, text="Change", command=self.change_priority).pack(side=tk.LEFT, padx=5)

        ttk.Label(frame, text="Process Logs", font=('Helvetica', 12, 'bold')).pack(anchor='w', pady=(10, 0))
        self.log_box = tk.Text(frame, height=8, width=150)
        self.log_box.pack()

        ttk.Label(frame, text="Gantt Chart", font=('Helvetica', 12, 'bold')).pack(anchor='w', pady=(10, 0))
        self.gantt_scroll_canvas = Canvas(frame, width=1000, height=220, bg="white")
        self.gantt_scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.gantt_scroll_canvas.yview)
        self.gantt_inner_frame = ttk.Frame(self.gantt_scroll_canvas)
        self.gantt_inner_frame.bind("<Configure>", lambda e: self.gantt_scroll_canvas.configure(scrollregion=self.gantt_scroll_canvas.bbox("all")))
        self.gantt_scroll_canvas.create_window((0, 0), window=self.gantt_inner_frame, anchor="nw")
        self.gantt_scroll_canvas.configure(yscrollcommand=self.gantt_scrollbar.set)
        self.gantt_scroll_canvas.pack(side="left", fill="both", expand=True)
        self.gantt_scrollbar.pack(side="right", fill="y")

        self.gantt_canvas = Canvas(self.gantt_inner_frame, width=1000, height=1000, bg="white")
        self.gantt_canvas.pack()

        self.process_table.bind("<Button-1>", self.select_process)

    def add_process(self):
        name = self.name_entry.get()
        try:
            time_ = int(self.sleep_entry.get())
            priority = int(self.priority_box.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Time and priority must be numbers.")
            return
        proc = ManagedProcess(self.pid_counter, name, time_, priority, self.queue)
        self.process_list.append(proc)
        self.log(f"Process {proc.pid} added with priority {priority}")
        self.notify(f"Process {proc.pid} added.")
        self.pid_counter += 1
        self.schedule()

    def change_priority(self):
        try:
            pid = int(self.pid_change_entry.get())
            new_priority = int(self.new_priority_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Priority and PID must be numbers.")
            return
        for p in self.process_list:
            if p.pid == pid:
                old_priority = p.priority
                p.priority = new_priority
                self.log(f"Process {pid} priority changed from {old_priority} to {new_priority}")
                self.notify(f"Priority of Process {pid} changed.")
                self.schedule()
                break

    def schedule(self):
        self.running_processes = [p for p in self.process_list if p.status == "Running"]
        self.paused_processes = [p for p in self.process_list if p.status == "Paused"]
        waiting = [p for p in self.process_list if p.status == "Waiting"]

        if self.preemptive_enabled.get():
            all_active = self.running_processes + self.paused_processes + waiting
            all_active.sort(key=lambda x: x.priority)
            self.running_processes.clear()
            self.paused_processes.clear()
            for proc in all_active:
                if proc.status == "Completed":
                    continue
                if len(self.running_processes) < self.max_running:
                    if not proc.thread or not proc.thread.is_alive():
                        proc.start()
                    proc.resume()
                    proc.status = "Running"
                    self.running_processes.append(proc)
                else:
                    proc.pause()
                    proc.status = "Paused"
                    self.paused_processes.append(proc)
        else:
            for p in waiting:
                if len(self.running_processes) < self.max_running:
                    p.start()
                    p.status = "Running"
                    self.running_processes.append(p)

    def update_gui(self):
        try:
            while True:
                msg = self.queue.get_nowait()
                if msg[0] == "update":
                    pid, progress = msg[1], msg[2]
                    for p in self.process_list:
                        if p.pid == pid:
                            p.progress = progress
                elif msg[0] == "completed":
                    pid = msg[1]
                    for p in self.process_list:
                        if p.pid == pid:
                            p.status = "Completed"
                            self.log(f"Process {pid} completed.")
                            self.notify(f"Process {pid} completed.")
                            self.schedule()
                elif msg[0] == "gantt_start":
                    self.gantt_data[msg[1]] = [msg[2], None]
                elif msg[0] == "gantt_end":
                    self.gantt_data[msg[1]][1] = msg[2]
        except thread_queue.Empty:
            pass

        self.process_table.delete("1.0", tk.END)
        sorted_list = self.process_list
        if self.sort_var.get() == "priority":
            sorted_list = sorted(self.process_list, key=lambda x: x.priority)
        elif self.sort_var.get() == "status":
            order = {"Running": 0, "Paused": 1, "Waiting": 2, "Completed": 3}
            sorted_list = sorted(self.process_list, key=lambda x: order.get(x.status, 99))
        elif self.sort_var.get() == "start_time":
            sorted_list = sorted(self.process_list, key=lambda x: x.start_time or "")

        for p in sorted_list:
            self.process_table.insert(tk.END, f"PID {p.pid} | {p.name} | Priority: {p.priority} | Status: {p.status} | Progress: {p.progress}%\n")

        if self.selected_pid is not None:
            for p in self.process_list:
                if p.pid == self.selected_pid:
                    current_scroll = self.info_table.yview()
                    self.info_table.delete("1.0", tk.END)
                    self.info_table.insert(tk.END, f"Process #{p.pid}\nName: {p.name}\nPriority: {p.priority}\nStatus: {p.status}\nProgress: {p.progress}%\nStart: {p.start_time}\nEnd: {p.end_time}\nRemaining: {p.remaining}s")
                    self.info_table.yview_moveto(current_scroll[0])
                    break

        self.draw_gantt_chart()
        self.root.after(1000, self.update_gui)

    def draw_gantt_chart(self):
        self.gantt_canvas.delete("all")
        x = 10
        y = 20
        height = 20
        scale = 10

        for pid, (start, end) in self.gantt_data.items():
            if end is None:
                end = time.time()
            width = (end - start) * scale
            self.gantt_canvas.create_rectangle(x, y, x + width, y + height, fill="skyblue")
            self.gantt_canvas.create_text(x + width / 2, y + 10, text=f"P{pid}")
            y += 30

    def select_process(self, event):
        try:
            index = self.process_table.index(f"@{event.x},{event.y}")
            line = self.process_table.get(f"{index} linestart", f"{index} lineend")
            pid = int(line.split()[1])
            self.selected_pid = pid
        except Exception:
            pass

    def log(self, msg):
        ts = datetime.datetime.now().strftime("[%H:%M:%S]")
        self.log_box.insert(tk.END, f"{ts} {msg}\n")
        self.log_box.see(tk.END)

    def notify(self, message):
        winsound.MessageBeep()
        messagebox.showinfo("Notification", message)

if __name__ == "__main__":
    root = tk.Tk()
    app = SchedulerApp(root)
    root.mainloop()


























