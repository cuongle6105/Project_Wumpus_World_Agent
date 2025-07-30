from environment import in_bounds
from environment import DIRECTIONS
class Agent:
    def __init__(self):
        self.position = [0, 0]
        self.direction = "E"
        self.has_gold = False
        self.actions = []
        self.arrows = 1
    
    def reset(self):
        self.position = [0, 0]
        self.direction = "E"
        self.has_gold = False
        self.actions = []
        self.arrows = 1

    def shoot_arrow(self, env):
        if self.arrows <= 0:
            return False  # No arrows left
        self.arrows -= 1
        x, y = self.position
        direction = self.direction

        dx, dy = {"N": (0, 1), "E": (1, 0), "S": (0, -1), "W": (-1, 0)}[direction]
        x += dx
        y += dy

        while in_bounds(x, y, env.size):
            cell = env.grid[x][y]
            if cell.has_wumpus:
                cell.has_wumpus = False
                env.remaining_wumpuses -= 1  # Update count in environment
                return True  # Wumpus killed
            x += dx
            y += dy
        return False  # Arrow missed


    def move_forward(self, env):
        dx, dy = {"N": (0, 1), "E": (1, 0), "S": (0, -1), "W": (-1, 0)}[self.direction]
        new_x = self.position[0] + dx
        new_y = self.position[1] + dy
        if in_bounds(new_x, new_y, env.size):
            self.position = [new_x, new_y]
            env.grid[new_x][new_y].visited = True
            return True
        return False

    def turn_left(self):
        idx = (DIRECTIONS.index(self.direction) - 1) % 4
        self.direction = DIRECTIONS[idx]

    def turn_right(self):
        idx = (DIRECTIONS.index(self.direction) + 1) % 4
        self.direction = DIRECTIONS[idx]

    def grab(self, env):
        x, y = self.position
        if env.grid[x][y].has_gold:
            self.has_gold = True
            env.grid[x][y].has_gold = False
            return True
        return False
    
    def climb(self, env):
        x, y = self.position
        if (x, y) == (0, 0) and self.has_gold:
            return True
        return False
        