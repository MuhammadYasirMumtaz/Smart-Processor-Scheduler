# Smart Process Scheduler

A Python-based CPU scheduling simulator built on core Operating System principles. Visualizes process execution through **Gantt Charts** with support for multiple scheduling algorithms.

---

## Scheduling Algorithms

| Algorithm | Type | Description |
|---|---|---|
| **SJF** | Non-Preemptive | Shortest Job First — executes the process with the least burst time |
| **SRTF** | Preemptive | Shortest Remaining Time First — preempts if a shorter job arrives |
| **Priority (Non-Preemptive)** | Non-Preemptive | Executes highest priority process without interruption |
| **Priority (Preemptive)** | Preemptive | Higher priority process can interrupt the running process |

---

## Features

- ✅ Simulate multiple CPU scheduling algorithms
- ✅ Preemptive & Non-Preemptive modes
- ✅ Gantt Chart visualization of process execution
- ✅ Calculates **Waiting Time**, **Turnaround Time**, and **Completion Time**
- ✅ Built on core OS scheduling concepts

---

## Getting Started

### Prerequisites
- Python 3.x

### Run the project
```bash
python main.py
```

---

## OS Concepts Used

- **Process Scheduling** — managing CPU time among multiple processes
- **Burst Time** — the time a process needs on the CPU
- **Arrival Time** — when a process enters the ready queue
- **Priority Scheduling** — assigning importance levels to processes
- **Preemption** — interrupting a running process for a higher-priority one
- **Gantt Chart** — visual timeline of process execution order

---

## Author

**Muhammad Yasir Mumtaz**  
[GitHub](https://github.com/MuhammadYasirMumtaz)
