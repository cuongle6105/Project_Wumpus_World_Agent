from agent import Agent
from environment import DIRECTIONS
import heapq

def make_next_action(agent, inference, env, actions):
    x, y = agent.position
    # dir_map = {(-1, 0): "N", (0, 1): "E", (1, 0): "S", (0, -1): "W"}
    dir_map = {(0, 1): "N", (1, 0): "E", (0, -1): "S", (-1, 0): "W"}
    dir_index = {"N": 0, "E": 1, "S": 2, "W": 3}
    env.grid[x][y].visited = True

    # Estimate risk/cost for entering a cell
    def get_cell_cost(px, py):
        
        status = inference.infer([px, py])
        # print(f"Inferring cell {px}, {py} status: {status}")
        
        if status == "unsafe":
            return float('inf')  # completely avoid
        elif status == "uncertain":
            return 1000  # high penalty
        elif not env.grid[px][py].visited:
            return 1  # unvisited but inferred safe
        else:
            return 2  # visited and safe
    def is_adjacent_to_visited(i, j):
        for x in range(env.size):
            for y in range(env.size):
                if env.grid[x][y].visited:
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < env.size and 0 <= ny < env.size:
                            if nx == i and ny == j:
                                return True
        return False

    # Dijkstra search with customizable target
    def run_dijkstra(is_target):
        heap = []
        heapq.heappush(heap, (0, tuple(agent.position), []))
        visited = set()

        while heap:
            cost, pos_tuple, path = heapq.heappop(heap)
            if pos_tuple in visited:
                continue
            visited.add(pos_tuple)
            pos = list(pos_tuple)

            if is_target(pos[0], pos[1]):
                return path

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = pos[0] + dx, pos[1] + dy
                if 0 <= nx < env.size and 0 <= ny < env.size:
                    move_cost = get_cell_cost(nx, ny)
                    if move_cost < float('inf'):
                        heapq.heappush(heap, (cost + move_cost, (nx, ny), path + [[nx, ny]]))
        return []
    
    def target_safe_unvisited_adjacent(i, j):
        result = (
            inference.infer([i, j]) == "safe" and 
            not env.grid[i][j].visited and 
            is_adjacent_to_visited(i, j)
        )
        if result:
            print(f"Checking cell ({i}, {j}): {result}")
        return result
    
    def target_uncertained_unvisited_adjacent(i, j):
        result = (
            inference.infer([i, j]) == "uncertain" and 
            not env.grid[i][j].visited and 
            is_adjacent_to_visited(i, j)
        )
        if result:
            print(f"Checking cell ({i}, {j}): {result}")
        # print(f"Checking cell ({i}, {j}): {result}")
        return result
    

    

    # 1. If agent perceives gold (glitter), grab it
    if 'G' in env.get_percepts() and not agent.has_gold:
        actions.append("GRAB")
        agent.has_gold = True
        env.grid[x][y].has_gold = False
        env.grid[x][y].glitter = False
        return

    # 2. If agent has gold, return to start and climb out
    if agent.has_gold:
        if agent.position == [0, 0]:
            actions.append("CLIMB")
            return
        path = run_dijkstra(lambda i, j: [i, j] == [0, 0])

    # 3. Otherwise, explore safe & unvisited cells
    else:
        # path = run_dijkstra(lambda i, j: inference.infer([i, j]) == "safe" and not env.grid[i][j].visited)
        path = run_dijkstra(target_safe_unvisited_adjacent)
        print("Path found to safe unvisited adjacent cells:", path)
        if not path:
            path = run_dijkstra(target_uncertained_unvisited_adjacent)
            print("Path found to uncertain unvisited adjacent cells:", path)
        #     # 4. If nothing safe/unvisited, explore safe (even visited) to keep moving
        #     path = run_dijkstra(lambda i, j: inference.infer([i, j]) == "safe")
        # if not path:
        #     # 5. As last resort, explore uncertain cells that are unvisited
        #     path = run_dijkstra(lambda i, j: inference.infer([i, j]) == "uncertain" and not env.grid[i][j].visited)

    # 6. If no path is found, agent does nothing
    if not path:
        actions.append("NO_OP")
        return

    # Move toward first step in path
    next_pos = path[0]
    dx, dy = next_pos[0] - x, next_pos[1] - y
    target_dir = dir_map.get((dx, dy))

    if agent.direction != target_dir:
        current_idx = dir_index[agent.direction]
        target_idx = dir_index[target_dir]
        diff = (target_idx - current_idx + 4) % 4
        if diff == 1:
            agent.turn_right()
            actions.append("TURN_RIGHT")
        elif diff == 3:
            agent.turn_left()
            actions.append("TURN_LEFT")
        elif diff == 2:
            agent.turn_right()
            agent.turn_right()
            actions.extend(["TURN_RIGHT", "TURN_RIGHT"])
        return  # Only turn this step

    # Move forward
    if agent.move_forward(env):
        new_x, new_y = agent.position
        env.grid[new_x][new_y].visited = True
        actions.append("FORWARD")
    else:
        actions.append("NO_OP")
