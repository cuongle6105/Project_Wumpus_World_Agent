import pygame
import sys
from environment import Environment
from agent import Agent
from visualizer import Visualizer
from inference import InferenceEngine
from planning import make_next_action, reset_planner
from advanced_planning import make_advanced_action, make_random_action

pygame.init()
font = pygame.font.SysFont("Arial", 18)
small_font = pygame.font.SysFont("Arial", 14)

info = pygame.display.Info()
DISPLAY_WIDTH, DISPLAY_HEIGHT = info.current_w - 70, info.current_h - 70
PANEL_WIDTH = 340

# Input settings
def calculate_cell_size(n):
    return min((DISPLAY_WIDTH - PANEL_WIDTH) // n, DISPLAY_HEIGHT // n)

map_size = 8
CELL_SIZE = calculate_cell_size(map_size)
WINDOW_WIDTH = CELL_SIZE * map_size + PANEL_WIDTH
WINDOW_HEIGHT = max(CELL_SIZE * map_size, 600)
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Wumpus World Game")
clock = pygame.time.Clock()

# Game state variables
wumpus_count = 2
pit_ratio = 0.2
advanced_setting = False

def draw_button(surface, rect, text, active):
    color = (0, 255, 0) if active else (200, 200, 200)
    pygame.draw.rect(surface, color, rect)
    pygame.draw.rect(surface, (0, 0, 0), rect, 2)
    text_surf = font.render(text, True, (0, 0, 0))
    text_rect = text_surf.get_rect(center=rect.center)
    surface.blit(text_surf, text_rect)

def draw_percepts_table(surface, x, y, percepts):
    pygame.draw.rect(surface, (255, 255, 255), (x, y, PANEL_WIDTH - 20, 100))
    pygame.draw.rect(surface, (0, 0, 0), (x, y, PANEL_WIDTH - 20, 100), 2)
    cell_label = font.render("Cell: ({}, {})".format(*agent.position), True, (0, 0, 0))
    surface.blit(cell_label, (x + 10, y + 10))
    percept_text = []
    if "B" in percepts:
        percept_text.append("breeze")
    if  "S" in percepts:
        percept_text.append("stench")
    if  "G" in percepts:
        percept_text.append("grab treasure")
    percept_str = ", ".join(percept_text) if percept_text else "none"
    percept_label = small_font.render("Percepts: " + percept_str, True, (0, 0, 0))
    surface.blit(percept_label, (x + 10, y + 40))

def draw_score(surface, x, y, score):
    score_label = font.render("Score: {}".format(score), True, (0, 0, 0))
    surface.blit(score_label, (x, y))

input_texts = {"size": "8", "wumpus": "2", "pit": "0.2"}
input_boxes = {}
active_input = None
error_message = ""

# Buttons (will be updated dynamically)
control_buttons = {}
setting_buttons = {}

def draw_inputs(surface, panel_left):
    surface.blit(font.render("Map Size:", True, (0, 0, 0)), (panel_left + 20, 80))
    surface.blit(font.render("Wumpus:", True, (0, 0, 0)), (panel_left + 20, 120))
    surface.blit(font.render("Pit Ratio:", True, (0, 0, 0)), (panel_left + 20, 160))

    for key in input_boxes:
        pygame.draw.rect(surface, (255, 255, 255), input_boxes[key])
        pygame.draw.rect(surface, (255, 0, 0) if active_input == key else (0, 0, 0), input_boxes[key], 2)
        text = font.render(input_texts[key], True, (0, 0, 0))
        surface.blit(text, (input_boxes[key].x + 5, input_boxes[key].y + 5))

def reset_game_preset(preset_map=None):
    global env, agent, vis, score, step_count, percepts, game_end
    env = Environment.from_grid(preset_map["grid"], preset_map["size"])
    env.grid[0][0].has_pit = False
    env.grid[0][0].has_wumpus = False
    agent = Agent()
    vis = Visualizer(env, agent)
    score = 0
    step_count = 0
    game_end = False
    percepts = env.get_percepts()
    reset_planner()

def reset_game():
    global env, agent, vis, score, step_count, percepts, game_end
    env = Environment(size=map_size, num_wumpus=wumpus_count, pit_prob=pit_ratio)
    env.grid[0][0].has_pit = False
    env.grid[0][0].has_wumpus = False
    agent = Agent()
    vis = Visualizer(env, agent)
    score = 0
    step_count = 0
    game_end = False
    percepts = env.get_percepts()
    reset_planner()

# Initial setup
auto_play = False
paused = False
score = 0
step_count = 0
game_end = False
game_won = False
game_lose = False
game_tie = False
inference_engine = InferenceEngine()

reset_game()

while True:
    clock.tick(5)
    panel_left = CELL_SIZE * map_size
    WINDOW_WIDTH = panel_left + PANEL_WIDTH
    WINDOW_HEIGHT = max(CELL_SIZE * map_size, 600)
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    screen.fill((255, 255, 255))

    # Update button and input positions
    setting_buttons = {
        "basic": pygame.Rect(panel_left + 20, 20, 120, 35),
        "advanced": pygame.Rect(panel_left + 150, 20, 120, 35)
    }
    input_boxes = {
        "size": pygame.Rect(panel_left + 120, 80, 60, 30),
        "wumpus": pygame.Rect(panel_left + 120, 120, 60, 30),
        "pit": pygame.Rect(panel_left + 120, 160, 60, 30)
    }
    control_buttons = {
        "create": pygame.Rect(panel_left + 20, 200, 120, 35),
        "play": pygame.Rect(panel_left + 20, 250, 80, 40),
        "pause": pygame.Rect(panel_left + 110, 250, 80, 40),
        "restart": pygame.Rect(panel_left + 200, 250, 80, 40)
    }
    map_buttons = {
        "map1": pygame.Rect(panel_left + 10, 500, 100, 35),
        "map2": pygame.Rect(panel_left + 125, 500, 100, 35),
        "map3": pygame.Rect(panel_left + 240, 500, 100, 35)
    }

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            for key, box in input_boxes.items():
                if box.collidepoint(event.pos):
                    active_input = key
                    break
            else:
                active_input = None

            if setting_buttons["basic"].collidepoint(event.pos):
                advanced_setting = False
            elif setting_buttons["advanced"].collidepoint(event.pos):
                advanced_setting = True
                
            if map_buttons["map1"].collidepoint(event.pos):
                reset_game_preset(map1)
            elif map_buttons["map2"].collidepoint(event.pos):
                reset_game_preset(map2)
            elif map_buttons["map3"].collidepoint(event.pos):
                reset_game_preset(map3)


            for key, rect in control_buttons.items():
                if rect.collidepoint(event.pos):
                    if key == "create":
                        if key == "create":
                            try:
                                map_size_current = map_size
                                map_size = int(input_texts["size"])
                                wumpus_count = int(input_texts["wumpus"])
                                pit_ratio = float(input_texts["pit"])
                                if not (1 <= map_size <= 12):
                                    error_message = "Map size must be between 1 and 12."
                                    map_size = map_size_current
                                elif wumpus_count >= map_size * map_size or not (0 <= pit_ratio < 1):
                                    error_message = "Invalid map settings."
                                    map_size = map_size_current
                                else:
                                    CELL_SIZE = calculate_cell_size(map_size)
                                    WINDOW_WIDTH = CELL_SIZE * map_size + PANEL_WIDTH + 50
                                    WINDOW_HEIGHT = max(CELL_SIZE * map_size + 50, 600)
                                    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
                                    game_won = False
                                    reset_game()
                                    error_message = ""
                            except:
                                error_message = "Invalid input format."
                                map_size = map_size_current
                    elif key == "play":
                        auto_play = True
                        paused = False
                    elif key == "pause":
                        paused = True
                    elif key == "restart":
                        auto_play = False
                        paused = False
                        game_won = False
                        reset_game()

        elif event.type == pygame.KEYDOWN and active_input:
            if event.key == pygame.K_BACKSPACE:
                input_texts[active_input] = input_texts[active_input][:-1]
            elif event.key == pygame.K_RETURN:
                active_input = None
            else:
                input_texts[active_input] += event.unicode

    # Only runs when game is active
    if auto_play and not paused and not game_end:
        score -= 1
        step_count += 1
        if 'G' in percepts:
            if agent.grab(env):
                score += 10
        
        env.agent_pos = agent.position
        percepts = env.get_percepts()
        #inference engine to deduce neighboring cells are safe or not
        inference_engine.process_percepts(env.agent_pos[0], env.agent_pos[1], percepts, env)
        
        actions = []
        make_next_action(agent, inference_engine, env, actions)
        
        for action in actions:
            print("Action taken:", action)
            
            # Check if game completed successfully
            if action == "climb" and agent.has_gold and tuple(agent.position) == (0, 0):
                score += 1000
                auto_play = False
                game_end = True
                game_won = True
                break
            
            if action == "climb" and not agent.has_gold and tuple(agent.position) == (0, 0):
                auto_play = False
                game_end = True
                game_tie = True
                break
        
        print("Arrows left:", agent.arrows)
        for di, dj in env.adjacent(env.agent_pos[0], env.agent_pos[1]):
            print(f"cell({di}, {dj}) is " + inference_engine.infer((di, dj)))
        inference_engine.kb.show()
        
        x, y = agent.position
        cell = env.grid[x][y]
        if cell.has_pit or cell.has_wumpus:
           game_end = True
           game_lose = True
           auto_play = False
           paused = True

    vis.draw(screen)
    pygame.draw.rect(screen, (200, 200, 200), (panel_left, 0, PANEL_WIDTH, WINDOW_HEIGHT))

    draw_button(screen, setting_buttons["basic"], "Basic", not advanced_setting)
    draw_button(screen, setting_buttons["advanced"], "Advanced", advanced_setting)
    draw_inputs(screen, panel_left)
    draw_button(screen, control_buttons["create"], "Create Map", False)
    draw_button(screen, control_buttons["play"], "Play", auto_play and not paused)
    draw_button(screen, control_buttons["pause"], "Pause", paused)
    draw_button(screen, control_buttons["restart"], "Restart", False)
    
    draw_button(screen, map_buttons["map1"], "Map 1", False)
    draw_button(screen, map_buttons["map2"], "Map 2", False)
    draw_button(screen, map_buttons["map3"], "Map 3", False)

    draw_percepts_table(screen, panel_left + 10, 310, percepts)
    draw_score(screen, panel_left + 10, 430, score)
    
    if game_end:
        if game_won:
            win_surf = small_font.render("You win! Agent escaped with gold!", True, (0, 200, 100))
            screen.blit(win_surf, (panel_left + 10, 460))
        elif game_lose:
            score -= 1000
            lose_surf = small_font.render("You lose!", True, (255, 0, 0))
            screen.blit(lose_surf, (panel_left + 10, 460))
        elif game_tie:
            win_surf = small_font.render("Agent escaped without gold!", True, (0, 0, 0))
            screen.blit(win_surf, (panel_left + 10, 460))

    if error_message:
        err_label = small_font.render(error_message, True, (255, 0, 0))
        screen.blit(err_label, (panel_left + 10, 470))

    pygame.display.flip()