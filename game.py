import pygame as pg
import uuid
import os
import shutil
import subprocess

WIDTH = 1280
HEIGHT = 720

DEV = True

GRID_SIZE = (10, 10)

class Grid:

    cell_color = (10, 70, 135)
    hover_color = (10, 100, 180)
    preview_boat = None
    preview_pos = None

    def __init__(self, size):
        self.size = size
        self.cells = []  # Store cell rectangles and their positions
        self.boats = []

    def add_boat(self, boat):
        boat['id'] = len(self.boats) + 1
        self.boats.append(boat)

    def preview(self, boat):
        self.preview_boat = boat.copy()  # Make a copy to avoid modifying the original
        if 'direction' not in self.preview_boat:
            self.preview_boat['direction'] = 'h'  # Default to horizontal if not set

    def draw_boat(self, screen, boat, is_preview=False):
        # Get the cell size from the first cell in the grid
        if not self.cells:
            return
            
        cell_size = self.cells[0].width
        margin = 3  # Same margin as grid cells
        padding = 4  # Padding to make boats slightly smaller
        
        # Calculate the cells this boat occupies
        cells = []
        for i in range(boat['size']):
            try:
                if boat['direction'] == 'h':
                    # For horizontal boats, increment the column (j)
                    cell_idx = boat['pos'][0] * self.size[1] + (boat['pos'][1] + i)
                else:  # vertical
                    # For vertical boats, increment the row (i)
                    cell_idx = (boat['pos'][0] + i) * self.size[1] + boat['pos'][1]
                
                # Check if the cell index is valid
                if 0 <= cell_idx < len(self.cells):
                    cells.append(self.cells[cell_idx])
            except IndexError:
                return  # Skip drawing if boat would go out of bounds
        
        # If no valid cells were found, don't draw the boat
        if not cells:
            return
            
        # Calculate the rectangle that encompasses all cells
        min_x = min(cell.x for cell in cells)
        min_y = min(cell.y for cell in cells)
        max_x = max(cell.x + cell.width for cell in cells)
        max_y = max(cell.y + cell.height for cell in cells)
        
        # Create the boat rectangle with padding
        boat_rect = pg.Rect(
            min_x + padding,
            min_y + padding,
            max_x - min_x - (padding * 2),
            max_y - min_y - (padding * 2)
        )
        
        # Create a surface for the boat with alpha channel
        boat_surf = pg.Surface((boat_rect.width, boat_rect.height), pg.SRCALPHA)
        
        # Draw shadow
        shadow_v = pg.Vector2(1, 2)
        shadow_color = (3, 33, 64, 128 if is_preview else 255)
        boat_color = (151, 87, 43, 128 if is_preview else 255)
        
        pg.draw.rect(boat_surf, shadow_color, pg.Rect(shadow_v.x, shadow_v.y, boat_rect.width, boat_rect.height), border_radius=5)
        pg.draw.rect(boat_surf, boat_color, pg.Rect(0, 0, boat_rect.width, boat_rect.height), border_radius=5)
        
        # Draw the boat surface onto the screen
        screen.blit(boat_surf, boat_rect)

    def draw(self, screen, center_x, center_y, width, height):
        n, m = self.size
        
        margin = 3
        cell_size_x = (width - (margin * (n - 1))) // n
        cell_size_y = (height - (margin * (m - 1))) // m
        cell_size = min(cell_size_x, cell_size_y)
        
        boat_size = cell_size * 0.6
        
        grid_width = (cell_size * n) + (margin * (n - 1))
        grid_height = (cell_size * m) + (margin * (m - 1))
        
        start_x = center_x - grid_width // 2
        start_y = center_y - grid_height // 2
        
        # Clear previous cells
        self.cells = []
        preview_surf = None
        self.preview_pos = None
        
        # Draw cells
        for i in range(n):
            for j in range(m):
                rect = pg.Rect(
                    start_x + (i * (cell_size + margin)),
                    start_y + (j * (cell_size + margin)),
                    cell_size,
                    cell_size
                )
                self.cells.append(rect)
                
                # Check if mouse is hovering over this cell
                mouse_pos = pg.mouse.get_pos()
                color = self.hover_color if rect.collidepoint(mouse_pos) else self.cell_color
                
                # Draw cell
                pg.draw.rect(screen, color, rect, border_radius=5)

                if self.preview_boat and rect.collidepoint(mouse_pos):
                    self.preview_pos = (i, j)

        # Draw boats after the grid
        for boat in self.boats:
            if boat['pos'] is not None:
                self.draw_boat(screen, boat)

        # Draw preview boat if we have a position
        if self.preview_boat and self.preview_pos:
            preview_boat = self.preview_boat.copy()
            preview_boat['pos'] = self.preview_pos
            # Ensure direction is set
            if 'direction' not in preview_boat:
                preview_boat['direction'] = 'h'
            self.draw_boat(screen, preview_boat, is_preview=True)

