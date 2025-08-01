import random

DIRECTIONS = ["N", "E", "S", "W"]

def in_bounds(x, y, size):
    return 0 <= x < size and 0 <= y < size

class Cell:
    def __init__(self):
        self.has_pit = False
        self.has_wumpus = False
        self.has_gold = False
        self.visited = False
        self.breeze = False
        self.stench = False
        self.glitter = False

class Environment:
    def __init__(self, size=8, num_wumpus=2, pit_prob=0.2, generate_random=True):
        self.size = size
        self.grid = [[Cell() for _ in range(size)] for _ in range(size)]
        self.agent_pos = [0, 0]
        self.agent_dir = "E"
        self.num_wumpus = num_wumpus
        self.pit_prob = pit_prob
        self.remaining_wumpuses = num_wumpus

        # Only generate random environment if requested
        if generate_random:
            self.place_pits()
            self.place_wumpuses()
            self.place_gold()

    def place_pits(self):
        for x in range(self.size):
            for y in range(self.size):
                if (x, y) != (0, 0) and random.random() < self.pit_prob:
                    self.grid[x][y].has_pit = True
                    for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                        nx, ny = x + dx, y + dy
                        if in_bounds(nx, ny, self.size):
                            self.grid[nx][ny].breeze = True

    def place_wumpuses(self):
        placed = 0
        while placed < self.num_wumpus:
            x, y = random.randint(0, self.size-1), random.randint(0, self.size-1)
            if (x, y) != (0, 0) and not self.grid[x][y].has_pit and not self.grid[x][y].has_wumpus:
                self.grid[x][y].has_wumpus = True
                for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                    nx, ny = x + dx, y + dy
                    if in_bounds(nx, ny, self.size):
                        self.grid[nx][ny].stench = True
                placed += 1

    def place_gold(self):
        while True:
            x, y = random.randint(0, self.size-1), random.randint(0, self.size-1)
            if not self.grid[x][y].has_pit and not self.grid[x][y].has_wumpus:
                self.grid[x][y].has_gold = True
                self.grid[x][y].glitter = True
                break

    def get_percepts(self):
        x, y = self.agent_pos
        cell = self.grid[x][y]
        percepts = set()
        if cell.breeze:
            percepts.add('B')
        if cell.glitter:
            percepts.add('G')
        if cell.stench:
            percepts.add('S')
        return percepts

    def adjacent(self, i, j):
        directions = [(-1,0), (1,0), (0,-1), (0,1)]
        result = []
        for dx, dy in directions:
            ni, nj = i + dx, j + dy
            if 0 <= ni < self.size and 0 <= nj < self.size:
                result.append((ni, nj))
        return result

    @classmethod
    def from_grid(cls, grid_data, size):
        env = cls(size, num_wumpus=0, pit_prob=0, generate_random=False)

        for i in range(size):
            for j in range(size):
                contents = grid_data[size - 1 - i][j]
                if "P" in contents:
                    env.grid[i][j].has_pit = True
                if "W" in contents:
                    env.grid[i][j].has_wumpus = True
                if "G" in contents:
                    env.grid[i][j].has_gold = True
                    env.grid[i][j].glitter = True

        for i in range(size):
            for j in range(size):
                if env.grid[i][j].has_pit:
                    for ni, nj in env.adjacent(i, j):
                        env.grid[ni][nj].breeze = True
                if env.grid[i][j].has_wumpus:
                    for ni, nj in env.adjacent(i, j):
                        env.grid[ni][nj].stench = True
        return env
