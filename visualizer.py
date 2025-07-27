
import pygame
import os
from environment import Environment
from agent import Agent

CELL_SIZE = 64
MARGIN = 2
ICON_SIZE = 48

class Visualizer:
    def __init__(self, env: Environment, agent: Agent):
        self.env = env
        self.agent = agent
        self.shot_arrow = None
        # load & scale images
        self.images = {k: pygame.transform.scale(pygame.image.load(f"images/{'pit' if k=='pit' else k}.png"),
                                                (ICON_SIZE, ICON_SIZE))
                       for k in ("agent","arrow","shot","breeze","pit","stench","treasure","wumpus")}
        for k in ("agent","pit","wumpus"):
            self.images[k] = pygame.transform.scale(self.images[k],
                (CELL_SIZE - MARGIN*2, CELL_SIZE - MARGIN*2))
        self.images["arrow"] = pygame.transform.scale(self.images["arrow"], (24, 24))
        self.images["shot"] = pygame.transform.scale(self.images["shot"], (24, 24))

    def draw(self, surface):
        for x in range(self.env.size):
            for y in range(self.env.size):
                cell = self.env.grid[x][y]
                px, py = x * CELL_SIZE + MARGIN, (self.env.size - 1 - y) * CELL_SIZE + MARGIN
                rect = pygame.Rect(px, py, CELL_SIZE - MARGIN * 2, CELL_SIZE - MARGIN * 2)
                pygame.draw.rect(surface, (150,150,150) if cell.visited else (60,60,60), rect)
                if cell.has_pit:
                    surface.blit(self.images["pit"], rect); continue
                if cell.has_wumpus:
                    surface.blit(self.images["wumpus"], rect); continue
                center = rect.center
                if cell.glitter:
                    surface.blit(self.images["treasure"], self.images["treasure"].get_rect(center=center))
                if cell.stench:
                    surface.blit(self.images["stench"], self.images["stench"].get_rect(center=center))
                if cell.breeze:
                    surface.blit(self.images["breeze"], self.images["breeze"].get_rect(center=center))

        # draw agent last
        ax, ay = self.agent.position
        rect = pygame.Rect(ax * CELL_SIZE + MARGIN, (self.env.size - 1 - ay) * CELL_SIZE + MARGIN,
                           CELL_SIZE - MARGIN * 2, CELL_SIZE - MARGIN * 2)
        surface.blit(self.images["agent"], rect)

        # Draw direction arrow
        dir_map = {"N": 90, "E": 0, "S": -90, "W": 180}
        angle = dir_map.get(self.agent.direction, 0)
        rotated_arrow = pygame.transform.rotate(self.images["arrow"], angle)
        arrow_rect = rotated_arrow.get_rect(center=rect.center)
        surface.blit(rotated_arrow, arrow_rect)

        # Draw flying shot if active
        if self.shot_arrow:
            x, y, direction = self.shot_arrow
            if 0 <= x < self.env.size and 0 <= y < self.env.size:
                angle = dir_map.get(direction, 0)
                rotated_shot = pygame.transform.rotate(self.images["shot"], angle)
                px = x * CELL_SIZE + CELL_SIZE // 2
                py = (self.env.size - 1 - y) * CELL_SIZE + CELL_SIZE // 2
                shot_rect = rotated_shot.get_rect(center=(px, py))
                surface.blit(rotated_shot, shot_rect)

                # Check for wumpus hit
                cell = self.env.grid[x][y]
                if cell.has_wumpus:
                    cell.has_wumpus = False
                    self.shot_arrow = None
                    return  # Skip moving the arrow further

                # Move arrow
                if direction == "N":
                    y += 1
                elif direction == "S":
                    y -= 1
                elif direction == "E":
                    x += 1
                elif direction == "W":
                    x -= 1

                if 0 <= x < self.env.size and 0 <= y < self.env.size:
                    self.shot_arrow = (x, y, direction)
                else:
                    self.shot_arrow = None

    def fire_arrow(self):
        if not self.shot_arrow:
            x, y = self.agent.position
            self.shot_arrow = (x, y, self.agent.direction)