class Scene:
    buttons = {}
    def setup(self):
        pass

    def update(self, screen):
        pass

class MenuScene(Scene):
    def __init__(self, game):
        self.game = game
        self.buttons = {
            "play": {
                "rect": pg.Rect(100, 100, 200, 100),
                "pos": (WIDTH / 2, HEIGHT / 2),
                "click": lambda: self.game.goto_scene("setup")
            }
        }
        self.was_hovering = False  # Track previous hover state

        for btn in self.buttons.values():
            btn["rect"].center = btn["pos"]

    def update(self, screen):
        mouse_pos = pg.mouse.get_pos()
        is_hovering = self.buttons["play"]["rect"].collidepoint(mouse_pos)
        
        # Play hover sound when mouse enters the button
        if is_hovering and not self.was_hovering:
            pg.mixer.Sound(self.game.assets.audio["music"]["hover"]).play()
        
        self.was_hovering = is_hovering
        
        btn_color = (10, 70, 135) if is_hovering else (13, 82, 154)
        
        pg.draw.rect(screen, btn_color, self.buttons["play"]["rect"], 0, 10)

        font = pg.font.Font(None, 36)
        text = font.render("Jugar", True, (255, 255, 255))
        text_rect = text.get_rect(center=self.buttons["play"]["rect"].center)
        screen.blit(text, text_rect)

class MatchScene(Scene):
    def __init__(self, game):
        self.game = game
        self.grid = None
        self.buttons = {
            "back": {
                "rect": pg.Rect(0, 0, 100, 40),
                "pos": (WIDTH - 60, HEIGHT - 30),
                "click": lambda: self.game.goto_scene("setup")
            }
        }

        for btn in self.buttons.values():
            btn["rect"].center = btn["pos"]

    def save_config(self):
        # Clean cache directory
        if os.path.exists("cache"):
            shutil.rmtree("cache")
        os.makedirs("cache")

        with open(f"cache/{self.id}.txt", "w") as f:
            # Write match ID
            f.write(f"{self.id}\n")
            
            # Write grid size
            f.write(f"{self.grid.size[0]} {self.grid.size[1]}\n")
            
            # Create and write the grid state
            grid_state = [[0 for _ in range(self.grid.size[1])] for _ in range(self.grid.size[0])]
            
            # Fill in boat positions
            for boat in self.grid.boats:
                x, y = boat['pos']
                for i in range(boat['size']):
                    if boat.get('direction', 'h') == 'h':  # Default to horizontal if not set
                        grid_state[y + i][x] = boat['id']
                    else:  # vertical
                        grid_state[y][x + i] = boat['id']
            
            # Write the grid state
            for row in grid_state:
                f.write(" ".join(map(str, row)) + "\n")

    def start_backend(self):

        if DEV or not os.path.exists("main.exe"):
            subprocess.run(["gcc", "main.c", "-o", "main.exe"], )

        result = subprocess.run(["./main.exe", "iniciarJuego", f"{self.id}.txt"], capture_output=True, text=True)
        print(result.stdout)
        print(result.stderr)

    def setup(self, grid):
        self.grid = grid
        self.id = str(uuid.uuid4())[:5]
        self.save_config()
        self.start_backend()

    def update(self, screen):
        # Draw the grid
        self.grid.draw(screen, WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT * 0.8)
        
        # Draw back button
        mouse_pos = pg.mouse.get_pos()
        btn_color = (10, 70, 135) if self.buttons["back"]["rect"].collidepoint(mouse_pos) else (13, 82, 154)
        
        pg.draw.rect(screen, btn_color, self.buttons["back"]["rect"], 0, 10)

        font = pg.font.Font(None, 24)
        text = font.render("Back", True, (255, 255, 255))
        text_rect = text.get_rect(center=self.buttons["back"]["rect"].center)
        screen.blit(text, text_rect)

