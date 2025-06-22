import pygame as pg
import uuid
import os
import shutil
import subprocess
import random
import math

WIDTH = 1280
HEIGHT = 720

DEV = True

GRID_SIZE = (10, 10)

class Grid:

    cell_color = (10, 70, 135)
    hover_color = (10, 100, 180)
    handle_click = lambda s,x,y: None

    def __init__(self, scene, size, width, height, boats=[]):
        self.scene = scene
        self.size = size
        self.boats = boats

        self.width = width
        self.height = height

        self.cell_size = min(self.width // self.size[0], self.height // self.size[1])
        self.margin = 3
        
        self.grid_width = (self.cell_size * self.size[0]) + (self.margin * (self.size[0] - 1))
        self.grid_height = (self.cell_size * self.size[1]) + (self.margin * (self.size[1] - 1))
        
        # Add state grid to track cell states (hit/miss)
        self.state_grid = [[0 for _ in range(self.size[1])] for _ in range(self.size[0])]
        
    def mark_cell(self, x, y, value):
        """Mark a cell as hit or miss and update visual representation"""
        self.state_grid[y][x] = value
        
        # Play sound if it's a hit (negative value indicates hit)
        if value < 0:
            destroy_sound = self.scene.game.assets.audio["sfx"]["destroy"]
            destroy_sound.play()
        
    def draw_grid_frame(self, screen):
        frame_surface = pg.Surface((self.grid_width + 20, self.grid_height + 20), pg.SRCALPHA)
        frame_color = (0, 0, 0, 80)
        frame_rect = pg.Rect(0, 0, self.grid_width + 20, self.grid_height + 20)
        pg.draw.rect(frame_surface, frame_color, frame_rect, border_radius=15)
        screen.blit(frame_surface, (self.start_pos.x - 10, self.start_pos.y - 10))
    
    def draw_boat(self, screen, boat, is_preview=False):
        
        padding = 4

        x0, y0 = boat['pos']
        x = x0 * (self.cell_size + self.margin) + padding
        y = y0 * (self.cell_size + self.margin) + padding

        long = boat['size'] * (self.cell_size + self.margin) - padding * 2 - self.margin
        short = self.cell_size - padding * 2
        width, height = (long, short) if boat['direction'] == 'h' else (short, long)

        # Crear el rectángulo del barco con padding
        boat_rect = pg.Rect(x, y, width, height)
        
        # Crear una superficie para el barco con canal alfa
        boat_surf = pg.Surface((boat_rect.width, boat_rect.height), pg.SRCALPHA)
        boat_color = (151, 87, 43, 128 if is_preview else 255)
        pg.draw.rect(boat_surf, boat_color, pg.Rect(0, 0, boat_rect.width, boat_rect.height), border_radius=5)
        
        # Dibujar la superficie del barco en la pantalla
        screen.blit(boat_surf, boat_rect)
    
    def draw_cell(self, screen, i, j):
        w = self.cell_size + self.margin
        s = self.cell_size
        rect = pg.Rect(i * w, j * w, s, s)
        mouse_pos = pg.mouse.get_pos() - self.start_pos
        color = self.hover_color if rect.collidepoint(mouse_pos) else self.cell_color
        pg.draw.rect(screen, color, rect, border_radius=5)
        return rect
    
    def draw(self, surf):
        # Draw hit/miss indicators on the grid
        n, m = self.size
        for i in range(n):
            for j in range(m):
                w = self.cell_size + self.margin
                s = self.cell_size
                rect = pg.Rect(i * w, j * w, s, s)
                
                # Draw darker box for misses (value = 99)
                if self.state_grid[i][j] == 99:
                    pg.draw.rect(surf, (5, 35, 67), rect, border_radius=5)
                
                # Draw broken image for hits (negative values)
                if self.state_grid[i][j] < 0:
                    broken_img = self.scene.game.assets.images["broken"]
                    broken_img = pg.transform.smoothscale(broken_img, (s, s))
                    surf.blit(broken_img, rect)

    def update(self, screen, center_x, center_y):

        self.preview_pos = None

        screen_middle = pg.Vector2(center_x, center_y)
        grid_middle = pg.Vector2(self.grid_width // 2, self.grid_height // 2)
        self.start_pos = screen_middle - grid_middle

        # Draw the grid frame first (behind the grid)
        self.draw_grid_frame(screen)

        grid_surf = pg.Surface((self.grid_width, self.grid_height), pg.SRCALPHA)

        n, m = self.size
        # Dibujar celdas
        for i in range(n):
            for j in range(m):
                self.draw_cell(grid_surf, i, j)

        # Dibujar barcos después de la cuadrícula
        for boat in self.boats:
            if boat['pos'] is not None:
                self.draw_boat(grid_surf, boat)

        self.draw(grid_surf)
        screen.blit(grid_surf, self.start_pos)

class SetupGrid(Grid):
    
    preview_boat = None
    preview_pos = None

    def add_boat(self, boat):
        boat['id'] = len(self.boats) + 1
        self.boats.append(boat)
        self.preview_boat = None
        self.preview_pos = None

    def preview(self, boat):
        self.preview_boat = boat
        if 'direction' not in self.preview_boat:
            self.preview_boat['direction'] = 'h'  # Por defecto horizontal si no está establecido

    def draw_cell(self, screen, i, j):
        rect = super().draw_cell(screen, i, j)

        mouse_pos = pg.mouse.get_pos() - self.start_pos
        w = self.cell_size + self.margin
        s = self.cell_size
        rect = pg.Rect(i * w, j * w, s, s)

        if self.preview_boat and rect.collidepoint(mouse_pos):
            # Verificar si el barco excedería los límites de la cuadrícula
            boat_size = self.preview_boat['size']
            direction = self.preview_boat.get('direction', 'h')
            
            # Verificar si el barco cabe en la dirección actual, si no, probar la otra dirección
            if direction == 'h' and i + boat_size > self.size[0]:
                direction = 'v'
            elif direction == 'v' and j + boat_size > self.size[1]:
                direction = 'h'
            self.preview_boat['direction'] = direction
                
            # Establecer posición de vista previa si el barco cabe en cualquier dirección
            if (direction == 'h' and i + boat_size <= self.size[0]) or \
               (direction == 'v' and j + boat_size <= self.size[1]):
                self.preview_boat['direction'] = direction
                self.preview_pos = (i, j)

    def draw(self, grid_surf):
         # Dibujar barco de vista previa si tenemos una posición
        if self.preview_boat and self.preview_pos:
            preview_boat = self.preview_boat.copy()
            preview_boat['pos'] = self.preview_pos
            # Asegurar que la dirección esté establecida
            if 'direction' not in preview_boat:
                preview_boat['direction'] = 'h'
            self.draw_boat(grid_surf, preview_boat, is_preview=True)

class EnemyGrid(Grid):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.selected_target = None
        self.target_img = self.scene.game.assets.images["target"]

        target_size = int(self.cell_size * 0.8)
        dim = (target_size, target_size)
        self.target_img = pg.transform.smoothscale(self.target_img, dim)

        self.state_grid = [[0 for _ in range(self.size[1])] for _ in range(self.size[0])]
        
        # Referencia al objeto seleccionado para mostrar marcador
        self.selected_object = None
        # Orientación manual para torpedo (6: horizontal, 7: vertical)
        self.torpedo_orientation = 6

    def set_selected_object(self, object_name):
        self.selected_object = object_name
        # Resetear orientación cuando se selecciona un nuevo objeto
        self.torpedo_orientation = 6

    def rotate_torpedo(self):
        """Rotar la orientación del torpedo entre horizontal y vertical"""
        if self.selected_object == 'torpedo':
            self.torpedo_orientation = 7 if self.torpedo_orientation == 6 else 6

    def is_valid_torpedo_position(self, i, j):
        """Verificar si la posición es válida para colocar un torpedo (en el borde)"""
        border = (0, self.size[0] - 1)
        return i in border or j in border

    def handle_click(self, pos):
        # Convertir posición del mouse a índices de celda de la cuadrícula
        mouse_vec = pg.Vector2(pos) - self.start_pos
        for i in range(self.size[0]):
            for j in range(self.size[1]):
                w = self.cell_size + self.margin
                s = self.cell_size
                rect = pg.Rect(i * w, j * w, s, s)
                if rect.collidepoint(mouse_vec):
                    self.selected_target = (i, j)
                    return

    def clear_target(self):
        self.selected_target = None

    def draw_state(self, screen, x, y):

        screen_middle = pg.Vector2(x, y)
        grid_middle = pg.Vector2(self.grid_width // 2, self.grid_height // 2)
        self.start_pos = screen_middle - grid_middle

        # Draw the grid frame first (behind the grid)
        self.draw_grid_frame(screen)

        grid_surf = pg.Surface((self.grid_width, self.grid_height), pg.SRCALPHA)

        n, m = self.size
        # Dibujar celdas
        for i in range(n):
            for j in range(m):
                w = self.cell_size + self.margin
                s = self.cell_size
                rect = pg.Rect(i * w, j * w, s, s)
                
                if self.state_grid[i][j] == 99:
                    pg.draw.rect(grid_surf, (10, 70, 135), rect)

                if self.state_grid[i][j] < 0:
                    # dibujar imagen de roto
                    broken_img = self.scene.game.assets.images["broken"]
                    broken_img = pg.transform.smoothscale(broken_img, (s, s))
                    grid_surf.blit(broken_img, rect)

        # Dibujar objetos colocados
        self.draw_placed_objects(grid_surf)
        screen.blit(grid_surf, self.start_pos)

    def draw_placed_objects(self, grid_surf):
        """Dibujar objetos que han sido colocados en la cuadrícula"""
        if not hasattr(self.scene, 'placed_objects'):
            return
            
        for obj in self.scene.placed_objects:
            x, y = obj['x'], obj['y']
            object_name = obj['object_name']
            
            # Calcular posición en la superficie de la cuadrícula
            w = self.cell_size + self.margin
            s = self.cell_size
            rect = pg.Rect(x * w, y * w, s, s)
            
            # Obtener imagen del objeto
            obj_img = self.scene.game.assets.images[object_name]
            obj_size = int(self.cell_size * 0.6)
            scaled_obj = pg.transform.smoothscale(obj_img, (obj_size, obj_size))
            
            # Centrar la imagen del objeto en la celda
            obj_rect = scaled_obj.get_rect(center=rect.center)
            grid_surf.blit(scaled_obj, obj_rect)

            if object_name == 'torpedo':
                orientation = obj['orientation']
                circle_radius = 3
                circle_color = (255, 0, 0)
                max_i = self.size[0] - 1
                max_j = self.size[1] - 1
                # Horizontal
                if orientation == 6:
                    if x == 0:  # left border, points right
                        circle_x = rect.right - circle_radius - 2
                        circle_y = rect.centery
                        pg.draw.circle(grid_surf, circle_color, (circle_x, circle_y), circle_radius)
                    elif x == max_i:  # right border, points left
                        circle_x = rect.left + circle_radius + 2
                        circle_y = rect.centery
                        pg.draw.circle(grid_surf, circle_color, (circle_x, circle_y), circle_radius)
                # Vertical
                elif orientation == 7:
                    if y == 0:  # top border, points down
                        circle_x = rect.centerx
                        circle_y = rect.bottom - circle_radius - 2
                        pg.draw.circle(grid_surf, circle_color, (circle_x, circle_y), circle_radius)
                    elif y == max_j:  # bottom border, points up
                        circle_x = rect.centerx
                        circle_y = rect.top + circle_radius + 2
                        pg.draw.circle(grid_surf, circle_color, (circle_x, circle_y), circle_radius)

    def update_cell(self, x, y, value):
        self.state_grid[x][y] = value

        if value < 0:
            # reproducir sonido de destrucción
            destroy_sound = self.scene.game.assets.audio["sfx"]["destroy"]
            destroy_sound.play()

    def draw_cell(self, screen, i, j):
        super().draw_cell(screen, i, j)
        
        # Dibujar marcador de objetivo seleccionado
        if self.selected_target == (i, j):
            w = self.cell_size + self.margin
            s = self.cell_size
            rect = pg.Rect(i * w, j * w, s, s)

            # Centrar la imagen del objetivo en la celda
            img_rect = self.target_img.get_rect(center=rect.center)
            screen.blit(self.target_img, img_rect)
        
        # Dibujar marcador de objeto seleccionado solo en la posición del mouse
        if self.selected_object:
            w = self.cell_size + self.margin
            s = self.cell_size
            rect = pg.Rect(i * w, j * w, s, s)
            
            # Verificar si el mouse está sobre esta celda
            mouse_pos = pg.mouse.get_pos() - self.start_pos
            if rect.collidepoint(mouse_pos):
                # Obtener imagen del objeto seleccionado
                obj_img = self.scene.game.assets.images[self.selected_object]
                obj_size = int(self.cell_size * 0.6)
                scaled_obj = pg.transform.smoothscale(obj_img, (obj_size, obj_size))
                
                # Centrar la imagen del objeto en la celda
                obj_rect = scaled_obj.get_rect(center=rect.center)
                screen.blit(scaled_obj, obj_rect)

                # Dibujar círculo de orientación para torpedo en preview
                if self.selected_object == 'torpedo':
                    # Solo mostrar orientación si la posición es válida para torpedo
                    if self.is_valid_torpedo_position(i, j):
                        circle_radius = 3
                        circle_color = (255, 0, 0)

                        max_i = self.size[0] - 1
                        max_j = self.size[1] - 1
                        
                        if self.torpedo_orientation == 6:  # Horizontal
                            if i == 0:  # left border, points right
                                circle_x = rect.right - circle_radius - 2
                                circle_y = rect.centery
                                pg.draw.circle(screen, circle_color, (circle_x, circle_y), circle_radius)
                            elif i == max_i:  # right border, points left
                                circle_x = rect.left + circle_radius + 2
                                circle_y = rect.centery
                                pg.draw.circle(screen, circle_color, (circle_x, circle_y), circle_radius)
                        # Vertical
                        elif self.torpedo_orientation == 7:
                            if j == 0:  # top border, points down
                                circle_x = rect.centerx
                                circle_y = rect.bottom - circle_radius - 2
                                pg.draw.circle(screen, circle_color, (circle_x, circle_y), circle_radius)
                            elif j == max_j:  # bottom border, points up
                                circle_x = rect.centerx
                                circle_y = rect.top + circle_radius + 2
                                pg.draw.circle(screen, circle_color, (circle_x, circle_y), circle_radius)

class ObjectPanel:

    img_size = (55, 55)

    def __init__(self, game, width, height):
        self.game = game
        self.width = width
        self.height = height

        assets = self.game.assets
        self.items = {
            'bomb': {'id': 1, 'quantity': 1, 'image': assets.images["bomb"], 'info': "Bomba\nPuede destruir casillas en un rango de 3x3"},
            'spyglass': {'id': 2, 'quantity': 1, 'image': assets.images["spyglass"], 'info': "Catalejo\nPuede ver una casilla adicional"},
            'torpedo': {'id': 3, 'quantity': 1, 'image': assets.images["torpedo"], 'info': "Torpedo\nEs lanzado en línea recta desde el borde para destruir la primera casilla que encuentre"}
        }
        self.setup()

    def set_items(self, items):
        self.items = items

    def setup(self):
        # Cargar imágenes
        for item in self.items.values():
            item['surface'] = pg.transform.scale(item['image'], self.img_size)

    def handle_click(self, pos):
        # Método base para manejar clics - puede ser sobrescrito por subclases
        pass

    def update(self, screen, x, y):
        self.panel_x = x
        self.panel_y = y
        
        # Dibujar fondo del panel
        surf = pg.Surface((self.width, self.height), pg.SRCALPHA)
        pg.draw.rect(surf, (10, 70, 135), (0, 0, self.width, self.height), border_radius=5)
        
        # Calcular diseño de cuadrícula
        cell_width = self.width // 3
        cell_height = 90
        padding = 10
        
        # Dibujar elementos en cuadrícula
        for i, (item_name, item) in enumerate(self.items.items()):
            col = i % 3
            row = i // 3
            
            # Calcular posición de la caja
            box_rect = pg.Rect(
                col * cell_width + padding,
                row * cell_height + padding,
                cell_width - padding * 2,
                cell_height - padding * 2
            )
            pg.draw.rect(surf, (13, 82, 154), box_rect, border_radius=8)
            
            # Calcular posición centrada de la imagen
            item_x = box_rect.centerx - self.img_size[0] // 2
            item_y = box_rect.centery - self.img_size[1] // 2
            
            # Dibujar imagen del elemento
            surf.blit(item['surface'], (item_x, item_y))

            # Dibujar cantidad de usos restantes
            if item['quantity'] > 0:
                font = pg.font.Font(None, 20)
                quantity_text = font.render(str(item['quantity']), True, (255, 255, 255))
                # Posicionar en la esquina superior derecha de la caja
                text_x = box_rect.right - quantity_text.get_width() - 5
                text_y = box_rect.top + 5
                surf.blit(quantity_text, (text_x, text_y))

            mouse_relative_pos = pg.Vector2(pg.mouse.get_pos()) - pg.Vector2(x, y)
            if box_rect.collidepoint(mouse_relative_pos):
                self.game.info_box.add_message(f"{item['info']}")
        
        screen.blit(surf, (x, y))

class SetupObjectPanel(ObjectPanel):
    def __init__(self, game, width, height):
        super().__init__(game, width, height)
        self.selector_rects = {}  # Almacenar rectángulos del selector para detección de clics

    def draw_quantity_selector(self, screen, pos, size, quantity, item_name):

        x, y = pos
        w, h = size

        # Dibujar fondo del selector de cantidad
        selector_rect = pg.Rect(x, y, w, h)
        pg.draw.rect(screen, (10, 100, 180), selector_rect)
        
        # Dibujar botón menos
        minus_rect = pg.Rect(x, y, w // 3, h)
        pg.draw.rect(screen, (7, 41, 77), minus_rect)
        font = pg.font.Font(None, 20)

        minus_text = font.render("-", True, (255, 255, 255))
        minus_text_rect = minus_text.get_rect(center=minus_rect.center)
        screen.blit(minus_text, minus_text_rect)
        
        # Dibujar cantidad
        quantity_text = font.render(str(quantity), True, (255, 255, 255))
        q_rect = quantity_text.get_rect(center=selector_rect.center)
        screen.blit(quantity_text, q_rect)
        
        # Dibujar botón más
        plus_rect = pg.Rect(x + w - w // 3, y, w // 3, h)
        pg.draw.rect(screen, (7, 41, 77), plus_rect)
        plus_text = font.render("+", True, (255, 255, 255))
        plus_text_rect = plus_text.get_rect(center=plus_rect.center)
        screen.blit(plus_text, plus_text_rect)
        
        # Almacenar rectángulos para detección de clics con coordenadas relativas al panel
        self.selector_rects[item_name] = {
            'minus': pg.Rect(x, y, w // 3, h),
            'plus': pg.Rect(x + w - w // 3, y, w // 3, h)
        }

    def handle_click(self, pos):
        # Convertir posición global a posición local del panel
        local_pos = (pos[0] - self.panel_x, pos[1] - self.panel_y)
        audio = self.game.assets.audio["music"]
        mixer = pg.mixer

        # Verificar cada botón del selector de cada elemento
        for item_name, rects in self.selector_rects.items():
            if rects['minus'].collidepoint(local_pos):
                if self.items[item_name]['quantity'] > 0:
                    self.items[item_name]['quantity'] -= 1
                    hover_audio = self.game.assets.audio["sfx"]["hover"]
                    hover_audio.play()
                else:
                    deny_audio = self.game.assets.audio["sfx"]["deny"]
                    deny_audio.play()
                    
            elif rects['plus'].collidepoint(local_pos):
                self.items[item_name]['quantity'] += 1
                hover_audio = self.game.assets.audio["sfx"]["hover"]
                hover_audio.play()

    def update(self, screen, x, y):
        self.panel_x = x
        self.panel_y = y
        
        # Dibujar fondo del panel
        surf = pg.Surface((self.width, self.height), pg.SRCALPHA)
        pg.draw.rect(surf, (10, 70, 135), (0, 0, self.width, self.height), border_radius=5)
        
        # Calcular diseño de cuadrícula
        cell_width = self.width // 3
        cell_height = 90
        padding = 10
        
        # Dibujar elementos en cuadrícula
        for i, (item_name, item) in enumerate(self.items.items()):
            col = i % 3
            row = i // 3
            
            # Calcular posición de la caja
            box_rect = pg.Rect(
                col * cell_width + padding,
                row * cell_height + padding,
                cell_width - padding * 2,
                cell_height - padding * 2
            )
            pg.draw.rect(surf, (13, 82, 154), box_rect, border_radius=8)
            
            # Calcular posición centrada de la imagen
            item_x = box_rect.centerx - self.img_size[0] // 2
            item_y = box_rect.centery - self.img_size[1] // 2 - 10  # Desplazamiento hacia arriba para hacer espacio al selector
            
            # Dibujar imagen del elemento
            surf.blit(item['surface'], (item_x, item_y))

            mouse_relative_pos = pg.Vector2(pg.mouse.get_pos()) - pg.Vector2(x, y)
            if box_rect.collidepoint(mouse_relative_pos):
                self.game.info_box.add_message(f"{item['info']}")
            
            # Dibujar selector de cantidad
            h = 20
            selector_size = (box_rect.width, h)
            selector_pos = (box_rect.left, item_y + box_rect.height - h)
            self.draw_quantity_selector(surf, selector_pos, selector_size, item['quantity'], item_name)
        
        screen.blit(surf, (x, y))

class Scene:

    buttons = {}
    ui = None
    handle_click = None

    def __init__(self, game):
        self.game = game

    def setup(self):
        pass

    def update(self, screen):
        pass
        
    def draw_frame(self, screen):
        """Draw a rounded black box frame with 50% opacity around the screen"""
        # Create a surface with alpha channel for transparency
        frame_surface = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
        
        # Black color with 50% opacity (128 alpha value)
        frame_color = (0, 0, 0, 50)
        
        # Frame dimensions - leaving some margin from screen edges
        margin = 20
        frame_rect = pg.Rect(margin, margin, WIDTH - 2 * margin, HEIGHT - 2 * margin)
        
        # Draw the rounded rectangle frame
        pg.draw.rect(frame_surface, frame_color, frame_rect, border_radius=15)
        
        # Blit the frame surface onto the screen
        screen.blit(frame_surface, (0, 0))

class MenuScene(Scene):
    def setup(self):
        self.ui = UIManager(self.game)

        action = lambda: self.game.goto_scene("intro")
        play_center = (WIDTH / 2, HEIGHT / 2)
        self.ui.add_button( "play", (200, 100), action, "Jugar", center=play_center)

        # Agregar botón de Historial
        action_historial = lambda: self.game.goto_scene("history")
        history_center = (WIDTH / 2, HEIGHT / 2 + 120)
        self.ui.add_button("historial", (200, 100), action_historial, "Historial", center=history_center)

    def update(self, screen):
        # Dibujar título
        title_img = self.game.assets.images["title"]
        title_width = 400
        title_height = int(title_width * title_img.get_height() / title_img.get_width())
        scaled_title = pg.transform.smoothscale(title_img, (title_width, title_height))
        
        title_x = (WIDTH - title_width) // 2
        title_y = HEIGHT // 4 - title_height // 2
        screen.blit(scaled_title, (title_x, title_y))
        
        self.ui.update(screen)
        
    def draw_frame(self, screen):
        """Override to not draw frame in menu scene"""
        pass

class TextScene(Scene):
    """Base class for scenes with typewriter text effects"""

    def setup(self):
        # Variables for the effect typewriter
        self.current_paragraph = 0
        self.current_char = 0
        self.typewriter_speed = 2  # Caracteres por frame
        self.frame_counter = 0
        self.finished_typing = False
        
        # Configuración del box de texto
        self.text_box_width = WIDTH - 100
        self.text_box_height = 300
        self.text_box_x = 50
        self.text_box_y = HEIGHT - self.text_box_height - 100
        
        # Configuración del texto
        self.font = pg.font.Font(None, 24)
        self.line_height = 30
        self.max_chars_per_line = 80

        self.start()

    def wrap_text(self, text, max_width):
        """Envolver texto para que quepa en el ancho especificado"""
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            test_width = self.font.size(test_line)[0]
            
            if test_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines

    def update_typewriter(self, texts):
        """Actualizar el efecto typewriter"""
        if self.finished_typing:
            return
            
        self.frame_counter += 1
        
        if self.frame_counter % self.typewriter_speed == 0:
            if self.current_paragraph < len(texts):
                paragraph = texts[self.current_paragraph]
                if paragraph == "":  # Línea vacía
                    self.current_paragraph += 1
                    self.current_char = 0
                else:
                    # Calcular el número total de caracteres en el párrafo actual
                    lines = self.wrap_text(paragraph, self.text_box_width - 60)
                    total_chars = sum(len(line) for line in lines)
                    
                    if self.current_char < total_chars:
                        self.current_char += 1
                    else:
                        # Pasar al siguiente párrafo
                        self.current_paragraph += 1
                        self.current_char = 0
            else:
                # Terminamos de escribir todo
                self.finished_typing = True

    def draw_text_box(self, screen, texts):
        """Dibujar el box de texto con el efecto typewriter"""
        # Dibujar fondo del box
        box_rect = pg.Rect(self.text_box_x, self.text_box_y, self.text_box_width, self.text_box_height)
        pg.draw.rect(screen, (10, 70, 135), box_rect, border_radius=10)
        
        # Crear superficie para el texto con transparencia
        text_surface = pg.Surface((self.text_box_width - 40, self.text_box_height - 40), pg.SRCALPHA)
        
        current_y = 0
        
        # Dibujar párrafos completos
        for i in range(self.current_paragraph):
            if i < len(texts):
                paragraph = texts[i]
                if paragraph == "":  # Línea vacía
                    current_y += self.line_height // 2
                else:
                    lines = self.wrap_text(paragraph, self.text_box_width - 60)
                    for line in lines:
                        text = self.font.render(line, True, (255, 255, 255))
                        text_surface.blit(text, (0, current_y))
                        current_y += self.line_height
        
        # Dibujar párrafo actual con efecto typewriter
        if self.current_paragraph < len(texts):
            paragraph = texts[self.current_paragraph]
            if paragraph == "":  # Línea vacía
                current_y += self.line_height // 2
            else:
                lines = self.wrap_text(paragraph, self.text_box_width - 60)
                chars_processed = 0
                
                for line in lines:
                    # Calcular cuántos caracteres de esta línea mostrar
                    line_length = len(line)
                    chars_to_show = max(0, min(line_length, self.current_char - chars_processed))
                    
                    if chars_to_show > 0:
                        display_text = line[:chars_to_show]
                        text = self.font.render(display_text, True, (255, 255, 255))
                        text_surface.blit(text, (0, current_y))
                    
                    chars_processed += line_length
                    current_y += self.line_height
        
        # Dibujar la superficie de texto en el box
        screen.blit(text_surface, (self.text_box_x + 20, self.text_box_y + 20))

    def handle_click(self, pos):
        # Si hacemos clic en cualquier lugar, acelerar o completar el texto
        if not self.finished_typing:
            # Completar todo el texto inmediatamente
            self.finished_typing = True
            self.current_paragraph = len(self.get_texts())
            self.current_char = 0
        return False

    def get_texts(self):
        """Override this method in subclasses to return the texts to display"""
        return []

class IntroScene(TextScene):

    def start(self):

        self.text_box_width = (WIDTH // 2) - 50  # Half screen width minus margin
        self.text_box_height = HEIGHT - 200  # Most of screen height
        self.text_box_x = 50  # Left margin
        self.text_box_y = 100  # Top margin

        self.current_paragraph = 0
        self.current_char = 0
        self.typewriter_speed = 2  # Caracteres por frame
        self.frame_counter = 0
        self.finished_typing = False

        self.start_frame = int(self.game.frame)
        self.ui = UIManager(self.game)
        
        # Botón para continuar al setup
        action_continue = lambda: self.game.goto_scene("setup")
        self.ui.add_button("continue", (150, 50), action_continue, "Continuar", topleft=(WIDTH-180, HEIGHT-80))
        
        # Botón para volver al menú
        action_back = lambda: self.game.goto_scene("menu")
        self.ui.add_button("back", (120, 50), action_back, "Volver", topleft=(60, HEIGHT-80))
        
        # Variables para mostrar imágenes explicativas
        self.current_image = None
        self.image_alpha = 0  # Para efecto de fade in/out
        
        # Diccionario con imágenes y sus rangos de frames para mostrar
        # Formato: "nombre_imagen": (frame_inicio, frame_fin)
        # frame_fin = -1 significa que se muestra hasta el final de la escena
        self.image_frames = {
            "prat": (950, -1)  # Mostrar desde frame 120 hasta el final
        }

    def get_texts(self):
        return [
            "Mientras el grupo 'Ensalada César' se encontraba sumergido en el caos del proyecto final de Estructura de Datos, un evento inesperado sacudió su realidad: sus computadores cobraron vida y los abdujeron sin previo aviso.",
            "",
            "Al abrir los ojos, se vieron atrapados en un universo alternativo lleno de lógica distorsionada, algoritmos flotantes... y mares infinitos.",
            "",
            "Ahora, en este mundo donde la programación y la fantasía chocan, deberán enfrentar a un enemigo legendario: Arturo Prat y su temido escuadrón de marines, comandando una flota de buques invisibles.",
            "",
            "Solo tú, como jugador, puedes ayudarlos. Usa bombas, torpedos, catalejos y cañones para detectar y destruir los barcos enemigos ocultos en la niebla digital.",
            "",
            "Planea tu estrategia, apunta con precisión y lleva al equipo de Ensalada César a la victoria!",
            "",
            "Solo así podrán romper la maldición del código eterno y regresar a su realidad... antes de que sea demasiado tarde.",
        ]

    def update_image_display(self):
        """Actualizar qué imagen mostrar basado en el frame actual"""
        current_frame = self.game.frame - self.start_frame
        
        # Buscar qué imagen debe mostrarse en el frame actual
        image_to_show = None
        for image_name, (start_frame, end_frame) in self.image_frames.items():
            if current_frame >= start_frame:
                if end_frame == -1 or current_frame <= end_frame:
                    image_to_show = image_name
                    break
        
        # Actualizar imagen actual
        if image_to_show != self.current_image:
            if image_to_show:
                self.current_image = image_to_show
                self.image_alpha = 0  # Iniciar fade in
            else:
                self.current_image = None
                self.image_alpha = 0  # Iniciar fade out

    def update_image_alpha(self):
        """Actualizar transparencia de la imagen para efectos de fade"""
        if self.current_image:
            if self.image_alpha < 255:
                self.image_alpha = min(255, self.image_alpha + 5)  # Fade in
        else:
            if self.image_alpha > 0:
                self.image_alpha = max(0, self.image_alpha - 5)  # Fade out

    def draw_explicative_image(self, screen):
        """Dibujar imagen explicativa centrada en el lado derecho"""
        if not self.current_image or self.image_alpha <= 0:
            return
            
        # Obtener la imagen
        img = self.game.assets.images[self.current_image]
        
        # Escala simple para la imagen
        scale_factor = 0.6  # Ajusta este valor para cambiar el tamaño
        display_width = int(img.get_width() * scale_factor)
        display_height = int(img.get_height() * scale_factor)
        
        # Escalar imagen
        scaled_img = pg.transform.smoothscale(img, (display_width, display_height))
        
        # Crear superficie con transparencia
        img_surface = pg.Surface((display_width, display_height), pg.SRCALPHA)
        img_surface.set_alpha(self.image_alpha)
        img_surface.blit(scaled_img, (0, 0))
        
        # Posición centrada en el lado derecho
        center_x = 3 * WIDTH // 4
        center_y = HEIGHT // 2
        
        # Calcular posición para centrar la imagen
        x = center_x - display_width // 2
        y = center_y - display_height // 2
        
        # Dibujar la imagen
        screen.blit(img_surface, (x, y))

    def update(self, screen):
        self.draw_frame(screen)
        
        # Actualizar efecto typewriter
        self.update_typewriter(self.get_texts())
        
        # Actualizar imagen a mostrar
        self.update_image_display()
        
        # Actualizar transparencia de imagen
        self.update_image_alpha()
        
        # Dibujar imagen explicativa
        self.draw_explicative_image(screen)
        
        # Dibujar box de texto
        self.draw_text_box(screen, self.get_texts())
        
        # Dibujar UI
        self.ui.update(screen)

class HistoryScene(Scene):
    def setup(self):
        self.ui = UIManager(self.game)
        
        # Agregar botón de regreso
        action_back = lambda: self.game.goto_scene("menu")
        self.ui.add_button("back", (120, 40), action_back, "Volver", topleft=(50, 50))
        
        # Datos de la tabla (vacíos por ahora)
        self.table_data = []
        
        # Configuración de la tabla
        self.table_width = 800
        self.table_height = 400
        self.table_x = (WIDTH - self.table_width) // 2
        self.table_y = (HEIGHT - self.table_height) // 2
        
        # Encabezados de columnas
        self.headers = ["ID", "Jugador", "Victoria", "Puntuación"]
        self.column_widths = [100, 200, 150, 150]  # Ancho para cada columna
        self.row_height = 40
        self.header_height = 50

    def draw_table(self, screen):
        # Dibujar fondo de la tabla
        table_rect = pg.Rect(self.table_x, self.table_y, self.table_width, self.table_height)
        pg.draw.rect(screen, (10, 70, 135), table_rect, border_radius=10)
        
        # Dibujar fondo del encabezado
        header_rect = pg.Rect(self.table_x, self.table_y, self.table_width, self.header_height)
        pg.draw.rect(screen, (13, 82, 154), header_rect, border_radius=10)
        
        # Dibujar encabezados
        font = pg.font.Font(None, 28)
        x_offset = self.table_x + 20  # Posición x inicial con padding
        
        for i, header in enumerate(self.headers):
            text = font.render(header, True, (255, 255, 255))
            text_rect = text.get_rect(midleft=(x_offset, self.table_y + self.header_height // 2))
            screen.blit(text, text_rect)
            x_offset += self.column_widths[i]
        
        # Dibujar línea separadora
        separator_y = self.table_y + self.header_height
        pg.draw.line(screen, (255, 255, 255), 
                    (self.table_x, separator_y), 
                    (self.table_x + self.table_width, separator_y), 2)
        
        # Dibujar datos de la tabla (vacíos por ahora)
        if not self.table_data:
            # Dibujar mensaje "No hay datos"
            no_data_font = pg.font.Font(None, 32)
            no_data_text = no_data_font.render("No hay datos disponibles", True, (255, 255, 255))
            no_data_rect = no_data_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
            screen.blit(no_data_text, no_data_rect)
        else:
            # Dibujar filas de datos (cuando hay datos disponibles)
            data_font = pg.font.Font(None, 24)
            for row_idx, row_data in enumerate(self.table_data):
                row_y = separator_y + (row_idx + 1) * self.row_height
                x_offset = self.table_x + 20
                
                for col_idx, cell_data in enumerate(row_data):
                    text = data_font.render(str(cell_data), True, (255, 255, 255))
                    text_rect = text.get_rect(midleft=(x_offset, row_y + self.row_height // 2))
                    screen.blit(text, text_rect)
                    x_offset += self.column_widths[col_idx]

    def update(self, screen):
        self.draw_frame(screen)
        self.draw_table(screen)
        self.ui.update(screen)

class FinalScene(TextScene):

    def custom_start(self):
        pass

    def start(self):
        self.ui = UIManager(self.game)
        self.start_frame = int(self.game.frame)
        
        # Botón para volver al menú
        action_menu = lambda: self.game.goto_scene("menu")
        self.ui.add_button("menu", (150, 50), action_menu, "Menú Principal", center=(WIDTH//2 - 100, HEIGHT-80))
        
        # Botón para jugar de nuevo
        action_play_again = lambda: self.game.goto_scene("setup")
        self.ui.add_button("play_again", (150, 50), action_play_again, "Jugar de Nuevo", center=(WIDTH//2 + 100, HEIGHT-80))
        
        # Variables para efectos de celebración
        self.frame_counter = 0
        self.celebration_particles = []

        self.custom_start()


    def draw_prat(self, screen):
        """Dibujar imagen de Prat derrotado arriba de los botones"""
        # Obtener la imagen
        img = self.game.assets.images[self.prat_asset]
        
        # Calcular tamaño de la imagen (mantener proporción)
        max_width = 400
        max_height = 300
        
        # Calcular dimensiones manteniendo proporción
        img_ratio = img.get_width() / img.get_height()
        if img_ratio > max_width / max_height:
            # Imagen más ancha que alta
            display_width = max_width
            display_height = int(max_width / img_ratio)
        else:
            # Imagen más alta que ancha
            display_height = max_height
            display_width = int(max_height * img_ratio)
        
        # Escalar imagen
        scaled_img = pg.transform.smoothscale(img, (display_width, display_height))
        
        # Calcular posición centrada horizontalmente, arriba de los botones
        x = (WIDTH - display_width) // 2
        y = HEIGHT - 150 - display_height  # 150 píxeles arriba de los botones
        
        # Dibujar la imagen
        screen.blit(scaled_img, (x, y))

    def draw_text(self, screen):
        """Dibujar texto de victoria con efecto typewriter"""
        font_large = pg.font.Font(None, 72)
        font_medium = pg.font.Font(None, 36)
        font_small = pg.font.Font(None, 28)
        
        y_offset = HEIGHT // 4
        texts = self.get_texts()
        
        for i, text in enumerate(texts):
            if i < self.current_paragraph:
                # Texto completo
                display_text = text
            elif i == self.current_paragraph:
                # Texto actual con typewriter
                display_text = text[:self.current_char]
            else:
                # Texto futuro (no mostrar)
                continue
            
            if display_text:
                # Seleccionar fuente según el texto
                if i == 0:  # "¡VICTORIA!"
                    font = font_large
                    color = (255, 215, 0)  # Dorado
                elif i == 1:  # Primera línea de descripción
                    font = font_medium
                    color = (255, 255, 255)
                else:  # Resto del texto
                    font = font_small
                    color = (200, 200, 200)
                
                text_surface = font.render(display_text, True, color)
                text_rect = text_surface.get_rect(center=(WIDTH//2, y_offset))
                screen.blit(text_surface, text_rect)
                
                y_offset += font.get_height() + 20

    def update(self, screen):
        self.draw_frame(screen)
        self.update_typewriter(self.get_texts())
        self.draw_text(screen)
        self.draw_prat(screen)
        self.loop(screen)
        self.ui.update(screen)

class VictoryScene(FinalScene):
    prat_asset = "prat_defeated"

    def custom_start(self):
        self.generate_particles()

    def get_texts(self):
        return [
            "¡VICTORIA!",
            "¡El equipo de Ensalada César ha triunfado!",
            "Has derrotado a Arturo Prat y su flota invisible.",
            "Los estudiantes pueden regresar a su realidad... ¡Por ahora!",
        ]
    
    def generate_particles(self):
        """Generar partículas de celebración"""
        for _ in range(50):
            particle = {
                'x': random.randint(0, WIDTH),
                'y': random.randint(0, HEIGHT),
                'vx': random.uniform(-3, 3),
                'vy': random.uniform(-5, -1),
                'life': random.randint(60, 120),
                'color': random.choice([(255, 215, 0), (255, 255, 255), (255, 100, 100), (100, 255, 100), (100, 100, 255)])
            }
            self.celebration_particles.append(particle)

    def update_particles(self):
        """Actualizar partículas de celebración"""
        for particle in self.celebration_particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['vy'] += 0.1  # Gravedad
            particle['life'] -= 1
            
            if particle['life'] <= 0:
                self.celebration_particles.remove(particle)
        
        # Regenerar partículas si se acabaron
        if len(self.celebration_particles) < 20:
            self.generate_particles()

    def draw_particles(self, screen):
        """Dibujar partículas de celebración"""
        for particle in self.celebration_particles:
            alpha = min(255, particle['life'] * 3)
            color = (*particle['color'], alpha)
            
            # Crear superficie con transparencia
            particle_surf = pg.Surface((4, 4), pg.SRCALPHA)
            pg.draw.circle(particle_surf, color, (2, 2), 2)
            screen.blit(particle_surf, (particle['x'], particle['y']))

    def loop(self, screen):
        self.update_particles()
        self.draw_particles(screen)
    
class DefeatScene(FinalScene):
    prat_asset = "prat_winner"

    def get_texts(self):
        return [
            "¡DERROTA!",
            "¡El equipo de Ensalada César ha sido derrotado!",
            "Has sido derrotado por Arturo Prat y su flota invisible.",
            "Los estudiantes deben regresar a su realidad... ¡Por ahora!",
        ]
    
    def loop(self, screen):
        pass
    

class MatchScene(Scene):
    def setup(self, grid, objects):
        self.init_match(grid, objects)
        self.game.event_manager.add_action_key(pg.K_SPACE, self.end_turn)
        self.game.event_manager.add_action_key(pg.K_r, self.rotate_torpedo)

    def handle_click(self, pos):
        # Verificar si el clic está en el panel de objetos
        panel_x = WIDTH // 4 - self.object_panel.width // 2
        panel_y = HEIGHT // 3 + self.gridB.grid_height // 2 + 20
        panel_rect = pg.Rect(panel_x, panel_y, self.object_panel.width, self.object_panel.height)
        
        if panel_rect.collidepoint(pos):
            self.handle_object_panel_click(pos)
            return True
            
        # Si hay un objeto seleccionado, manejar clic en la cuadrícula
        if self.selected_object:
            self.handle_grid_object_click(pos)
            return True
            
        # Manejo normal de clic en la cuadrícula enemiga
        self.gridA.handle_click(pos)

    def handle_object_panel_click(self, pos):
        # Convertir posición global a posición local del panel
        local_pos = (pos[0] - self.object_panel.panel_x, pos[1] - self.object_panel.panel_y)
        
        # Calcular diseño de cuadrícula del panel
        cell_width = self.object_panel.width // 3
        cell_height = 90
        padding = 10
        
        # Verificar clic en cada elemento
        for i, (item_name, item) in enumerate(self.object_panel.items.items()):
            if item['quantity'] <= 0:
                continue
                
            col = i % 3
            row = i // 3
            
            # Calcular posición de la caja
            box_rect = pg.Rect(
                col * cell_width + padding,
                row * cell_height + padding,
                cell_width - padding * 2,
                cell_height - padding * 2
            )
            
            if box_rect.collidepoint(local_pos):
                # Seleccionar este objeto
                self.selected_object = item_name
                self.gridA.set_selected_object(item_name)
                hover_sound = self.game.assets.audio["sfx"]["hover"]
                hover_sound.play()
                return

    def handle_grid_object_click(self, pos):
        # Verificar si el clic está en la cuadrícula enemiga
        mouse_vec = pg.Vector2(pos) - self.gridA.start_pos
        for i in range(self.gridA.size[0]):
            for j in range(self.gridA.size[1]):
                w = self.gridA.cell_size + self.gridA.margin
                s = self.gridA.cell_size
                rect = pg.Rect(i * w, j * w, s, s)
                if rect.collidepoint(mouse_vec):
                    # Para torpedo, usar orientación manual solo si la posición es válida
                    orientation = 0
                    if self.selected_object == 'torpedo':
                        if self.gridA.is_valid_torpedo_position(i, j):
                            orientation = self.gridA.torpedo_orientation
                        else:
                            return  # No permitir colocar torpedo en posición inválida

                    self.use_object_at_position(i, j, orientation)
                    return

    def use_object_at_position(self, x, y, orientation=0):
        if not self.selected_object or self.object_panel.items[self.selected_object]['quantity'] <= 0:
            return
            
        if self.selected_object == 'torpedo' and orientation == 0:
            return

        # Decrementar cantidad
        self.object_panel.items[self.selected_object]['quantity'] -= 1

        # Agregar objeto usado a la lista del turno
        new_object = {
            'object_id': self.object_panel.items[self.selected_object]['id'],
            'x': x,
            'y': y
        }

        if self.selected_object == 'torpedo':
            new_object['orientation'] = orientation
        
        self.used_objects.append(new_object)
        # Agregar objeto a la lista de objetos colocados para mostrar visualmente
        self.placed_objects.append({'object_name': self.selected_object, **new_object})
        
        # Limpiar selección
        self.selected_object = None
        self.gridA.set_selected_object(None)

    def save_config(self):

        grid = self.gridB

        # Limpiar directorio de caché
        if os.path.exists("cache"):
            shutil.rmtree("cache")
        os.makedirs("cache")

        with open(f"cache/{self.id}.txt", "w") as f:
            # Escribir ID de partida
            f.write(f"{self.id}\n")
            
            # Escribir tamaño de cuadrícula
            f.write(f"{grid.size[0]} {grid.size[1]}\n")
            
            # Crear y escribir el estado de la cuadrícula
            grid_state = [[0 for _ in range(grid.size[1])] for _ in range(grid.size[0])]
            
            # Llenar posiciones de barcos
            for boat in grid.boats:
                x, y = boat['pos']
                for i in range(boat['size']):
                    if boat.get('direction', 'h') == 'h':  # Por defecto horizontal si no está establecido
                        grid_state[y][x+i] = boat['id']
                    else:  # vertical
                        grid_state[y+i][x] = boat['id']
            
            # Escribir el estado de la cuadrícula
            for row in grid_state:
                f.write(" ".join(map(str, row)) + "\n")

            # Escribir información de objetos
            objects_with_quantity = [item for item in self.game.scenes["setup"].object_panel.items.values() if item['quantity'] > 0]
            f.write(f"N objetos: {len(objects_with_quantity)}\n")
            
            # Escribir id y cantidad de cada objeto
            for item in objects_with_quantity:
                f.write(f"{item['id']} {item['quantity']}\n")

    def start_backend(self):

        if DEV or not os.path.exists("main.exe"):
            # gcc TDAS/*.c main.c -o main.exe
            try:
                result = subprocess.run(["gcc", "TDAS/*.c", "main.c", "-o", "main.exe"], 
                                      capture_output=True, text=True, check=True)
                print("Compilación exitosa")
            except subprocess.CalledProcessError as e:
                print(f"Error de compilación: {e}")
                print(f"stdout: {e.stdout}")
                print(f"stderr: {e.stderr}")
                return
            except FileNotFoundError:
                print("Error: gcc no encontrado. Asegúrate de tener GCC instalado.")
                return

        try:
            pipe = subprocess.PIPE
            self.proc = subprocess.Popen(["./main.exe", "iniciarJuego", f"{self.id}.txt"], 
                                       stdin=pipe, stdout=pipe, stderr=pipe, text=True, encoding='utf-8')
            
            # Leer la primera línea de respuesta
            first_response = self.proc.stdout.readline()
            if first_response:
                print(first_response, end='')
            else:
                print("Error: No se recibió respuesta del backend")
                
        except Exception as e:
            print(f"Error al iniciar el backend: {e}")
            self.proc = None

    def init_match(self, grid, objects):

        margin = WIDTH // 20
        self.gridA = EnemyGrid(self, GRID_SIZE, WIDTH // 2 - margin*2, HEIGHT * 0.9, boats=[])
        self.gridB = Grid(self, GRID_SIZE, HEIGHT // 2 - margin*2, HEIGHT * 0.8, boats=grid.boats)

        # Agregar panel de objetos para uso en juego
        self.object_panel = ObjectPanel(self.game, WIDTH // 4, HEIGHT // 6)
        self.object_panel.set_items(objects)
        
        # Estado de selección de objetos
        self.selected_object = None
        
        # Lista de objetos usados en este turno
        self.used_objects = []
        
        # Lista de objetos colocados en la cuadrícula (para mostrar visualmente)
        self.placed_objects = []

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
        # Agregar botón 'Terminar Turno'
        self.ui = UIManager(self.game)
        action = self.end_turn
        self.ui.add_button("end_turn", (180, 50), action, "Terminar Turno", topleft=(WIDTH-220, HEIGHT-80))
        
        # Agregar botón 'Salir' en la esquina inferior izquierda
        exit_action = lambda: self.game.goto_scene("menu")
        self.ui.add_button("exit", (120, 50), exit_action, "Salir", topleft=(40, HEIGHT-80))
        
        self.turn_ended = False

        self.game.event_manager.add_action_key(pg.K_SPACE, self.end_turn)
        
        # Registrar cheat de bombas en el EventManager
        self.game.event_manager.add_cheat_sequence("bomb_cheat", 241, 3, self.activate_bomb_cheat)

    def activate_bomb_cheat(self):
        """Activar el cheat de bombas"""
        if 'bomb' in self.object_panel.items:
            # Agregar 10 bombas
            self.object_panel.items['bomb']['quantity'] += 10
            self.object_panel.items['torpedo']['quantity'] += 10
            
            # Reproducir sonido de éxito
            create_sound = self.game.assets.audio["sfx"]["create"]
            create_sound.play()
            
            print("¡Cheat activado! +10 bombas")
        else:
            print("Error: No se encontró el objeto 'bomb' en el panel")

    def end_turn(self):
        if self.gridA.selected_target is not None or self.used_objects:
            # Verificar si el proceso backend existe
            if self.proc is None:
                print("Error: No hay proceso backend activo")
                # Limpiar estado del turno sin enviar mensajes
                self.gridA.clear_target()
                self.used_objects = []
                self.placed_objects = []
                self.turn_ended = True
                return
            
            # Verificar si el proceso backend sigue vivo
            if self.proc.poll() is not None:
                print("Error: El proceso backend ha terminado inesperadamente")
                # Limpiar estado del turno sin enviar mensajes
                self.gridA.clear_target()
                self.used_objects = []
                self.placed_objects = []
                self.turn_ended = True
                return
            
            # Calcular número total de mensajes
            num_messages = 0
            
            if self.gridA.selected_target is not None:
                num_messages += 1  # Mensaje de ataque
                
            num_messages += len(self.used_objects)  # Mensajes de objetos usados
            
            # Enviar mensaje de nuevo turno
            msg = f'8 {num_messages}\n'
            
            # Enviar mensaje de ataque si hay objetivo seleccionado
            if self.gridA.selected_target is not None:
                msg += f"4 {self.gridA.selected_target[0]} {self.gridA.selected_target[1]}\n"
            
            # Enviar mensajes de objetos usados
            for obj in self.used_objects:
                if obj['object_id'] == 3:
                    msg += f"5 {obj['object_id']} {obj['x']} {obj['y']} {obj['orientation']}\n"
                else:
                    msg += f"5 {obj['object_id']} {obj['x']} {obj['y']}\n"
            
            print(msg, end='')
            
            try:
                self.proc.stdin.write(msg)
                self.proc.stdin.flush()
            except (OSError, IOError) as e:
                print(f"Error al enviar mensaje al backend: {e}")
                # Limpiar estado del turno sin enviar mensajes
                self.gridA.clear_target()
                self.used_objects = []
                self.placed_objects = []
                self.turn_ended = True
                return

            try:
                # Leer la primera línea (debería ser "8 X" para número de mensajes)
                first_line = self.proc.stdout.readline().strip()
                
                # Analizar el número de mensajes
                if first_line.startswith("8 "):
                    num_messages = int(first_line.split()[1])
                    print(first_line)
                    
                    # Leer todos los mensajes
                    for i in range(num_messages):
                        message = self.proc.stdout.readline().strip()
                        print(message, end='\n')

                        message_type = int(message.split()[0])

                        if message_type == 4:
                            x, y = map(int, message.split()[1:])
                            self.gridB.mark_cell(x, y, 99)

                        if message_type == 9: # Informe de Estado Casilla
                            x, y, value = map(int, message.split()[1:])
                            self.gridA.update_cell(x, y, value)

                        if message_type == 777: # Código de Fin de Juego

                            self.proc.kill()

                            result = int(message.split()[1])
                            if result == 1:
                                self.game.goto_scene("defeat")
                            elif result == 2:
                                self.game.goto_scene("victory")  

                            return
                        # Aquí puedes procesar cada mensaje según sea necesario
            except (OSError, IOError) as e:
                print(f"Error al leer respuesta del backend: {e}")
            
            # Limpiar estado del turno
            self.gridA.clear_target()
            self.used_objects = []  # Limpiar lista de objetos usados
            self.placed_objects = []  # Limpiar lista de objetos colocados visualmente
            self.turn_ended = True

    def draw_fog(self, screen, box):
        fog_surf = pg.Surface(box.size, pg.SRCALPHA)
        fog_surf.fill((0, 0, 0, 20))
        screen.blit(fog_surf, box.topleft)

    def update(self, screen):
        self.draw_frame(screen)

        # Dibujar la cuadrícula
        posA = pg.Vector2(2 * WIDTH / 3, HEIGHT / 2)
        posB = pg.Vector2(WIDTH / 4, HEIGHT / 3)

        self.gridA.update(screen, *posA)
        self.gridB.update(screen, *posB)

        w_a = self.gridA.grid_width
        gridA_rect = pg.Rect(*self.gridA.start_pos, w_a, w_a)

        self.draw_fog(screen, gridA_rect)
        self.gridA.draw_state(screen, *posA)

        # Dibujar panel de objetos debajo de gridB
        panel_x = WIDTH // 4 - self.object_panel.width // 2
        panel_y = HEIGHT // 3 + self.gridB.grid_height // 2 + 20
        self.object_panel.update(screen, panel_x, panel_y)

        # Manejar clic para apuntar
        if self.game.event_manager.is_clicking and not self.turn_ended:
            mouse_pos = pg.mouse.get_pos() - self.gridB.start_pos
            for i in range(self.gridB.size[0]):
                for j in range(self.gridB.size[1]):
                    w = self.gridB.cell_size + self.gridB.margin
                    s = self.gridB.cell_size
                    rect = pg.Rect(i * w, j * w, s, s)
                    if rect.collidepoint(mouse_pos):
                        self.gridB.handle_click(i, j)

        self.ui.update(screen)

    def rotate_torpedo(self):
        """Rotar la orientación del torpedo"""
        if hasattr(self, 'gridA'):
            self.gridA.rotate_torpedo()

class SetupScene(Scene):
    def setup(self):
        self.grid = SetupGrid(self, GRID_SIZE, WIDTH, HEIGHT * 0.8)
        self.object_panel = SetupObjectPanel(self.game, WIDTH // 5, HEIGHT * 0.8)

        new_boat = lambda size: {'size': size, 'pos': None, 'direction': 'h', 'selected': False }
        self.boats = [ new_boat(2), new_boat(3), new_boat(3), new_boat(4), new_boat(5) ]

        self.ui = UIManager(self.game)

        action = lambda: self.start_match()
        self.ui.add_button( "start", (120, 40), action, "Comenzar", center=(WIDTH - 90, HEIGHT - 50))

        action = lambda: self.game.goto_scene("menu")
        self.ui.add_button("back", (120, 40), action, "Volver", center=(90, HEIGHT - 50))

        # Agregar botón de aleatorización en la parte superior del panel selector de barcos
        randomize_action = lambda: self.randomize_boats()
        randomize_center = (140, HEIGHT//2 - HEIGHT//3 - 30)
        dice_img = self.game.assets.images["dice"]
        self.ui.add_button("randomize", (50, 50), randomize_action, image=dice_img, opacity=0.4, center=randomize_center)

        # Agregar botón de limpiar junto al botón de aleatorización
        clear_action = lambda: self.clear_all_boats()
        clear_center = (200, HEIGHT//2 - HEIGHT//3 - 30)
        clear_img = self.game.assets.images["clear"]
        self.ui.add_button("clear", (50, 50), clear_action, image=clear_img, opacity=0.4, center=clear_center)

        self.game.event_manager.add_action_key(pg.K_r, self.rotate_selected_boat)

    def randomize_boats(self):
        # Obtener barcos que aún no han sido colocados
        unplaced_boats = [boat for boat in self.boats if boat['pos'] is None]
        
        if not unplaced_boats:
            # Todos los barcos ya están colocados, solo reproducir sonido de denegación
            deny_sound = self.game.assets.audio["sfx"]["deny"]
            deny_sound.play()
            return
        
        # Intentar colocar cada barco no colocado aleatoriamente
        for boat in unplaced_boats:
            attempts = 0
            max_attempts = 100
            
            while attempts < max_attempts:
                # Posición y dirección aleatorias
                x = random.randint(0, self.grid.size[0] - 1)
                y = random.randint(0, self.grid.size[1] - 1)
                direction = random.choice(['h', 'v'])
                
                # Verificar si el barco cabe en esta posición y dirección
                if direction == 'h' and x + boat['size'] <= self.grid.size[0]:
                    # Verificar si todas las celdas están vacías
                    can_place = True
                    for i in range(boat['size']):
                        if not self.is_cell_empty(x + i, y):
                            can_place = False
                            break
                    
                    if can_place:
                        boat['pos'] = (x, y)
                        boat['direction'] = direction
                        self.grid.add_boat(boat.copy())
                        break
                        
                elif direction == 'v' and y + boat['size'] <= self.grid.size[1]:
                    # Verificar si todas las celdas están vacías
                    can_place = True
                    for i in range(boat['size']):
                        if not self.is_cell_empty(x, y + i):
                            can_place = False
                            break
                    
                    if can_place:
                        boat['pos'] = (x, y)
                        boat['direction'] = direction
                        self.grid.add_boat(boat.copy())
                        break
                
                attempts += 1
            
            # Si no pudimos colocar el barco después del máximo de intentos, saltarlo
            if attempts >= max_attempts:
                continue
        
        # Reproducir efecto de sonido
        create_sound = self.game.assets.audio["sfx"]["create"]
        create_sound.play()

    def is_cell_empty(self, x, y):
        """Verificar si una celda está vacía (ningún barco la ocupa)"""
        for boat in self.grid.boats:
            if boat['pos'] is None:
                continue
                
            boat_x, boat_y = boat['pos']
            boat_size = boat['size']
            direction = boat.get('direction', 'h')
            
            if direction == 'h':
                if y == boat_y and x >= boat_x and x < boat_x + boat_size:
                    return False
            else:  # vertical
                if x == boat_x and y >= boat_y and y < boat_y + boat_size:
                    return False
        
        return True

    def clear_all_boats(self):
        # Limpiar todos los barcos de la cuadrícula
        self.grid.boats = []
        
        # Restablecer todos los barcos al estado no colocado
        for boat in self.boats:
            boat['pos'] = None
            boat['selected'] = False
        
        # Reproducir efecto de sonido
        destroy_sound = self.game.assets.audio["sfx"]["destroy"]
        destroy_sound.play()

    def start_match(self):
        self.game.scenes["match"]
        self.game.goto_scene("match", grid=self.grid, objects=self.object_panel.items)

    def place_boat(self, pos):
        # Encontrar el barco seleccionado
        selected_boat = None
        for boat in self.boats:
            if boat['selected']:
                selected_boat = boat
                break
        
        if not selected_boat:
            return
            
        # Verificar si el barco puede ser colocado en esta posición
        if not self.grid.preview_pos:
            return
        
        create_sound = self.game.assets.audio["sfx"]["create"]
        create_sound.play()
            
        # Colocar el barco
        selected_boat['pos'] = self.grid.preview_pos
        selected_boat['direction'] = selected_boat.get('direction', 'h')  # Asegurar que la dirección esté establecida
        selected_boat['selected'] = False
        
        # Agregar el barco a la cuadrícula
        self.grid.add_boat(selected_boat.copy())
        
        # Remover el barco de los barcos disponibles
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
        # Verificar si el clic está en el panel de objetos
        panel_x = WIDTH - self.object_panel.width - 50
        panel_y = HEIGHT // 2 - self.object_panel.height // 2
        panel_rect = pg.Rect(panel_x, panel_y, self.object_panel.width, self.object_panel.height)
        
        if panel_rect.collidepoint(pos):
            self.object_panel.handle_click(pos)
            return True
            
        # Manejar colocación de barco en clic
        if self.grid.preview_pos:
            self.place_boat(self.grid.preview_pos)
            return True
            
        return False

    def update(self, screen):
        self.draw_frame(screen)

        self.grid.update(screen, WIDTH / 2 - 60, HEIGHT / 2) 
        rect = pg.Rect(0, 0, 80, 2*HEIGHT//3)
        rect.center = (170, HEIGHT / 2)
        pg.draw.rect(screen, (13, 82, 154), rect, border_radius=5)

        self.ui.update(screen)
        self.object_panel.update(screen, WIDTH - self.object_panel.width - 100, HEIGHT // 2 - self.object_panel.height // 2)

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

        

class InfoBox:

    margin = 10
    padding = 10
    opacity = 100
    message = []

    def __init__(self, game, width, height):
        self.game = game
        self.width = width
        self.height = height

    def add_message(self, message):
        self.message.append(message)

    def wrap_text(self, text, font, max_width):
        # First split by newlines
        paragraphs = text.split('\n')
        all_lines = []
        
        for paragraph in paragraphs:
            words = paragraph.split(' ')
            current_line = []
            
            for word in words:
                # Test if adding the word exceeds the width
                test_line = ' '.join(current_line + [word])
                test_width = font.size(test_line)[0]
                
                if test_width <= max_width - (self.padding * 2):
                    current_line.append(word)
                else:
                    if current_line:
                        all_lines.append(' '.join(current_line))
                    current_line = [word]
            
            if current_line:
                all_lines.append(' '.join(current_line))
            
        return all_lines

    def draw(self, screen):
        if not self.message:
            return

        x = self.margin
        y = screen.get_height() - self.height - self.margin

        surf = pg.Surface((self.width, self.height), pg.SRCALPHA)
        surf.fill((0, 0, 0, self.opacity))

        font = pg.font.Font(None, 24)
        current_y = self.padding
        
        for message in self.message:
            # Wrap the text
            wrapped_lines = self.wrap_text(message, font, self.width)
            
            # Draw each line
            for line in wrapped_lines:
                text = font.render(line, True, (255, 255, 255))
                surf.blit(text, (self.padding, current_y))
                current_y += text.get_height() + 2  # Add small spacing between lines
                
                # If we exceed the height, stop drawing
                if current_y > self.height - self.padding:
                    break

        screen.blit(surf, (x, y))
        self.message = []

class UIManager:
    def __init__(self, game):
        self.game = game
        self.buttons = {}
        self.was_hovering = {}  # Track hover state for each button

    def add_button(self, name, size, click, text=None, image=None, opacity=1.0, topleft=None, center=None):
        rect = pg.Rect(0, 0, size[0], size[1])
        if center is not None:
            rect.center = center
        elif topleft is not None:
            rect.topleft = topleft
            
        self.buttons[name] = {
            "rect": rect,
            "click": click,
            "text": text,
            "image": image,
            "opacity": opacity
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
                hover_sound = self.game.assets.audio["sfx"]["hover"]
                hover_sound.play()
            
            self.was_hovering[name] = is_hovering
            
            # Create a surface for the button with alpha support
            btn_surf = pg.Surface((btn["rect"].width, btn["rect"].height), pg.SRCALPHA)
            
            # Draw button background with opacity
            btn_color = (10, 70, 135) if is_hovering else (13, 82, 154)
            pg.draw.rect(btn_surf, btn_color, (0, 0, btn["rect"].width, btn["rect"].height), 0, 10)
            
            # Draw image if provided
            if btn["image"]:
                # Scale image to fit button size with some padding
                img_size = min(btn["rect"].width, btn["rect"].height) - 10
                scaled_img = pg.transform.smoothscale(btn["image"], (img_size, img_size))
                
                # Apply opacity to image
                if btn["opacity"] < 1.0:
                    scaled_img.set_alpha(int(255 * btn["opacity"]))
                
                img_rect = scaled_img.get_rect(center=(btn["rect"].width//2, btn["rect"].height//2))
                btn_surf.blit(scaled_img, img_rect)
            # Draw text if provided (and no image)
            elif btn["text"]:
                font = pg.font.Font(None, 24)
                text_color = (255, 255, 255, int(255 * btn["opacity"]))
                text = font.render(btn["text"], True, text_color)
                text_rect = text.get_rect(center=(btn["rect"].width//2, btn["rect"].height//2))
                btn_surf.blit(text, text_rect)
            
            # Draw the button surface onto the screen
            screen.blit(btn_surf, btn["rect"])

class AnimatedWaveBackground:
    def __init__(self, wave_image, screen_width, screen_height, num_waves=16):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.wave_image = wave_image
        self.num_waves = num_waves
        self.frame_counter = 0
        
        self.wave_layers = []
        
        base_wave_height = int(screen_height * 0.25)
        overlap_factor = 0.3 # From user's edit
        
        for i in range(num_waves):
            # Respect user's edit for wave height
            aspect_ratio = self.wave_image.get_width() / self.wave_image.get_height()
            scaled_height = base_wave_height * 2 
            scaled_width = int(scaled_height * aspect_ratio)

            scaled_wave = pg.transform.smoothscale(self.wave_image, (scaled_width, scaled_height))
            
            wave_surface = scaled_wave.copy()

            # Create a brightness factor (0.0 = black, 1.0 = original color)
            brightness = 1.0 - (i / (num_waves - 1) * 0.7)

            # Create a color to multiply the wave image with
            tint_value = int(255 * brightness)
            tint_color = (tint_value, tint_value, tint_value)

            # Apply the darkening effect by multiplying the wave's colors
            wave_surface.fill(tint_color, None, pg.BLEND_RGB_MULT)
            
            # Position waves to overlap
            y_overlap = scaled_height * overlap_factor
            y_pos = (screen_height - scaled_height) - (i * y_overlap) + (num_waves/2 * y_overlap)

            # Define movement properties for each wave
            direction = 1 if i % 2 == 0 else -1
            speed = 0.2 + (i * 0.01)
            frequency = 0.01 + (i * 0.007)
            amplitude = 10 + (i * 0.5)

            if i % 3 == 0:
                speed *= 1.4
                frequency *= 1.1

            self.wave_layers.append({
                'surface': wave_surface,
                'y_pos_base': y_pos,
                'x_offset': random.randint(0, screen_width),
                'direction': direction,
                'speed': speed,
                'frequency': frequency,
                'amplitude': amplitude
            })
    
    def update(self):
        self.frame_counter += 1
        for wave in self.wave_layers:
            wave['x_offset'] += wave['direction'] * wave['speed']
            
            if abs(wave['x_offset']) > wave['surface'].get_width():
                wave['x_offset'] = 0

    def draw(self, screen):
        for wave in sorted(self.wave_layers, key=lambda w: w['y_pos_base']):
            sin_offset = math.sin(self.frame_counter * wave['frequency']) * wave['amplitude']
            x_pos = wave['x_offset']
            y_pos = wave['y_pos_base'] + sin_offset
            
            wave_width = wave['surface'].get_width()
            
            # Calculate how many wave instances we need to cover the entire screen
            # We need to cover from -wave_width to screen_width + wave_width to ensure no gaps
            start_x = -wave_width
            end_x = self.screen_width + wave_width
            
            # Calculate the first wave position that covers the left edge
            first_wave_x = x_pos
            while first_wave_x > start_x:
                first_wave_x -= wave_width
            
            # Draw waves from left to right to ensure complete coverage
            current_x = first_wave_x
            while current_x < end_x:
                screen.blit(wave['surface'], (current_x, y_pos))
                current_x += wave_width

class AssetManager:
    def load(self):
        self.audio = {
            "music": {
                "main": "assets/audio/menu.mp3",
            },
            "sfx": {
                "hover": pg.mixer.Sound("assets/audio/hover.wav"),
                "create": pg.mixer.Sound("assets/audio/create.wav"),
                "deny": pg.mixer.Sound("assets/audio/deny.wav"),
                "destroy": pg.mixer.Sound("assets/audio/destroy.wav"),
            }
        }
        for audio in self.audio["sfx"].values():
            audio.set_volume(0.1)

        self.images = {
            "menu": pg.image.load("assets/img/menu.png").convert_alpha(),
            "bomb": pg.image.load("assets/img/bomb.png").convert_alpha(),
            "spyglass": pg.image.load("assets/img/spyglass.png").convert_alpha(),
            "torpedo": pg.image.load("assets/img/torpedo.png").convert_alpha(),
            "target": pg.image.load("assets/img/target.png").convert_alpha(),
            "broken": pg.image.load("assets/img/broken.png").convert_alpha(),
            "dice": pg.image.load("assets/img/dice.png").convert_alpha(),
            "clear": pg.image.load("assets/img/clear.png").convert_alpha(),
            "title": pg.image.load("assets/img/tittle.png").convert_alpha(),
            "wave": pg.image.load("assets/img/wave.png").convert_alpha(),
            "prat": pg.image.load("assets/img/prat.png").convert_alpha(),
            "prat_defeated": pg.image.load("assets/img/prat_defeated.png").convert_alpha(),
            "prat_winner": pg.image.load("assets/img/prat_winner.png").convert_alpha(),
        }

        # Create animated wave background with more waves
        self.background = AnimatedWaveBackground(self.images["wave"], WIDTH, HEIGHT, num_waves=12)

class Game:
    def __init__(self, win_size):
        self.running = True
        pg.mixer.init()
        
        # Configurar volumen general (0.0 a 1.0)
        pg.mixer.music.set_volume(0.3)  # Volumen para música de fondo
        
        self.win_size = win_size
        self.frame = 0

        self.event_manager = EventManager(self)
        self.assets = AssetManager()
        self.info_box = InfoBox(self, WIDTH // 3, HEIGHT // 5 )

    def goto_scene(self, scene_name, *args, **kwargs):
        self.current_scene = self.scenes[scene_name]
        self.current_scene.setup(*args, **kwargs)
        
    def setup(self):
        self.assets.load()
        pg.mixer.music.load(self.assets.audio["music"]["main"])
        pg.mixer.music.play(-1)

        self.scenes = {
            "menu": MenuScene(self),
            "intro": IntroScene(self),
            "setup": SetupScene(self),
            "match": MatchScene(self),
            "history": HistoryScene(self),
            "victory": VictoryScene(self),
            "defeat": DefeatScene(self)
        }

        # Registrar cheats globalmente
        self.event_manager.add_cheat_sequence("bomb_cheat", pg.K_F10, 3, self.activate_bomb_cheat)

        self.current_scene = self.scenes["setup"] if DEV else self.scenes["menu"]
        self.current_scene.setup()

    def activate_bomb_cheat(self):
        """Activar el cheat de bombas - solo funciona en MatchScene"""
        if hasattr(self.current_scene, 'object_panel') and 'bomb' in self.current_scene.object_panel.items:
            # Agregar 10 bombas
            self.current_scene.object_panel.items['bomb']['quantity'] += 10
            self.current_scene.object_panel.items['torpedo']['quantity'] += 10
            
            # Reproducir sonido de éxito
            create_sound = self.assets.audio["sfx"]["create"]
            create_sound.play()
            
            print("¡Cheat activado! +10 bombas")
        else:
            print("Cheat solo disponible durante el juego")

    def update(self, screen):
        self.event_manager.update()
        
        screen.fill((12, 139, 221))
        self.assets.background.update()
        self.assets.background.draw(screen)

        self.current_scene.update(screen)
        if self.current_scene.ui:
            self.current_scene.ui.update(screen)
        self.frame += 1

        self.info_box.draw(screen)

        return self.running

class EventManager:
    def __init__(self, game):
        self.game = game
        self.is_clicking = False
        self.actions = {}
        self.cheat_sequences = {}  # Para manejar secuencias de cheat
        self.cheat_timeout_max = 60  # 1 segundo a 60 FPS

    def add_action_key(self, key, callback):
        self.actions[key] = callback

    def add_cheat_sequence(self, name, key, sequence_length, callback):
        """Agregar una secuencia de cheat
        name: nombre del cheat
        key: tecla que activa el cheat
        sequence_length: número de presiones requeridas
        callback: función a ejecutar cuando se active el cheat
        """
        self.cheat_sequences[name] = {
            'key': key,
            'sequence_length': sequence_length,
            'callback': callback,
            'sequence': [],
            'timeout': 0
        }

    def handle_cheat_key(self, key):
        """Manejar presiones de tecla para cheats"""
        current_time = self.game.frame
        
        for cheat_name, cheat_data in self.cheat_sequences.items():
            if cheat_data['key'] == key:
                # Agregar timestamp a la secuencia
                cheat_data['sequence'].append(current_time)
                
                # Mantener solo las últimas presiones necesarias
                if len(cheat_data['sequence']) > cheat_data['sequence_length']:
                    cheat_data['sequence'].pop(0)
                
                # Verificar si tenemos la secuencia completa
                if len(cheat_data['sequence']) == cheat_data['sequence_length']:
                    # Verificar timeout
                    time_diff = cheat_data['sequence'][-1] - cheat_data['sequence'][0]
                    if time_diff <= self.cheat_timeout_max:
                        # Activar cheat
                        cheat_data['callback']()
                        cheat_data['sequence'].clear()
                    else:
                        # Timeout expirado, limpiar secuencia
                        cheat_data['sequence'].clear()
                break

    def handle_key_down(self, key):
        if key == pg.K_ESCAPE:
            self.game.running = False

        if key in self.actions:
            self.actions[key]()

        # Verificar si es una tecla de cheat
        self.handle_cheat_key(key)

    def handle_click(self, pos):
        scene = self.game.current_scene
        if scene.ui:
            scene.ui.mousePressed(pos)
        if scene.handle_click:
            scene.handle_click(pos)

    def update(self):
        self.is_clicking = False
        for ev in pg.event.get():
            if ev.type == pg.QUIT:
                self.game.running = False

            elif ev.type == pg.KEYDOWN:
                self.handle_key_down(ev.key)

            elif ev.type == pg.MOUSEBUTTONDOWN:
                self.handle_click(ev.pos)

            elif ev.type == pg.MOUSEBUTTONUP:
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

class Engine:

    FPS = 60

    def __init__(self, game):
        self.game = game
        self.setup()

    def setup(self):
        pg.init()
        pg.display.set_caption("ByteWave")
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
