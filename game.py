import pygame as pg
import uuid
import os
import shutil
import subprocess

WIDTH = 1280
HEIGHT = 720

DEV = True

GRID_SIZE = (15, 15)

class Grid:

    cell_color = (10, 70, 135)
    hover_color = (10, 100, 180)
    preview_boat = None
    preview_pos = None

    def __init__(self, size, width, height, boats=[]):
        self.size = size
        self.boats = boats

        self.width = width
        self.height = height

        self.cell_size = min(self.width // self.size[0], self.height // self.size[1])
        self.margin = 3
        
        self.grid_width = (self.cell_size * self.size[0]) + (self.margin * (self.size[0] - 1))
        self.grid_height = (self.cell_size * self.size[1]) + (self.margin * (self.size[1] - 1))
        
    def add_boat(self, boat):
        boat['id'] = len(self.boats) + 1
        self.boats.append(boat)
        self.preview_boat = None
        self.preview_pos = None

    def preview(self, boat):
        self.preview_boat = boat
        if 'direction' not in self.preview_boat:
            self.preview_boat['direction'] = 'h'  # Default to horizontal if not set

    def draw_boat(self, screen, boat, is_preview=False):
        
        padding = 4

        x0, y0 = boat['pos']
        x = x0 * (self.cell_size + self.margin) + padding
        y = y0 * (self.cell_size + self.margin) + padding

        long = boat['size'] * (self.cell_size + self.margin) - padding * 2 - self.margin
        short = self.cell_size - padding * 2
        width, height = (long, short) if boat['direction'] == 'h' else (short, long)

        # Create the boat rectangle with padding
        boat_rect = pg.Rect(x, y, width, height)
        
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
    
    def draw_cell(self, screen, i, j):
        rect = pg.Rect(i * (self.cell_size + self.margin), j * (self.cell_size + self.margin), self.cell_size, self.cell_size)

        # Check if mouse is hovering over this cell
        mouse_pos = pg.mouse.get_pos() - self.start_pos
        color = self.hover_color if rect.collidepoint(mouse_pos) else self.cell_color
        
        # Draw cell
        pg.draw.rect(screen, color, rect, border_radius=5)

        if self.preview_boat and rect.collidepoint(mouse_pos):
            # Check if boat would exceed grid boundaries
            boat_size = self.preview_boat['size']
            direction = self.preview_boat.get('direction', 'h')
            
            # Check if boat fits in current direction, if not try the other direction
            if direction == 'h' and i + boat_size > self.size[0]:
                direction = 'v'
            elif direction == 'v' and j + boat_size > self.size[1]:
                direction = 'h'
            self.preview_boat['direction'] = direction
                
            # Set preview position if boat fits in either direction
            if (direction == 'h' and i + boat_size <= self.size[0]) or \
               (direction == 'v' and j + boat_size <= self.size[1]):
                self.preview_boat['direction'] = direction
                self.preview_pos = (i, j)

    def draw(self, screen, center_x, center_y):

        self.preview_pos = None

        screen_middle = pg.Vector2(center_x, center_y)
        grid_middle = pg.Vector2(self.grid_width // 2, self.grid_height // 2)
        self.start_pos = screen_middle - grid_middle

        grid_surf = pg.Surface((self.grid_width, self.grid_height), pg.SRCALPHA)
        

        n, m = self.size
        # Draw cells
        for i in range(n):
            for j in range(m):
                self.draw_cell(grid_surf, i, j)

        # Draw boats after the grid
        for boat in self.boats:
            if boat['pos'] is not None:
                self.draw_boat(grid_surf, boat)

        # Draw preview boat if we have a position
        if self.preview_boat and self.preview_pos:
            preview_boat = self.preview_boat.copy()
            preview_boat['pos'] = self.preview_pos
            # Ensure direction is set
            if 'direction' not in preview_boat:
                preview_boat['direction'] = 'h'
            self.draw_boat(grid_surf, preview_boat, is_preview=True)

        screen.blit(grid_surf, self.start_pos)

class ObjectPanel:

    img_size = (50, 50)

    def __init__(self, game, width, height):
        self.game = game
        self.width = width
        self.height = height

        assets = self.game.assets
        self.items = {
            'bomb': {'id': 1, 'quantity': 1, 'image': assets.images["bomb"]},
            'spyglass': {'id': 2, 'quantity': 1, 'image': assets.images["spyglass"]},
            'torpedo': {'id': 3, 'quantity': 1, 'image': assets.images["torpedo"]}
        }
        self.selector_rects = {}  # Store selector rectangles for click detection
        self.setup()

    def setup(self):
        # Load images
        for item in self.items.values():
            item['surface'] = pg.transform.scale(item['image'], self.img_size)

    def draw_quantity_selector(self, screen, pos, size, quantity, item_name):

        x, y = pos
        w, h = size

        # Draw quantity background
        selector_rect = pg.Rect(x, y, w, h)
        pg.draw.rect(screen, (10, 100, 180), selector_rect)
        
        # Draw minus button
        minus_rect = pg.Rect(x, y, w // 3, h)
        pg.draw.rect(screen, (7, 41, 77), minus_rect)
        font = pg.font.Font(None, 20)

        minus_text = font.render("-", True, (255, 255, 255))
        minus_text_rect = minus_text.get_rect(center=minus_rect.center)
        screen.blit(minus_text, minus_text_rect)
        
        # Draw quantity
        quantity_text = font.render(str(quantity), True, (255, 255, 255))
        q_rect = quantity_text.get_rect(center=selector_rect.center)
        screen.blit(quantity_text, q_rect)
        
        # Draw plus button
        plus_rect = pg.Rect(x + w - w // 3, y, w // 3, h)
        pg.draw.rect(screen, (7, 41, 77), plus_rect)
        plus_text = font.render("+", True, (255, 255, 255))
        plus_text_rect = plus_text.get_rect(center=plus_rect.center)
        screen.blit(plus_text, plus_text_rect)
        
        # Store rectangles for click detection
        self.selector_rects[item_name] = {
            'minus': minus_rect,
            'plus': plus_rect
        }

    def handle_click(self, pos):
        # Convert global position to local panel position
        local_pos = (pos[0] - self.panel_x, pos[1] - self.panel_y)
        audio = self.game.assets.audio["music"]
        mixer = pg.mixer

        # Check each item's selector buttons
        for item_name, rects in self.selector_rects.items():
            if rects['minus'].collidepoint(local_pos):
                if self.items[item_name]['quantity'] > 0:
                    self.items[item_name]['quantity'] -= 1
                    mixer.Sound(audio["hover"]).play()
                else:
                    mixer.Sound(audio["deny"]).play()
            elif rects['plus'].collidepoint(local_pos):
                self.items[item_name]['quantity'] += 1
                pg.mixer.Sound(self.game.assets.audio["music"]["hover"]).play()

    def update(self, screen, x, y):
        self.panel_x = x
        self.panel_y = y
        
        # Draw panel background
        surf = pg.Surface((self.width, self.height), pg.SRCALPHA)
        pg.draw.rect(surf, (10, 70, 135), (0, 0, self.width, self.height), border_radius=5)
        
        # Calculate grid layout
        cell_width = self.width // 3
        cell_height = 90
        padding = 10
        
        # Draw items in grid
        for i, (item_name, item) in enumerate(self.items.items()):
            col = i % 3
            row = i // 3
            
            # Calculate box position
            box_rect = pg.Rect(
                col * cell_width + padding,
                row * cell_height + padding,
                cell_width - padding * 2,
                cell_height - padding * 2
            )
            pg.draw.rect(surf, (13, 82, 154), box_rect, border_radius=8)
            
            # Calculate centered image position
            item_x = box_rect.centerx - self.img_size[0] // 2
            item_y = box_rect.centery - self.img_size[1] // 2 - 10  # Offset up slightly to make room for selector
            
            # Draw item image
            surf.blit(item['surface'], (item_x, item_y))
            
            # Draw quantity selector
            h = 20
            selector_size = (box_rect.width, h)
            selector_pos = (box_rect.left, item_y + box_rect.height - h)
            self.draw_quantity_selector(surf, selector_pos, selector_size, item['quantity'], item_name)
        
        screen.blit(surf, (x, y))

class Scene:

    buttons = {}
    ui = None

    def __init__(self, game):
        self.game = game

    def setup(self):
        pass

    def update(self, screen):
        pass

class MenuScene(Scene):
    def setup(self):
        self.ui = UIManager(self.game)

        action = lambda: self.game.goto_scene("setup")
        self.ui.add_button( "play", (200, 100), action, "Jugar", center=(WIDTH / 2, HEIGHT / 2))

    def update(self, screen):
        self.ui.update(screen)

class MatchScene(Scene):
    def setup(self, grid):
        self.init_match(grid)

    def save_config(self):

        grid = self.gridA

        # Clean cache directory
        if os.path.exists("cache"):
            shutil.rmtree("cache")
        os.makedirs("cache")

        with open(f"cache/{self.id}.txt", "w") as f:
            # Write match ID
            f.write(f"{self.id}\n")
            
            # Write grid size
            f.write(f"{grid.size[0]} {grid.size[1]}\n")
            
            # Create and write the grid state
            grid_state = [[0 for _ in range(grid.size[1])] for _ in range(grid.size[0])]
            
            # Fill in boat positions
            for boat in grid.boats:
                x, y = boat['pos']
                for i in range(boat['size']):
                    if boat.get('direction', 'h') == 'h':  # Default to horizontal if not set
                        grid_state[y][x+i] = boat['id']
                    else:  # vertical
                        grid_state[y+i][x] = boat['id']
            
            # Write the grid state
            for row in grid_state:
                f.write(" ".join(map(str, row)) + "\n")

            # Write objects information
            objects_with_quantity = [item for item in self.game.scenes["setup"].object_panel.items.values() if item['quantity'] > 0]
            f.write(f"N objetos: {len(objects_with_quantity)}\n")
            
            # Write each object's id and quantity
            for item in objects_with_quantity:
                f.write(f"{item['id']} {item['quantity']}\n")

    def start_backend(self):

        if DEV or not os.path.exists("main.exe"):
            subprocess.run(["gcc", "TDAS/*.c", "main.c", "-o", "main.exe"])

        result = subprocess.run(["./main.exe", "iniciarJuego", f"{self.id}.txt"], capture_output=True, text=True)
        print(result.stdout)
        print(result.stderr)

    def init_match(self, grid):

        margin = WIDTH // 20
        self.gridA = Grid(GRID_SIZE, WIDTH // 2 - margin*2, HEIGHT * 0.9, boats=[])
        self.gridB = Grid(GRID_SIZE, HEIGHT // 2 - margin*2, HEIGHT * 0.8, boats=grid.boats)

        self.fog_list = []
        x_step = self.gridA.grid_width // 5
        y_step = self.gridA.grid_height // 5
        for i in range(5):
            for j in range(5):
                x = x_step * i
                y = y_step * j

                self.fog_list.append(pg.Vector2(x, y))

        self.id = str(uuid.uuid4())[:5]
        self.save_config()
        self.start_backend()

    def draw_fog(self, screen, box):

        # cloud = self.game.assets.animations["fog_cloud"]

        fog_surf = pg.Surface(box.size, pg.SRCALPHA)
        fog_surf.fill((0, 0, 0, 100))
        screen.blit(fog_surf, box.topleft)

    def update(self, screen):
        # Draw the grid
        posA = pg.Vector2(2 * WIDTH / 3, HEIGHT / 2)
        posB = pg.Vector2(WIDTH / 4, HEIGHT / 3)

        self.gridA.draw(screen, *posA)
        self.gridB.draw(screen, *posB)

        gridA_rect = pg.Rect(*self.gridA.start_pos, self.gridA.grid_width, self.gridA.grid_width)
        self.draw_fog(screen, gridA_rect)

class SetupScene(Scene):
    def setup(self):
        self.grid = Grid(GRID_SIZE, WIDTH, HEIGHT * 0.8)
        self.object_panel = ObjectPanel(self.game, WIDTH // 5, HEIGHT * 0.8)

        new_boat = lambda size: {'size': size, 'pos': None, 'direction': 'h', 'selected': False }
        self.boats = [ new_boat(2), new_boat(3), new_boat(3), new_boat(4), new_boat(5) ]

        self.ui = UIManager(self.game)

        action = lambda: self.start_match()
        self.ui.add_button( "start", (120, 40), action, "Start Game", center=(WIDTH - 70, HEIGHT - 30))

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

    def handle_click(self, pos):
        # Check if click is on object panel
        panel_x = WIDTH - self.object_panel.width - 50
        panel_y = HEIGHT // 2 - self.object_panel.height // 2
        panel_rect = pg.Rect(panel_x, panel_y, self.object_panel.width, self.object_panel.height)
        
        if panel_rect.collidepoint(pos):
            self.object_panel.handle_click(pos)
            return True
            
        # Handle boat placement on click
        if self.grid.preview_pos:
            self.place_boat(self.grid.preview_pos)
            return True
            
        return False

    def update(self, screen):
        self.grid.draw(screen, WIDTH / 2, HEIGHT / 2) 
        rect = pg.Rect(0, 0, 80, 2*HEIGHT//3)
        rect.center = (100, HEIGHT / 2)
        pg.draw.rect(screen, (12, 139, 221), rect, border_radius=5)

        # Handle boat placement on click
        if self.game.event_manager.is_clicking:
            self.handle_click(pg.mouse.get_pos())

        self.ui.update(screen)
        self.object_panel.update(screen, WIDTH - self.object_panel.width - 50, HEIGHT // 2 - self.object_panel.height // 2)

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

class UIManager:
    def __init__(self, game):
        self.game = game
        self.buttons = {}
        self.was_hovering = {}  # Track hover state for each button

    def add_button(self, name, size, click, text=None, topleft=None, center=None):
        rect = pg.Rect(0, 0, size[0], size[1])
        if center is not None:
            rect.center = center
        elif topleft is not None:
            rect.topleft = topleft
            
        self.buttons[name] = {
            "rect": rect,
            "click": click,
            "text": text
        }
        self.was_hovering[name] = False

    def mousePressed(self, pos):
        for _, btn in self.buttons.items():
            if btn["rect"].collidepoint(pos):
                btn["click"]()
                return True
        return False

    def update(self, screen):
        mouse_pos = pg.mouse.get_pos()
        
        for name, btn in self.buttons.items():
            is_hovering = btn["rect"].collidepoint(mouse_pos)
            
            # Play hover sound when mouse enters the button
            if is_hovering and not self.was_hovering[name]:
                pg.mixer.Sound(self.game.assets.audio["music"]["hover"]).play()
            
            self.was_hovering[name] = is_hovering
            
            # Draw button
            btn_color = (10, 70, 135) if is_hovering else (13, 82, 154)
            pg.draw.rect(screen, btn_color, btn["rect"], 0, 10)
            
            # Draw text if provided
            if btn["text"]:
                font = pg.font.Font(None, 24)
                text = font.render(btn["text"], True, (255, 255, 255))
                text_rect = text.get_rect(center=btn["rect"].center)
                screen.blit(text, text_rect)


class Game:
    def __init__(self, win_size):
        self.running = True
        pg.mixer.init()
        self.win_size = win_size
        self.frame = 0

        self.event_manager = EventManager(self)
        self.assets = AssetManager()

    def goto_scene(self, scene_name, *args, **kwargs):
        self.current_scene = self.scenes[scene_name]
        self.current_scene.setup(*args, **kwargs)
        
    def setup(self):
        self.assets.load()
        pg.mixer.music.load(self.assets.audio["music"]["main"])
        pg.mixer.music.play(-1)

        self.scenes = {
            "menu": MenuScene(self),
            "setup": SetupScene(self),
            "match": MatchScene(self)
        }
        self.current_scene = self.scenes["menu"]
        self.current_scene.setup()

    def update(self, screen):
        self.event_manager.update()
        screen.fill((12, 139, 221))

        self.current_scene.update(screen)
        if self.current_scene.ui:
            self.current_scene.ui.update(screen)
        self.frame += 1

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
        scene = self.game.current_scene
        if scene.ui:
            scene.ui.mousePressed(pos)

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

class AnimatedSprite:
    def __init__(self, img, size, n_frames):
        self.img = pg.image.load(img).convert()
        self.size = size
        self.n_frames = n_frames

        self.columns = self.img.get_width() // self.size[0]
        self.rows = self.img.get_height() // self.size[1]

    def get_frame(self, frame):
        frame = frame % self.n_frames  # Ensure frame is within bounds
        row = frame // self.columns    # Calculate row based on columns
        col = frame % self.columns     # Calculate column
        x = col * self.size[0]         # Calculate x position
        y = row * self.size[1]         # Calculate y position
        return self.img.subsurface(x, y, self.size[0], self.size[1])


class AssetManager:
    def load(self):
        self.audio = {
            "music": {
                "main": "assets/audio/menu.mp3",
                "hover": "assets/audio/hover.wav",
                "create": "assets/audio/create.wav",
                "deny": "assets/audio/deny.wav"
            }
        }

        self.images = {
            "menu": pg.image.load("assets/img/menu.png").convert_alpha(),
            "bomb": pg.image.load("assets/img/bomb.png").convert_alpha(),
            "spyglass": pg.image.load("assets/img/spyglass.png").convert_alpha(),
            "torpedo": pg.image.load("assets/img/torpedo.png").convert_alpha()
        }

        self.animations = {
            "fog_cloud": AnimatedSprite("assets/anim/fog-cloud.png", (1280, 900), 37),
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
