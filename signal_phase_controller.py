import time
from copy import deepcopy
from itertools import product

class SignalPhaseController:
    def __init__(self, intersections, phase_duration=5):
        self.intersections = intersections
        self.phase_duration = phase_duration
        self.current_phase = 0  # 0 = N-S green, 1 = E-W green
        self.last_switch_time = time.time()

        # Initialize all traffic signals at intersections
        for intersection in self.intersections.values():
            intersection.traffic_signal = TrafficSignal("RED")

    def update_signals(self, vehicles):
        now = time.time()
        # Only evaluate phase change if duration has elapsed
        if now - self.last_switch_time >= self.phase_duration:
            next_phase = self.bfs_signal_decision(vehicles)
            if next_phase != self.current_phase:
                self.current_phase = next_phase
                self.last_switch_time = now

        # Update signals based on current phase
        for pos, intersection in self.intersections.items():
            r, c = pos
            if self.current_phase == 0:  # N-S green
                if self.is_vertical_road(r, c):
                    intersection.traffic_signal.state = "GREEN"
                else:
                    intersection.traffic_signal.state = "RED"
            else:  # E-W green
                if self.is_horizontal_road(r, c):
                    intersection.traffic_signal.state = "GREEN"
                else:
                    intersection.traffic_signal.state = "RED"

    def bfs_signal_decision(self, vehicles, depth=3):
        def simulate(phase_sequence, intersections, vehicles):
            intersections = deepcopy(intersections)
            vehicles = deepcopy(vehicles)
            wait_time = 0
            for phase in phase_sequence:
                # Update traffic signals for this phase
                for pos, inter in intersections.items():
                    r, c = pos
                    if phase == 0 and self.is_vertical_road(r, c):
                        inter.traffic_signal.state = "GREEN"
                    elif phase == 1 and self.is_horizontal_road(r, c):
                        inter.traffic_signal.state = "GREEN"
                    else:
                        inter.traffic_signal.state = "RED"

                # Simulate vehicle movement
                for vehicle in vehicles:
                    if vehicle.position != vehicle.destination and vehicle.path:
                        next_pos = vehicle.path[0]
                        signal = intersections[next_pos].traffic_signal
                        cur_r, cur_c = vehicle.position
                        next_r, next_c = next_pos
                        vertical_move = (next_c == cur_c and next_r != cur_r)
                        horizontal_move = (next_r == cur_r and next_c != cur_c)

                        if signal.state == "GREEN":
                            if phase == 0 and vertical_move:
                                vehicle.move()
                            elif phase == 1 and horizontal_move:
                                vehicle.move()
                        else:
                            wait_time += 1
                    elif vehicle.position != vehicle.destination:
                        wait_time += 1  # Still waiting
            return wait_time

        phase_options = [0, 1]
        phase_sequences = list(product(phase_options, repeat=depth))

        best_sequence = None
        min_wait = float("inf")
        for sequence in phase_sequences:
            wait = simulate(sequence, self.intersections, vehicles)
            if wait < min_wait:
                min_wait = wait
                best_sequence = sequence

        return best_sequence[0] if best_sequence else self.current_phase

    def is_vertical_road(self, r, c):
        neighbors = self.intersections[(r, c)].neighbors
        for nr, nc in neighbors:
            if nc == c:
                return True
        return False

    def is_horizontal_road(self, r, c):
        neighbors = self.intersections[(r, c)].neighbors
        for nr, nc in neighbors:
            if nr == r:
                return True
        return False


class TrafficSignal:
    def __init__(self, state="RED"):
        self.state = state


if __name__ == "__main__":
    print("SignalPhaseController with BFS decision logic ran successfully!")
