import tkinter as tk
from tkinter import ttk, messagebox
import psutil
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

def refresh_process_list(sort_by='pid'):
    for widget in canvas_frame.winfo_children():
        widget.destroy()

    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
        try:
            pid = proc.info['pid']
            name = proc.info['name']
            cpu = proc.info['cpu_percent']
            mem = proc.info['memory_info'].rss / (1024 * 1024)  # Convert bytes to MB
            processes.append((pid, name, cpu, mem))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if sort_by == 'pid':
        processes.sort(key=lambda x: x[0])
    elif sort_by == 'cpu':
        processes.sort(key=lambda x: x[2], reverse=True)
    elif sort_by == 'memory':
        processes.sort(key=lambda x: x[3], reverse=True)
    
    tk.Label(canvas_frame, text=f"{'PID':<10} {'Name':<30} {'CPU%':<10} {'Memory(MB)':<10}", font=('Arial', 10, 'bold')).pack(anchor="w")
    
    for pid, name, cpu, mem in processes:
        tk.Label(canvas_frame, text=f"{pid:<10} {name:<30} {cpu:<10} {mem:<10.2f}").pack(anchor="w")

def terminate_process():
    pid = int(pid_entry.get())
    try:
        proc = psutil.Process(pid)
        proc.terminate()  # Or proc.kill() to force kill
        messagebox.showinfo("Success", f"Process {pid} terminated.")
        refresh_process_list(sort_by=sort_variable.get())
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        messagebox.showerror("Error", f"Could not terminate process {pid}.")

def on_frame_configure(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

def on_mouse_wheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

def update_periodically():
    refresh_process_list(sort_by=sort_variable.get())
    update_graphs()
    app.after(1000, update_periodically)

def update_graphs():
    processes = []
    for proc in psutil.process_iter(['pid', 'cpu_percent', 'memory_info']):
        try:
            pid = proc.info['pid']
            cpu = proc.info['cpu_percent']
            mem = proc.info['memory_info'].rss / (1024 * 1024)  # Convert bytes to MB
            processes.append((pid, cpu, mem))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    pids, cpus, mems = zip(*processes) if processes else ([], [], [])

    ax1.clear()
    ax2.clear()

    ax1.plot(pids, cpus, marker='o', linestyle='-', color='blue', label='CPU Usage')
    ax2.plot(pids, mems, marker='o', linestyle='-', color='red', label='Memory Usage')

    ax1.set_title('CPU Usage')
    ax1.set_xlabel('PID')
    ax1.set_ylabel('CPU %')
    ax1.grid(True)
    ax1.legend()

    ax2.set_title('Memory Usage')
    ax2.set_xlabel('PID')
    ax2.set_ylabel('Memory (MB)')
    ax2.grid(True)
    ax2.legend()

    canvas_agg.draw()

    # Connect hover event for interactive tooltips
    canvas_agg.mpl_connect('motion_notify_event', on_hover)

def on_hover(event):
    if event.inaxes:
        ax = event.inaxes
        xdata = event.xdata
        ydata = event.ydata

        if ax == ax1:
            line = ax.get_lines()[0]  # Get the first line in the axis
            xdata = int(round(xdata))  # Ensure integer PID
            if xdata in pids:
                index = pids.index(xdata)
                tooltip = f"PID: {pids[index]}\nCPU Usage: {cpus[index]}%"
                annot = ax.annotate(tooltip, xy=(xdata, cpus[index]), xytext=(10, 10),
                                    textcoords='offset points', bbox=dict(boxstyle='round', fc='w'),
                                    arrowprops=dict(arrowstyle='->'))
        elif ax == ax2:
            line = ax.get_lines()[0]
            xdata = int(round(xdata))  # Ensure integer PID
            if xdata in pids:
                index = pids.index(xdata)
                tooltip = f"PID: {pids[index]}\nMemory Usage: {mems[index]:.2f} MB"
                annot = ax.annotate(tooltip, xy=(xdata, mems[index]), xytext=(10, 10),
                                    textcoords='offset points', bbox=dict(boxstyle='round', fc='w'),
                                    arrowprops=dict(arrowstyle='->'))

        ax.figure.canvas.draw_idle()  # Redraw the canvas

app = tk.Tk()
app.title("Simple Task Manager")

notebook = ttk.Notebook(app)

# Create the Process List tab
process_tab = ttk.Frame(notebook)
notebook.add(process_tab, text="Processes")

canvas = tk.Canvas(process_tab)
scrollbar = tk.Scrollbar(process_tab, orient="vertical", command=canvas.yview)

canvas_frame = tk.Frame(canvas)
canvas.create_window((0, 0), window=canvas_frame, anchor="nw")
scrollbar.config(command=canvas.yview)
canvas.config(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

canvas_frame.bind("<Configure>", on_frame_configure)
app.bind_all("<MouseWheel>", on_mouse_wheel)

sort_variable = tk.StringVar(value='pid')

def sort_data():
    refresh_process_list(sort_by=sort_variable.get())

tk.Label(process_tab, text="Sort by:").pack()
sort_options = ['pid', 'cpu', 'memory']
for option in sort_options:
    tk.Radiobutton(process_tab, text=option.capitalize(), variable=sort_variable, value=option, command=sort_data).pack(anchor="w")

refresh_button = tk.Button(process_tab, text="Refresh", command=lambda: refresh_process_list(sort_by=sort_variable.get()))
refresh_button.pack(pady=10)

tk.Label(process_tab, text="PID to terminate:").pack()
pid_entry = tk.Entry(process_tab)
pid_entry.pack(pady=5)

terminate_button = tk.Button(process_tab, text="Terminate", command=terminate_process)
terminate_button.pack(pady=10)

# Create the Graphs tab
graphs_tab = ttk.Frame(notebook)
notebook.add(graphs_tab, text="Graphs")

fig = Figure(figsize=(8, 6), dpi=100)
ax1 = fig.add_subplot(211)
ax2 = fig.add_subplot(212)

canvas_agg = FigureCanvasTkAgg(fig, master=graphs_tab)
canvas_agg.get_tk_widget().pack(fill='both', expand=True)

notebook.pack(fill='both', expand=True)

update_periodically()

app.mainloop()
