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

    # Shoot Wumpus
    def find_wumpus_direction(self, pos, inference, agent_dir, desperate=False) -> Optional[str]:
        if not desperate:
            return None
        
        for dir in self.directions:
            dx, dy = self.direction_deltas[dir]
            x, y = pos
            for _ in range(self.env_size):
                x += dx
                y += dy
                if not (0 <= x < self.env_size and 0 <= y < self.env_size):
                    break
                if f"W{x}{y}" in inference.kb.facts:
                    if agent_dir == dir:
                        return "shoot"
                    else:
                        return self.turn_toward(agent_dir, dir)
        return None

    # The plan of the agent
    def plan(self, agent, inference, env) -> Optional[str]:
        pos = tuple(agent.position)
        self.visited.add(pos)

        percepts = env.get_percepts()
        if 'G' in percepts and not agent.has_gold:
            return "grab"

        if agent.has_gold:
            self.returning = True

        if self.returning and pos == (0, 0):
            return "climb"

        target = (0, 0) if self.returning else self.get_target(pos, inference, env)
        if not target:
            return "turn_right"

        path = self.dijkstra(pos, target, inference, env)
        if not path or len(path) < 2:
            return "turn_right"
        
        target = (0, 0) if self.returning else self.get_target(pos, inference, env)
        if not target:
            if agent.arrows > 0:
                kill_wumpus_desperate = self.find_wumpus_direction(pos, inference, agent.direction, desperate=True)
                if kill_wumpus_desperate:
                    return kill_wumpus_desperate
            return "turn_right"

        next_pos = path[1]
        dx = next_pos[0] - pos[0]
        dy = next_pos[1] - pos[1]
        desired_dir = self.dir_map.get((dx, dy), agent.direction)

        if agent.direction != desired_dir:
            return self.turn_toward(agent.direction, desired_dir)
        else:
            return "move_forward"
        
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
