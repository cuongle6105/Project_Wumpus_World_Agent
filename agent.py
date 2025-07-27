from environment import in_bounds
from environment import DIRECTIONS
class Agent:
    def __init__(self):
        self.position = [0, 0]
        self.direction = "E"
        self.has_gold = False
        self.actions = []

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