class SetupScene(Scene):
    def __init__(self, game):
        self.game = game
        self.grid = Grid(GRID_SIZE)

        new_boat = lambda size: {'size': size, 'pos': None, 'direction': 'h', 'selected': False }
        self.boats = [ new_boat(2), new_boat(3), new_boat(3), new_boat(4), new_boat(5) ]

        self.buttons = {
            "start": {
                "rect": pg.Rect(0, 0, 120, 40),
                "pos": (WIDTH - 70, HEIGHT - 30),
                "click": lambda: self.start_match()
            }
        }

        for btn in self.buttons.values():
            btn["rect"].center = btn["pos"]

        self.game.event_manager.add_action_key(pg.K_r, self.rotate_selected_boat)

    def start_match(self):
        self.game.scenes["match"]
        self.game.goto_scene("match", grid=self.grid)

    def place_boat(self, pos):
        # Find the selected boat
        selected_boat = None
        for boat in self.boats:
            if boat['selected']:
                selected_boat = boat
                break
        
        if not selected_boat:
            return
            
        # Check if the boat can be placed at this position
        if not self.grid.preview_pos:
            return
        
        pg.mixer.Sound(self.game.assets.audio["music"]["create"]).play()
            
        # Place the boat
        selected_boat['pos'] = self.grid.preview_pos
        selected_boat['direction'] = selected_boat.get('direction', 'h')  # Ensure direction is set
        selected_boat['selected'] = False
        
        # Add the boat to the grid
        self.grid.add_boat(selected_boat.copy())
        
        # Remove the boat from the available boats
        self.boats.remove(selected_boat)

    def rotate_selected_boat(self):
        for boat in self.boats:
            if boat['selected']:
                boat['direction'] = 'v' if boat['direction'] == 'h' else 'h'
                break

    def draw_boat_btn(self, surf, boat):
        size = surf.get_size()[0]
        n = boat['size']

        pad = 10
        margin = 1
        in_size = min(size // 4, (size-pad) // n)

        y = size // 2 - in_size // 2
        x = (size - (in_size + margin) * n) // 2
        for _ in range(n):
            rect = pg.Rect(x, y, in_size, in_size)
            shadow_v = pg.Vector2(1, 2)
            pg.draw.rect(surf, (3, 33, 64), rect.move(shadow_v), border_radius=1)
            pg.draw.rect(surf, (151, 87, 43), rect, border_radius=1)
            x += in_size + margin

        return pg.transform.rotate(surf, 45)


    def update(self, screen):
        self.grid.draw(screen, WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT * 0.8) 
        rect = pg.Rect(0, 0, 80, 2*HEIGHT//3)
        rect.center = (100, HEIGHT / 2)
        pg.draw.rect(screen, (12, 139, 221), rect, border_radius=5)

        # Handle boat placement on click
        if self.game.event_manager.is_clicking and self.grid.preview_pos:
            self.place_boat(self.grid.preview_pos)

        # Draw start button
        mouse_pos = pg.mouse.get_pos()
        btn_color = (10, 70, 135) if self.buttons["start"]["rect"].collidepoint(mouse_pos) else (13, 82, 154)
        
        pg.draw.rect(screen, btn_color, self.buttons["start"]["rect"], 0, 10)

        font = pg.font.Font(None, 24)
        text = font.render("Start Game", True, (255, 255, 255))
        text_rect = text.get_rect(center=self.buttons["start"]["rect"].center)
        screen.blit(text, text_rect)

        margin = 5
        size = rect.size[0] - (margin * 2)
        pos = pg.Vector2(rect.topleft)
        pos.x += margin
        pos.y += margin

        for boat in self.boats:
            if boat['pos'] is None:
                rect = pg.Rect(pos.x, pos.y, size, size)
                
                if rect.collidepoint(pg.mouse.get_pos()):
                    color = (10, 70, 135)  
                    if self.game.event_manager.is_clicking:
                        for b in self.boats:
                            b['selected'] = False
                        boat['selected'] = True
                else: 
                    color = (7, 74, 140)
                        
                surf = pg.Surface((size, size), flags=pg.SRCALPHA).convert_alpha()
                surf = self.draw_boat_btn(surf, boat)

                if boat['selected']:
                    color = (5, 54, 102)

                    ghost_surf = surf.copy()
                    ghost_surf.set_alpha(150)  # 0.4 * 255
                    ghost_rect = ghost_surf.get_rect(center=pg.mouse.get_pos())
                    screen.blit(ghost_surf, ghost_rect)
                    
                    self.grid.preview(boat)

                pg.draw.rect(screen, color, rect, border_radius=5)

                offset_x = (surf.get_width() - size) // 2
                offset_y = (surf.get_height() - size) // 2
                screen.blit(surf, (pos.x - offset_x, pos.y - offset_y))
                
                pos.y += size + margin


class Game:
    def __init__(self, win_size):
        self.running = True
        pg.mixer.init()
        self.win_size = win_size

        self.event_manager = EventManager(self)
        self.assets = AssetManager()

        self.scenes = {
            "menu": MenuScene(self),
            "setup": SetupScene(self),
            "match": MatchScene(self)
        }
        self.current_scene = self.scenes["menu"]

    def goto_scene(self, scene_name, *args, **kwargs):
        self.current_scene = self.scenes[scene_name]
        self.current_scene.setup(*args, **kwargs)
        
    def setup(self):
        self.assets.load()
        pg.mixer.music.load(self.assets.audio["music"]["main"])
        pg.mixer.music.play(-1)

    def update(self, screen):
        self.event_manager.update()
        screen.fill((12, 139, 221))

        self.current_scene.update(screen)

        return self.running

class EventManager:
    def __init__(self, game):
        self.game = game
        self.is_clicking = False
        self.actions = {}

    def add_action_key(self, key, callback):
        self.actions[key] = callback

    def handle_key_down(self, key):
        if key == pg.K_ESCAPE:
            self.game.running = False

        if key in self.actions:
            self.actions[key]()

    def handle_click(self, pos):
        for btn in self.game.current_scene.buttons.values():
            if btn["rect"].collidepoint(pos):
                btn["click"]()

    def update(self):
        self.is_clicking = False
        for ev in pg.event.get():
            if ev.type == pg.QUIT:
                self.game.running = False

            if ev.type == pg.KEYDOWN:
                self.handle_key_down(ev.key)

            if ev.type == pg.MOUSEBUTTONDOWN:
                self.handle_click(ev.pos)

            if ev.type == pg.MOUSEBUTTONUP:
                self.is_clicking = True

class AssetManager:
    def load(self):
        self.audio = {
            "music": {
                "main": "assets/audio/menu.mp3",
                "hover": "assets/audio/hover.wav",
                "create": "assets/audio/create.wav"
            }
        }

        self.images = {
            "menu": pg.image.load("assets/img/menu.png").convert()
        }

class Engine:

    FPS = 60

    def __init__(self, game):
        self.game = game
        self.setup()

    def setup(self):
        pg.init()
        pg.display.set_caption("Battleship")
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        self.clock = pg.time.Clock()

    def run(self):
        self.running = True
        self.game.setup()
        while self.game.update(self.screen):
            pg.display.flip()
            self.clock.tick(self.FPS)

        pg.quit()

def main():
    game = Game(win_size=(WIDTH, HEIGHT))
    engine = Engine(game)
    engine.run()

if __name__ == "__main__":
    main()
