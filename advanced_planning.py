from agent import Agent
from environment import DIRECTIONS
import heapq

def make_next_action(agent, inference, env, actions):
    x, y = agent.position
    dir_map = {(0, 1): "N", (1, 0): "E", (0, -1): "S", (-1, 0): "W"}
    dir_index = {"N": 0, "E": 1, "S": 2, "W": 3}

    def get_cell_cost(px, py):
        status = inference.infer([px, py])
        if status == "unsafe": return float('inf')
        elif status == "uncertain": return 100
        elif not env.grid[px][py].visited: return 2
        else: return 1

    def run_dijkstra(is_target):
        heap = []
        # Use tuples for heap items because lists are not hashable
        heapq.heappush(heap, (0, tuple(agent.position), []))
        visited = set()

        while heap:
            cost, pos_tuple, path = heapq.heappop(heap)
            if pos_tuple in visited: continue
            visited.add(pos_tuple)
            pos = list(pos_tuple) # Convert back to list for game logic

            if is_target(pos[0], pos[1]):
                return path

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = pos[0] + dx, pos[1] + dy
                if 0 <= nx < env.size and 0 <= ny < env.size:
                    move_cost = get_cell_cost(nx, ny)
                    if move_cost < float('inf'):
                        # Push tuple representation to heap
                        heapq.heappush(heap, (cost + move_cost, (nx, ny), path + [[nx, ny]]))
        return []

    if env.grid[x][y].glitter:
        actions.append("GRAB"); return

    if agent.has_gold:
        if agent.position == [0, 0]:
            actions.append("CLIMB"); return
        path = run_dijkstra(lambda i, j: [i, j] == [0, 0])
    else:
        path = run_dijkstra(lambda i, j: env.grid[i][j].glitter)
        if not path: path = run_dijkstra(lambda i, j: inference.infer([i, j]) == "safe" and not env.grid[i][j].visited)
        if not path: path = run_dijkstra(lambda i, j: inference.infer([i, j]) == "uncertain" and not env.grid[i][j].visited)
        if not path: path = run_dijkstra(lambda i, j: inference.infer([i,j]) == "safe")
            
    if not path:
        actions.append("NO_OP"); return

    next_pos = path[0]
    dx, dy = next_pos[0] - agent.position[0], next_pos[1] - agent.position[1]
    target_dir = dir_map.get((dx, dy))

    if agent.direction != target_dir:
        current_idx, target_idx = dir_index[agent.direction], dir_index[target_dir]
        diff = (target_idx - current_idx + 4) % 4
        if diff == 1: agent.turn_right(), actions.append("TURN_RIGHT")
        elif diff == 3: agent.turn_left(), actions.append("TURN_LEFT")
        elif diff == 2: agent.turn_right(), agent.turn_right(), actions.extend(["TURN_RIGHT", "TURN_RIGHT"])
    else:
        if agent.move_forward(env):
            env.grid[agent.position[0]][agent.position[1]].visited = True
            actions.append("FORWARD")
        else: actions.append("NO_OP")   