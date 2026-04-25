from collections import deque
import time

class TrafficSignal:
    def __init__(self, intersection_id):
        self.intersection_id = intersection_id
        self.state = "RED"  # Initial state
        self.timer = 0

    def change_state(self, new_state):
        self.state = new_state
        self.timer = 0

    def update(self):
        # Simple timer-based state change logic (acan be improved)
        self.timer += 1
        if self.state == "RED" and self.timer >= 5:
            self.change_state("GREEN")
        elif self.state == "GREEN" and self.timer >= 5:
            self.change_state("RED")

class Intersection:
    def __init__(self, intersection_id, neighbors):
        self.intersection_id = intersection_id
        self.neighbors = neighbors  # List of neighboring intersection ids
        self.traffic_signal = TrafficSignal(intersection_id)

class Vehicle:
    def __init__(self, vehicle_id, start, destination):
        self.wait_time = 0
        self.travel_time = 0
        self.vehicle_id = vehicle_id
        self.position = start
        self.start = start 
        self.destination = destination
        self.path = []


    def set_path(self, path):
        self.path = path

    def move(self):
        
        if self.path:
            self.position = self.path.pop(0)
    def increment_wait_time(self):
        self.wait_time += 1
    def increment_travel_time(self):
        self.travel_time += 1


def bfs(grid, start, destination):
    rows, cols = len(grid), len(grid[0])
    visited = [[False]*cols for _ in range(rows)]
    parent = [[None]*cols for _ in range(rows)]

    directions = [(1,0), (-1,0), (0,1), (0,-1)]

    queue = deque([start])
    visited[start[0]][start[1]] = True

    while queue:
        r, c = queue.popleft()
        if (r, c) == destination:
            return parent
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if not visited[nr][nc] and grid[nr][nc] == 0:
                    visited[nr][nc] = True
                    parent[nr][nc] = (r, c)
                    queue.append((nr, nc))
    return None

def reconstruct_path(parent, start, destination):
    path = []
    current = destination
    while current != start:
        path.append(current)
        current = parent[current[0]][current[1]]
        if current is None:
            return []
    path.append(start)
    path.reverse()
    return path
print("Vehicle class loaded from:", __file__)