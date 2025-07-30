import heapq
from typing import List, Tuple, Set, Optional, Dict
from collections import deque
import random

class PathPlanner:
    """Dijkstra algorithm path-finding"""
    
    def __init__(self, env_size: int):
        self.env_size = env_size
        self.directions = ["N", "E", "S", "W"]
        self.direction_deltas = {
            "N": (0, 1), "E": (1, 0), "S": (0, -1), "W": (-1, 0)
        }
    
    def get_neighbors(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get valid neighboring positions"""
        x, y = pos
        neighbors = []
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.env_size and 0 <= ny < self.env_size:
                neighbors.append((nx, ny))
        return neighbors
    
    def is_safe_to_move(self, pos: Tuple[int, int], inference_engine, env) -> bool:
        """Comprehensive safety check before moving"""
        # Check bounds first
        x, y = pos
        if not (0 <= x < self.env_size and 0 <= y < self.env_size):
            return False
            
        # Check inference engine assessment
        safety = inference_engine.infer(pos)
        if safety == 'unsafe':
            return False
        
        # Double-check with environment if possible
        if hasattr(env, 'grid') and 0 <= x < len(env.grid) and 0 <= y < len(env.grid[0]):
            cell = env.grid[x][y]
            if hasattr(cell, 'has_pit') and cell.has_pit:
                return False
            if hasattr(cell, 'has_wumpus') and cell.has_wumpus:
                return False
        
        return True
    
    def dijkstra_safe_path(self, start: Tuple[int, int], goal: Tuple[int, int], 
                          inference_engine, env, avoid_uncertain: bool = True) -> Optional[List[Tuple[int, int]]]:
        """Enhanced Dijkstra with comprehensive safety checks"""
        if start == goal:
            return [start]
        
        pq = [(0, start)]
        distances = {start: 0}
        previous = {}
        visited = set()
        
        while pq:
            current_cost, current_pos = heapq.heappop(pq)
            
            if current_pos in visited:
                continue
            
            visited.add(current_pos)
            
            if current_pos == goal:
                path = []
                pos = goal
                while pos is not None:
                    path.append(pos)
                    pos = previous.get(pos)
                return path[::-1]
            
            for neighbor in self.get_neighbors(current_pos):
                if neighbor in visited:
                    continue
                
                # Comprehensive safety check
                if not self.is_safe_to_move(neighbor, inference_engine, env):
                    continue
                
                safety = inference_engine.infer(neighbor)
                
                # Skip unsafe cells completely
                if safety == 'unsafe':
                    continue
                
                # Assign costs based on safety
                cell_cost = 1
                if safety == 'uncertain':
                    if avoid_uncertain:
                        cell_cost = 50  # Very high cost but not impossible
                    else:
                        cell_cost = 10
                
                new_cost = current_cost + cell_cost
                
                if neighbor not in distances or new_cost < distances[neighbor]:
                    distances[neighbor] = new_cost
                    previous[neighbor] = current_pos
                    heapq.heappush(pq, (new_cost, neighbor))
        
        return None
    
    def find_safe_exploration_target(self, current_pos: Tuple[int, int], 
                                   inference_engine, visited_cells: Set[Tuple[int, int]], env) -> Optional[Tuple[int, int]]:
        """Find nearest safe unvisited cell with enhanced safety checks"""
        candidates = []
        
        for x in range(self.env_size):
            for y in range(self.env_size):
                pos = (x, y)
                if pos not in visited_cells:
                    if self.is_safe_to_move(pos, inference_engine, env):
                        safety = inference_engine.infer(pos)
                        if safety == 'safe':
                            distance = abs(x - current_pos[0]) + abs(y - current_pos[1])
                            candidates.append((distance, pos))
        
        if candidates:
            candidates.sort()
            return candidates[0][1]
        
        return None

class WumpusWorldPlanner:
    """Enhanced main planning logic with comprehensive game management"""
    
    def __init__(self, env_size: int):
        self.env_size = env_size
        self.path_planner = PathPlanner(env_size)
        self.reset()
        
        self.directions = ["N", "E", "S", "W"]
        self.direction_deltas = {
            "N": (0, 1), "E": (1, 0), "S": (0, -1), "W": (-1, 0)
        }
    
    def reset(self):
        """Reset planner state for a new game"""
        self.visited_cells: Set[Tuple[int, int]] = set()
        self.current_path: List[Tuple[int, int]] = []
        self.strategy = "explore"
        self.gold_location: Optional[Tuple[int, int]] = None
        self.last_position = None
        self.stuck_counter = 0
        self.max_stuck_attempts = 3
        self.game_completed = False
    
    def get_current_position(self, agent) -> Tuple[int, int]:
        """Get agent's current position as tuple"""
        return tuple(agent.position)
    
    def calculate_turn_actions(self, current_dir: str, target_dir: str) -> List[str]:
        """Calculate minimum turns needed to face target direction"""
        directions = self.directions
        current_idx = directions.index(current_dir)
        target_idx = directions.index(target_dir)
        
        diff = (target_idx - current_idx) % 4
        
        if diff == 0:
            return []
        elif diff == 1:
            return ["turn_right"]
        elif diff == 2:
            return ["turn_right", "turn_right"]
        else:
            return ["turn_left"]
    
    def get_direction_to_neighbor(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> str:
        """Get direction needed to move from one position to adjacent position"""
        dx = to_pos[0] - from_pos[0]
        dy = to_pos[1] - from_pos[1]
        
        if dx == 1: return "E"
        elif dx == -1: return "W"
        elif dy == 1: return "N"
        elif dy == -1: return "S"
        else:
            raise ValueError(f"Positions {from_pos} and {to_pos} are not adjacent")
    
    def should_shoot_arrow(self, agent, inference_engine, env) -> Optional[str]:
        """Enhanced arrow shooting logic with better target detection"""
        if agent.arrows <= 0:
            return None
        
        current_pos = self.get_current_position(agent)
        
        for direction in self.directions:
            dx, dy = self.direction_deltas[direction]
            check_pos = current_pos
            wumpus_found = False
            
            # Look along the direction
            for _ in range(self.env_size):
                check_pos = (check_pos[0] + dx, check_pos[1] + dy)
                
                if not (0 <= check_pos[0] < self.env_size and 0 <= check_pos[1] < self.env_size):
                    break
                
                safety = inference_engine.infer(check_pos)
                pos_str = f"{check_pos[0]}{check_pos[1]}"
                
                # Strong indication of wumpus
                if f"W{pos_str}" in inference_engine.kb.facts:
                    wumpus_found = True
                    break
                
                # If we hit a known safe cell, no wumpus beyond
                if safety == 'safe':
                    break
            
            if wumpus_found:
                return direction
        
        return None
    
    def update_strategy(self, agent, env, percepts):
        """Enhanced strategy update with comprehensive state management"""
        current_pos = self.get_current_position(agent)
        
        # Check for stuck condition
        if self.last_position == current_pos:
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0
        self.last_position = current_pos
        
        # CRITICAL: Check for gold in current cell and ensure proper grabbing
        if 'G' in percepts and not agent.has_gold:
            self.gold_location = current_pos
            self.strategy = "collect"
            print(f"GOLD DETECTED AT {current_pos}")
            return
        
        # CRITICAL: If at home position and has gold, climb out (HIGHEST PRIORITY)
        if current_pos == (0, 0) and agent.has_gold and not self.game_completed:
            self.strategy = "climb"
            self.game_completed = True
            print(f"READY TO CLIMB OUT WITH GOLD")
            return
        
        # If agent has gold but not at home, return home
        if agent.has_gold and not self.game_completed:
            self.strategy = "return"
            return
        
        # If game is completed, stay put
        if self.game_completed:
            self.strategy = "complete"
            return
        
        # Otherwise, continue exploring
        if self.strategy not in ["return", "climb", "complete"]:
            self.strategy = "explore"
    
    def get_safe_fallback_action(self, agent, inference_engine, env) -> Optional[str]:
        """Get a safe fallback action when stuck"""
        current_pos = self.get_current_position(agent)
        
        # Try each direction to find a safe move
        for direction in ["N", "E", "S", "W"]:
            dx, dy = self.direction_deltas[direction]
            next_pos = (current_pos[0] + dx, current_pos[1] + dy)
            
            if (0 <= next_pos[0] < self.env_size and 0 <= next_pos[1] < self.env_size):
                if self.path_planner.is_safe_to_move(next_pos, inference_engine, env):
                    safety = inference_engine.infer(next_pos)
                    if safety in ['safe']:  # Only very safe moves
                        if agent.direction != direction:
                            turn_actions = self.calculate_turn_actions(agent.direction, direction)
                            if turn_actions:
                                return turn_actions[0]
                        return "move_forward"
        
        # If no safe moves, just turn
        return "turn_right"
    
    def plan_next_action(self, agent, inference_engine, env, percepts) -> Optional[str]:
        """Enhanced main planning logic with comprehensive error handling"""
        current_pos = self.get_current_position(agent)
        self.visited_cells.add(current_pos)
        
        # Update strategy based on current situation
        self.update_strategy(agent, env, percepts)
        
        # Handle different strategies
        if self.strategy == "collect":
            return "grab"
        
        elif self.strategy == "climb":
            if current_pos == (0, 0) and agent.has_gold:
                print(f"CLIMBING OUT WITH GOLD")
                return "climb"
            else:
                # Something went wrong, reset to return strategy
                print(f"WARNING: Expected to be at (0,0) with gold, but at {current_pos}")
                self.strategy = "return"
        
        elif self.strategy == "complete":
            # Game is done, do nothing
            return None
        
        elif self.strategy == "return":
            target = (0, 0)
            path = self.path_planner.dijkstra_safe_path(current_pos, target, inference_engine, env)
            
            if path and len(path) > 1:
                next_pos = path[1]
                
                # Verify next position is actually safe
                if not self.path_planner.is_safe_to_move(next_pos, inference_engine, env):
                    print(f"WARNING: Planned move to {next_pos} is not safe")
                    return self.get_safe_fallback_action(agent, inference_engine, env)
                
                target_direction = self.get_direction_to_neighbor(current_pos, next_pos)
                
                if agent.direction != target_direction:
                    turn_actions = self.calculate_turn_actions(agent.direction, target_direction)
                    if turn_actions:
                        return turn_actions[0]
                
                return "move_forward"
            else:
                print(f"ERROR: No path to home from {current_pos}")
                return self.get_safe_fallback_action(agent, inference_engine, env)
        
        elif self.strategy == "explore":
            # Check if we should shoot an arrow
            shoot_direction = self.should_shoot_arrow(agent, inference_engine, env)
            if shoot_direction and agent.direction == shoot_direction:
                return "shoot"
            elif shoot_direction:
                turn_actions = self.calculate_turn_actions(agent.direction, shoot_direction)
                if turn_actions:
                    return turn_actions[0]
            
            # Find next exploration target
            target = self.path_planner.find_safe_exploration_target(
                current_pos, inference_engine, self.visited_cells, env
            )
            
            if target:
                path = self.path_planner.dijkstra_safe_path(current_pos, target, inference_engine, env)
                
                if path and len(path) > 1:
                    next_pos = path[1]
                    
                    # Verify safety before moving
                    if not self.path_planner.is_safe_to_move(next_pos, inference_engine, env):
                        print(f"WARNING: Planned exploration move to {next_pos} is not safe")
                        return self.get_safe_fallback_action(agent, inference_engine, env)
                    
                    target_direction = self.get_direction_to_neighbor(current_pos, next_pos)
                    
                    if agent.direction != target_direction:
                        turn_actions = self.calculate_turn_actions(agent.direction, target_direction)
                        if turn_actions:
                            return turn_actions[0]
                    
                    return "move_forward"
            
            # If no safe exploration targets, try uncertain cells with caution
            if self.stuck_counter < self.max_stuck_attempts:
                for x in range(self.env_size):
                    for y in range(self.env_size):
                        pos = (x, y)
                        if pos not in self.visited_cells:
                            safety = inference_engine.infer(pos)
                            if safety == 'uncertain':
                                path = self.path_planner.dijkstra_safe_path(
                                    current_pos, pos, inference_engine, env, avoid_uncertain=False
                                )
                                if path and len(path) > 1:
                                    next_pos = path[1]
                                    if self.path_planner.is_safe_to_move(next_pos, inference_engine, env):
                                        target_direction = self.get_direction_to_neighbor(current_pos, next_pos)
                                        
                                        if agent.direction != target_direction:
                                            turn_actions = self.calculate_turn_actions(agent.direction, target_direction)
                                            if turn_actions:
                                                return turn_actions[0]
                                        
                                        return "move_forward"
        
        # Ultimate fallback
        return self.get_safe_fallback_action(agent, inference_engine, env)

# Global planner instance
planner = None

def make_next_action(agent, inference_engine, env, actions):
    """Enhanced main function with comprehensive error handling and logging"""
    global planner
    
    # Initialize planner if needed
    if planner is None:
        planner = WumpusWorldPlanner(env.size)
        print(f"WUMPUS WORLD AGENT INITIALIZED FOR {env.size}x{env.size} MAP")
    
    # Check if we need to reset the planner for a new game
    
    current_pos = tuple(agent.position)
    if (current_pos == (0, 0) and not agent.has_gold and 
        planner.game_completed and planner.strategy == "complete"):
        print(f"NEW GAME DETECTED - RESETTING PLANNER")
        planner.reset()
    
    # Get current percepts
    percepts = env.get_percepts()
    
    # Safety check: verify agent position is safe
    if hasattr(env, 'grid'):
        x, y = current_pos
        if 0 <= x < len(env.grid) and 0 <= y < len(env.grid[0]):
            cell = env.grid[x][y]
            if hasattr(cell, 'has_pit') and cell.has_pit:
                print(f"CRITICAL ERROR: AGENT AT {current_pos} IS IN A PIT")
                return None
            if hasattr(cell, 'has_wumpus') and cell.has_wumpus:
                print(f"CRITICAL ERROR: AGENT AT {current_pos} IS WITH WUMPUS")
                return None
    
    # Plan next action
    next_action = planner.plan_next_action(agent, inference_engine, env, percepts)
    
    if next_action:
        actions.append(next_action)
        
        # Execute the action with error checking
        try:
            if next_action == "move_forward":
                old_pos = tuple(agent.position)
                success = agent.move_forward(env)
                new_pos = tuple(agent.position)
                if not success:
                    print(f"WARNING: Move forward failed from {old_pos}")
                elif old_pos == new_pos:
                    print(f"WARNING: Agent didn't move from {old_pos}")
                    
            elif next_action == "turn_left":
                agent.turn_left()
            elif next_action == "turn_right":
                agent.turn_right()
            elif next_action == "grab":
                success = agent.grab(env)
                if success:
                    print(f"GOLD ACQUIRED AT {current_pos}")
                else:
                    print(f"ERROR: Failed to grab gold at {current_pos}")
            elif next_action == "shoot":
                success = agent.shoot_arrow(env)
                if success:
                    print(f"WUMPUS ELIMINATED")
                else:
                    print(f"ARROW MISSED")
            elif next_action == "climb":
                print(f"MISSION COMPLETE: CLIMBING OUT AT {current_pos}")
                if agent.has_gold:
                    print(f"VICTORY: MAXIMUM SCORE ACHIEVED")
                else:
                    print(f"MISSION FAILED: NO GOLD ACQUIRED")
                
        except Exception as e:
            print(f"ERROR EXECUTING ACTION {next_action}: {e}")
            return None
        
        # Check for win condition
        if agent.has_gold and current_pos == (0, 0) and next_action == "climb":
            print(f"MISSION ACCOMPLISHED: GOLD RETRIEVED AND AGENT ESCAPED")
    else:
        print(f"ERROR: No action planned for position {current_pos}")
    
    return next_action


def reset_planner():
    """Function to reset the global planner - call this when starting a new game"""
    global planner
    if planner is not None:
        planner.reset()
        print(f"PLANNER RESET FOR NEW GAME")