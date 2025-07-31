import heapq
from typing import List, Tuple, Set, Optional

class Planner:
    #Initialization
    def __init__(self, env_size: int):
        self.env_size = env_size
        self.visited = set()
        self.returning = False
        self.directions = ["N", "E", "S", "W"]
        self.dir_map = {(0, 1): "N", (1, 0): "E", (0, -1): "S", (-1, 0): "W"}
        self.direction_deltas = {"N": (0, 1), "E": (1, 0), "S": (0, -1), "W": (-1, 0)}

    # Reset the planner
    def reset(self):
        self.visited.clear()
        self.returning = False

    # Get positions of neighbors
    def get_neighbors(self, pos):
        x, y = pos
        neighbors = []
        for dx, dy in self.dir_map:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.env_size and 0 <= ny < self.env_size:
                neighbors.append((nx, ny))
        return neighbors

    # Check is a position is safe to move to
    def is_safe(self, pos, inference, env):
        if inference.infer(pos) == 'unsafe':
            return False
        cell = env.grid[pos[0]][pos[1]]
        return not (getattr(cell, 'has_pit', False) or getattr(cell, 'has_wumpus', False))

    # Dijkstra for pathfinding
    def dijkstra(self, start, goal, inference, env) -> Optional[List[Tuple[int, int]]]:
        pq = [(0, start)]
        dist = {start: 0}
        prev = {}
        visited = set()

        while pq:
            cost, current = heapq.heappop(pq)
            if current in visited:
                continue
            visited.add(current)

            if current == goal:
                path = []
                while current in prev:
                    path.append(current)
                    current = prev[current]
                path.append(start)
                return path[::-1]

            for neighbor in self.get_neighbors(current):
                if neighbor in visited or not self.is_safe(neighbor, inference, env):
                    continue
                
                extra = 1
                if inference.infer(neighbor) == 'uncertain':
                    extra = 10

                new_cost = cost + extra
                if neighbor not in dist or new_cost < dist[neighbor]:
                    dist[neighbor] = new_cost
                    prev[neighbor] = current
                    heapq.heappush(pq, (new_cost, neighbor))
        return None
    
    # Returns the position of the closest safe and unvisited tile
    def get_target(self, pos, inference, env) -> Optional[Tuple[int, int]]:
        target = []
        for x in range(self.env_size):
            for y in range(self.env_size):
                p = (x, y)
                if p not in self.visited and self.is_safe(p, inference, env):
                    dist = abs(pos[0] - x) + abs(pos[1] - y)
                    target.append((dist, p))
        if target:
            target.sort()
            return target[0][1]
        return None
    
    # Returns the position of the closest safe and visited tile
    def get_backtrack_target(self, pos, inference, env) -> Optional[Tuple[int, int]]:
        target = []
        for p in self.visited:
            if not self.is_safe(p, inference, env):
                continue
            for neighbor in self.get_neighbors(p):
                if neighbor not in self.visited and self.is_safe(neighbor, inference, env):
                    dist = abs(pos[0] - p[0]) + abs(pos[1] - p[1])
                    target.append((dist, p))
                    break
        if target:
            target.sort()
            return target[0][1]
        return None

    # Turn towards a direction
    def turn_toward(self, current_dir, target_dir):
        dirs = self.directions
        i, j = dirs.index(current_dir), dirs.index(target_dir)
        if (j - i) % 4 == 1:
            return "turn_right"
        elif (i - j) % 4 == 1:
            return "turn_left"
        elif abs(j - i) == 2:
            return "turn_right"
        return None

    # Find wumpus
    def find_wumpus_tile(self, pos, inference, desperate=False) -> Optional[Tuple[int, int]]:
        x0, y0 = pos
        target = []

        # Get all known or suspected Wumpus positions
        for x in range(self.env_size):
            for y in range(self.env_size):
                is_known_wumpus = f"W{x}{y}" in inference.kb.facts
                is_uncertain = inference.infer((x, y)) == 'uncertain'
                if is_known_wumpus or (desperate and is_uncertain):
                    wx, wy = x, y

                    # Vertical
                    if x == x0:
                        dy = 1 if wy > y0 else -1
                        clear_path = True
                        for ty in range(y0 + dy, wy, dy):
                            if not (0 <= ty < self.env_size):
                                clear_path = False
                                break
                        if clear_path:
                            stench_tile = (x0, wy - dy)
                            dist = abs(wy - y0)
                            target.append((dist, stench_tile))

                    # Horizontally
                    elif y == y0:
                        dx = 1 if wx > x0 else -1
                        clear_path = True
                        for tx in range(x0 + dx, wx, dx):
                            if not (0 <= tx < self.env_size):
                                clear_path = False
                                break
                        if clear_path:
                            stench_tile = (wx - dx, y0)
                            dist = abs(wx - x0)
                            target.append((dist, stench_tile))
                            
        if target:
            target.sort()
            return target[0][1]
        return None
    
    # Get the Wumpus direction from stench cell
    def get_wumpus_direction_from_tile(self, pos, inference) -> Optional[str]:
        x0, y0 = pos
        for dir in self.directions:
            dx, dy = self.direction_deltas[dir]
            x, y = x0 + dx, y0 + dy
            if 0 <= x < self.env_size and 0 <= y < self.env_size:
                if f"W{x}{y}" in inference.kb.facts:
                    return dir
        return None
    
    # The plan of the agent
    def plan(self, agent, inference, env) -> Optional[str]:
        pos = tuple(agent.position)
        self.visited.add(pos)

        percepts = env.get_percepts()
        if 'G' in percepts and not agent.has_gold:
            return "grab"

        # Prioritize returning when has gold
        if agent.has_gold:
            self.returning = True

        # Climb if has gold and at (0, 0)
        if self.returning and pos == (0, 0):
            return "climb"

        # Find a safe new location to move to next
        target = (0, 0) if self.returning else self.get_target(pos, inference, env)
        if target:
            path = self.dijkstra(pos, target, inference, env)
            if path and len(path) >= 2:
                next_pos = path[1]
                dx = next_pos[0] - pos[0]
                dy = next_pos[1] - pos[1]
                desired_dir = self.dir_map.get((dx, dy), agent.direction)

                if agent.direction != desired_dir:
                    return self.turn_toward(agent.direction, desired_dir)
                else:
                    return "move_forward"

        # Find a safe old location to move to next
        backtrack_target = self.get_backtrack_target(pos, inference, env)
        if backtrack_target:
            path = self.dijkstra(pos, backtrack_target, inference, env)
            if path and len(path) >= 2:
                next_pos = path[1]
                dx = next_pos[0] - pos[0]
                dy = next_pos[1] - pos[1]
                desired_dir = self.dir_map.get((dx, dy), agent.direction)

                if agent.direction != desired_dir:
                    return self.turn_toward(agent.direction, desired_dir)
                else:
                    return "move_forward"

        # Desperately shoot Wumpus
        if agent.arrows > 0:
            stench_tile = self.find_wumpus_tile(pos, inference)
            
            # If at the stench tile, turn to shoot
            if stench_tile == pos:
                shoot_dir = self.get_wumpus_direction_from_tile(pos, inference)
                if shoot_dir:
                    if agent.direction == shoot_dir:
                        return "shoot"
                    else:
                        return self.turn_toward(agent.direction, shoot_dir)
            
            # Otherwise, move toward it
            if stench_tile:
                path = self.dijkstra(pos, stench_tile, inference, env)
                if path and len(path) >= 2:
                    next_pos = path[1]
                    dx = next_pos[0] - pos[0]
                    dy = next_pos[1] - pos[1]
                    desired_dir = self.dir_map.get((dx, dy), agent.direction)

                    if agent.direction != desired_dir:
                        return self.turn_toward(agent.direction, desired_dir)
                    else:
                        return "move_forward"
                            
        # Stuck and returning to (0, 0)
        if pos != (0, 0):
            path = self.dijkstra(pos, (0, 0), inference, env)
            if path and len(path) >= 2:
                next_pos = path[1]
                dx = next_pos[0] - pos[0]
                dy = next_pos[1] - pos[1]
                desired_dir = self.dir_map.get((dx, dy), agent.direction)

                if agent.direction != desired_dir:
                    return self.turn_toward(agent.direction, desired_dir)
                else:
                    return "move_forward"
        else:
            return "climb"

planner = None

# Make the agent do the next action
def make_next_action(agent, inference, env, actions):
    global planner
    if planner is None:
        planner = Planner(env.size)

    action = planner.plan(agent, inference, env)
    if not action:
        return
    
    actions.append(action)

    if action == "move_forward":
        agent.move_forward(env)
    elif action == "turn_right":
        agent.turn_right()
    elif action == "turn_left":
        agent.turn_left()
    elif action == "grab":
        agent.grab(env)
    elif action == "climb":
        agent.climb(env)
    elif action == "shoot":
        agent.shoot_arrow(env)

# Reset the planner after the game ends
def reset_planner():
    global planner
    if planner is not None:
        planner.reset()
