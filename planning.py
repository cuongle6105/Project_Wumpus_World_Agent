from agent import Agent
from environment import DIRECTIONS
import heapq

def make_next_action(agent, inference, env, actions):
    x, y = agent.position

    dir_map = {(0, 1): "N", (1, 0): "E", (0, -1): "S", (-1, 0): "W"}
    dir_index = {"N": 0, "E": 1, "S": 2, "W": 3}

    # Function to get the cost of moving to a cell
    def get_cell_cost(x, y):
        status = inference.infer((x, y))
        if status == "unsafe":
            return float('inf')
        elif status == "uncertain":
            return 100
        elif not env.grid[x][y].visited:
            return 2
        else:
            return 1

    # Dijkstra to find a path to the target position
    def run_dijkstra(target_pos):
        heap = []
        heapq.heappush(heap, (0, agent.position, []))
        visited = set()

        while heap:
            cost, (x, y), path = heapq.heappop(heap)
            if (x, y) in visited:
                continue
            visited.add((x, y))

            if target_pos(x, y):
                return path

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < env.size and 0 <= ny < env.size:
                    move_cost = get_cell_cost(nx, ny)
                    if move_cost < float('inf'):
                        heapq.heappush(heap, (cost + move_cost, (nx, ny), path + [(nx, ny)]))
        return []

    # See gold -> grab it
    if env.grid[x][y].glitter:
        agent.grab(env)
        actions.append("GRAB")
        return

    # Plan path
    # If has gold and at (0, 0), climb out
    if agent.has_gold:
        if agent.position == (0, 0):
            agent.climb(env)
            actions.append("CLIMB")
            return
        path = run_dijkstra(lambda i, j: (i, j) == (0, 0))
    else:
        # Priority: glitter -> safe + unvisited -> safe -> uncertain + unvisited
        path = run_dijkstra(lambda i, j: env.grid[i][j].glitter)
        if not path:
            path = run_dijkstra(lambda i, j: inference.infer((i, j)) == "safe" and not env.grid[i][j].visited)
        if not path:
            path = run_dijkstra(lambda i, j: inference.infer((i, j)) == "safe")
        if not path:
            path = run_dijkstra(lambda i, j: inference.infer((i, j)) == "uncertain" and not env.grid[i][j].visited)

    # Shoot if Wumpus if deperate and has arrows


    # Move towards the next position in the path
    next_pos = path[0]
    dx = next_pos[0] - agent.position[0]
    dy = next_pos[1] - agent.position[1]
    target_dir = dir_map.get((dx, dy))

    if not target_dir:
        actions.append("NO_OP")
        return

    if agent.direction != target_dir:
        current_idx = dir_index[agent.direction]
        target_idx = dir_index[target_dir]
        diff = (target_idx - current_idx) % 4

        if diff == 1:
            agent.turn_right()
            actions.append("TURN_RIGHT")
        elif diff == 3:
            agent.turn_left()
            actions.append("TURN_LEFT")
        else:
            agent.turn_left()
            agent.turn_left()
            actions.extend(["TURN_LEFT", "TURN_LEFT"])
    else:
        if agent.move_forward(env):
            env.grid[agent.position[0]][agent.position[1]].visited = True
            actions.append("FORWARD")
        else:
            actions.append("NO_OP")
