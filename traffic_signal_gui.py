import tkinter as tk
from tkinter import Canvas, Frame, Button, Label
import threading
import time

from traffic_signal_control import bfs, reconstruct_path, Vehicle, Intersection
from signal_phase_controller import SignalPhaseController

CELL_SIZE = 60
GRID_ROWS = 5
GRID_COLS = 5

VEHICLE_COLORS = ["#FF0000", "#0000FF", "#00AA00", "#FFAA00", "#AA00FF"]

class TrafficSignalGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Real-Time Traffic Signal Control with BFS and Coordinated Phases")

        self.main_frame = Frame(master)
        self.main_frame.pack()

        self.canvas = Canvas(self.main_frame, width=GRID_COLS*CELL_SIZE, height=GRID_ROWS*CELL_SIZE, bg="#e0e0e0", highlightthickness=0)
        self.canvas.grid(row=0, column=0, rowspan=4, padx=10, pady=10)

        self.control_frame = Frame(self.main_frame)
        self.control_frame.grid(row=0, column=1, sticky="n", padx=10, pady=10)

        self.status_frame = Frame(self.main_frame)
        self.status_frame.grid(row=1, column=1, sticky="n", padx=10, pady=10)

        self.grid = [
            [0, 0, 0, 0, 0],
            [1, 1, 0, 1, 0],
            [0, 0, 0, 0, 0],
            [0, 1, 0, 1, 1],
            [0, 0, 0, 0, 0]
        ]

        self.intersections = {}
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                if self.grid[r][c] == 0:
                    neighbors = []
                    for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < GRID_ROWS and 0 <= nc < GRID_COLS and self.grid[nr][nc] == 0:
                            neighbors.append((nr, nc))
                    self.intersections[(r,c)] = Intersection((r,c), neighbors)

        self.phase_controller = SignalPhaseController(self.intersections, phase_duration=5)

        self.vehicles = []
        vehicle_routes = [
            ((0, 0), (4, 4)),
            ((4, 0), (0, 4)),
            ((2, 0), (2, 4)),
            ((0, 2), (4, 2))
        ]
        for i, (start, dest) in enumerate(vehicle_routes):
            vehicle = Vehicle(f"V{i+1}", start, dest)
            parent = bfs(self.grid, start, dest)
            if parent:
                path = reconstruct_path(parent, start, dest)
                vehicle.set_path(path[1:])
            else:
                vehicle.set_path([])
            vehicle.color = VEHICLE_COLORS[i % len(VEHICLE_COLORS)]
            vehicle.wait_time = 0
            vehicle.travel_time = 0
            self.vehicles.append(vehicle)

        self.intersection_waits = {pos: 0 for pos in self.intersections}

        self.running = False
        self.simulation_thread = None

        self.start_button = Button(self.control_frame, text="Start", command=self.start_simulation, width=10)
        self.start_button.pack(pady=5)
        self.pause_button = Button(self.control_frame, text="Pause", command=self.pause_simulation, width=10, state="disabled")
        self.pause_button.pack(pady=5)
        self.reset_button = Button(self.control_frame, text="Reset", command=self.reset_simulation, width=10)
        self.reset_button.pack(pady=5)

        self.status_label = Label(self.status_frame, text="Status: Ready", justify="left")
        self.status_label.pack()

        self.draw_static_grid()
        self.draw_dynamic_elements()

    def draw_static_grid(self):
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                x1 = c * CELL_SIZE
                y1 = r * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE
                if self.grid[r][c] == 1: 
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill="#333333", outline="#222222", tags="static")
                    for i in range(5):
                        self.canvas.create_line(x1, y1 + i*12, x2, y1 + i*12, fill="#444444", tags="static")
                else:
                    for i in range(CELL_SIZE):
                        color_val = 230 - i
                        color = f"#{color_val:02x}{color_val:02x}{color_val:02x}"
                        self.canvas.create_line(x1, y1 + i, x2, y1 + i, fill=color, tags="static")

    def draw_dynamic_elements(self):
        self.canvas.delete("dynamic")

        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                if self.grid[r][c] == 0:
                    x1 = c * CELL_SIZE
                    y1 = r * CELL_SIZE
                    x2 = x1 + CELL_SIZE
                    y2 = y1 + CELL_SIZE
                    intersection = self.intersections.get((r, c))
                    if intersection and intersection.traffic_signal:
                        signal = intersection.traffic_signal
                        color = "red" if signal.state == "RED" else "green"
                        self.canvas.create_oval(x1+22, y1+22, x2-18, y2-18, fill="gray20", tags="dynamic")
                        self.canvas.create_oval(x1+20, y1+20, x2-20, y2-20, fill=color, tags="dynamic")

        for vehicle in self.vehicles:
            vr, vc = vehicle.position
            vx1 = vc * CELL_SIZE + 15
            vy1 = vr * CELL_SIZE + 15
            vx2 = vx1 + 30
            vy2 = vy1 + 30
            self.canvas.create_rectangle(vx1+3, vy1+3, vx2+3, vy2+3, fill="gray30", outline="", tags="dynamic")
            for i in range(15):
                self.canvas.create_rectangle(vx1, vy1+i*2, vx2, vy1+(i+1)*2, fill=vehicle.color, outline="", tags="dynamic")

    def simulation_loop(self):
        step = 0
        max_steps = 100
        while self.running and step < max_steps:
            all_arrived = True
            self.phase_controller.update_signals(self.vehicles)

            for vehicle in self.vehicles:
                vehicle.increment_travel_time()
                if vehicle.position != vehicle.destination and vehicle.path:
                    next_pos = vehicle.path[0]
                    signal = self.intersections[next_pos].traffic_signal

                    cur_r, cur_c = vehicle.position
                    next_r, next_c = next_pos
                    vertical_move = (next_c == cur_c and next_r != cur_r)
                    horizontal_move = (next_r == cur_r and next_c != cur_c)

                    if signal.state == "GREEN" and (
                        (self.phase_controller.current_phase == 0 and vertical_move) or
                        (self.phase_controller.current_phase == 1 and horizontal_move)):
                        vehicle.move()
                    else:
                        vehicle.increment_wait_time()
                        self.intersection_waits[next_pos] += 1
                elif vehicle.position != vehicle.destination:
                    vehicle.increment_wait_time()

                if vehicle.position != vehicle.destination:
                    all_arrived = False

            self.draw_dynamic_elements()

            status = f"Step: {step+1}\n"
            status += "Signal States:\n"
            for pos in sorted(self.intersections.keys()):
                signal = self.intersections[pos].traffic_signal
                state = "GREEN" if signal.state == "GREEN" else "RED"
                status += f"  {pos}: {state}\n"

            status += "\nIntersection Waits (Live):\n"
            for pos, count in sorted(self.intersection_waits.items()):
                if count > 0:
                    status += f"  {pos}: {count}\n"

            status += "\nVehicle Routes:\n"
            for vehicle in self.vehicles:
                status += f"  {vehicle.vehicle_id}: {vehicle.start} → {vehicle.position} → {vehicle.destination}\n"

            self.status_label.config(text=status)

            if all_arrived:
                break

            step += 1
            time.sleep(1)

        self.running = False
        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled")

        total_wait = sum(v.wait_time for v in self.vehicles)
        total_travel = sum(v.travel_time for v in self.vehicles)
        avg_wait = total_wait / len(self.vehicles)
        avg_travel = total_travel / len(self.vehicles)

        summary = f"All vehicles arrived in {step+1} steps.\n"
        summary += f"Avg Wait: {avg_wait:.2f}, Avg Travel: {avg_travel:.2f}\n\n"
        summary += "Intersection Waits:\n"
        for pos, count in sorted(self.intersection_waits.items()):
            if count > 0:
                summary += f"  {pos}: {count} waits\n"

        summary += "\nVehicle Final Positions:\n"
        for vehicle in self.vehicles:
            summary += f"  {vehicle.vehicle_id}: {vehicle.start} → {vehicle.position} → {vehicle.destination}\n"

        self.status_label.config(text=summary)

    def start_simulation(self):
        if not self.running:
            self.running = True
            self.start_button.config(state="disabled")
            self.pause_button.config(state="normal")
            self.simulation_thread = threading.Thread(target=self.simulation_loop)
            self.simulation_thread.start()

    def pause_simulation(self):
        self.running = False
        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled")

    def reset_simulation(self):
        self.running = False
        if self.simulation_thread is not None:
            self.simulation_thread.join()

        vehicle_routes = [
            ((0, 0), (4, 4)),
            ((4, 0), (0, 4)),
            ((2, 0), (2, 4)),
            ((0, 2), (4, 2))
        ]
        for i, vehicle in enumerate(self.vehicles):
            start, dest = vehicle_routes[i]
            vehicle.start = start
            vehicle.position = start
            vehicle.destination = dest
            parent = bfs(self.grid, start, dest)
            if parent:
                path = reconstruct_path(parent, start, dest)
                vehicle.set_path(path[1:])
            else:
                vehicle.set_path([])
            vehicle.wait_time = 0
            vehicle.travel_time = 0

        for pos in self.intersection_waits:
            self.intersection_waits[pos] = 0

        self.phase_controller.last_switch_time = time.time()
        self.phase_controller.current_phase = 0

        self.draw_dynamic_elements()
        self.status_label.config(text="Status: Ready")
        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = TrafficSignalGUI(root)
    root.mainloop()
