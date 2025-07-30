from collections import deque
from environment import in_bounds
import heapq

def dijkstra(start, goals, grid):
    size = len(grid)
    visited = set()
    heap = [(0, start, [])]
    while heap:
        cost, current, path = heapq.heappop(heap)
        if current in visited:
            continue
        visited.add(current)
        path = path + [current]
        if current in goals:
            return path
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = current[0] + dx, current[1] + dy
            if in_bounds(nx, ny, size) and grid[nx][ny].visited:
                heapq.heappush(heap, (cost + 1, (nx, ny), path))
    return None

def find_candidates(env, inference_engine, safe_only=True):
    size = env.size
    visited = {(i, j) for i in range(size) for j in range(size) if env.grid[i][j].visited}
    candidates = set()
    for x, y in visited:
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = x + dx, y + dy
            if not in_bounds(nx, ny, size):
                continue
            if env.grid[nx][ny].visited:
                continue
            status = inference_engine.infer((nx, ny))
            if safe_only and status == "safe":
                candidates.add((nx, ny))
            elif not safe_only and status == "uncertain":
                candidates.add((nx, ny))
    return candidates

def to_actions(agent, path):
    actions = []
    dir_map = {"N": (0, 1), "E": (1, 0), "S": (0, -1), "W": (-1, 0)}
    reverse_dir_map = {v: k for k, v in dir_map.items()}
    for next_pos in path[1:]:
        dx = next_pos[0] - agent.position[0]
        dy = next_pos[1] - agent.position[1]
        desired_dir = reverse_dir_map.get((dx, dy))
        if desired_dir is None:
            continue
        # Turn until facing desired_dir
        while agent.direction != desired_dir:
            actions.append("turn_left")
            idx = (["N", "E", "S", "W"].index(agent.direction) - 1) % 4
            agent.direction = ["N", "E", "S", "W"][idx]
        actions.append("move_forward")
        agent.position = list(next_pos)
    return actions

def make_next_action(agent, ie, env, actions):
    x, y = agent.position
    cell = env.grid[x][y]
    cell.visited = True

    if cell.has_gold:
        actions.append("grab")
        agent.grab(env)

    if agent.has_gold:
        path = dijkstra((x, y), {(0, 0)}, env.grid)
        if path:
            actions.extend(to_actions(agent, path))
            if agent.position == [0, 0]:
                actions.append("climb")
        return

    # Step 1: Try to reach a safe unvisited cell
    safe_targets = find_candidates(env, ie, safe_only=True)
    if safe_targets:
        path = dijkstra((x, y), safe_targets, env.grid)
        if path:
            actions.extend(to_actions(agent, path))
            return

    # Step 2: Try to reach an uncertain unvisited cell
    uncertain_targets = find_candidates(env, ie, safe_only=False)
    if uncertain_targets:
        path = dijkstra((x, y), uncertain_targets, env.grid)
        if path:
            actions.extend(to_actions(agent, path))
            return

    # Step 3: No action (stay still)
    return
