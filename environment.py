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
        self.wumpus_positions = []
        self.remaining_wumpuses = self.num_wumpus
        
        if generate_random:
            self.place_pits()
            self.place_wumpuses()
            self.place_gold()
            self.update_percepts()
            

    def update_percepts(self):
        # """ Recalculates all stenches and breezes on the map. """
        for x in range(self.size):
            for y in range(self.size):
                self.grid[x][y].breeze = False
                self.grid[x][y].stench = False

        for x in range(self.size):
            for y in range(self.size):
                if self.grid[x][y].has_pit:
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if in_bounds(nx, ny, self.size):
                            self.grid[nx][ny].breeze = True
        
        for wumpus_pos in self.wumpus_positions:
            wx, wy = wumpus_pos
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = wx + dx, wy + dy
                if in_bounds(nx, ny, self.size):
                    self.grid[nx][ny].stench = True

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
                self.wumpus_positions.append([x, y]) # Add position to our list
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
    
    def move_wumpuses(self):
        # """ Moves each wumpus to a valid random adjacent cell. """
        new_positions = []
        occupied = {tuple(pos) for pos in self.wumpus_positions}

        for x, y in self.wumpus_positions:
            self.grid[x][y].has_wumpus = False
            
            valid_moves = [[x, y]]
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if in_bounds(nx, ny, self.size) and not self.grid[nx][ny].has_pit and (nx, ny) not in occupied:
                    valid_moves.append([nx, ny])
            
            new_pos = random.choice(valid_moves)
            new_positions.append(new_pos)
            occupied.add(tuple(new_pos))  # prevent collisions
        
        self.wumpus_positions = new_positions
        for x, y in self.wumpus_positions:
            self.grid[x][y].has_wumpus = True
            
        self.update_percepts() # Recalculate stenches

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
        dirs = [(-1,0),(1,0),(0,-1),(0,1)]
        result = []
        for dx, dy in dirs:
            ni, nj = i + dx, j + dy
            if 0 <= ni < self.size and 0 <= nj < self.size:
                result.append((ni, nj))
        return result
    
    @classmethod
    def read_map_from_file(cls, grid_data, size):
        env = cls(size=size, num_wumpus=0, pit_prob=0, generate_random=False)

        for i in range(size):
            for j in range(size):
                contents = grid_data[size - 1 - i][j]
                if "P" in contents:
                    env.grid[i][j].has_pit = True
                if "W" in contents:
                    env.grid[i][j].has_wumpus = True
                    env.wumpus_positions.append([i, j])
                if "G" in contents:
                    env.grid[i][j].has_gold = True
                    env.grid[i][j].glitter = True

        env.update_percepts()
        env.remaining_wumpuses = len(env.wumpus_positions)

        return env