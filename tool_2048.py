import tkinter as tk
import random
import copy
import math

class Tile:
    def __init__(self, master, value, row, col, size=80, padding=5):
        self.master = master
        self.value = value
        self.row = row
        self.col = col
        self.size = size
        self.padding = padding
        self.colors = {
            0: ("#cdc1b4", "#776e65"),
            1: ("#eee4da", "#776e65"),
            2: ("#eee4da", "#776e65"),
            4: ("#ede0c8", "#776e65"),
            8: ("#f2b179", "#f9f6f2"),
            16: ("#f59563", "#f9f6f2"),
            32: ("#f67c5f", "#f9f6f2"),
            64: ("#f65e3b", "#f9f6f2"),
            128: ("#edcf72", "#f9f6f2"),
            256: ("#edcc61", "#f9f6f2"),
            512: ("#edc850", "#f9f6f2"),
            1024: ("#edc53f", "#f9f6f2"),
            2048: ("#edc22e", "#f9f6f2"),
        }
        
        self.frame = tk.Frame(master, width=size, height=size, bg=self.get_color()[0])
        self.label = tk.Label(self.frame, text=str(value) if value > 0 else "", 
                              font=("Arial", self.get_font_size(), "bold"), 
                              bg=self.get_color()[0], fg=self.get_color()[1])
        self.label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        self.place_at(row, col)

    def get_color(self):
        return self.colors.get(self.value, ("#3c3a32", "#f9f6f2"))

    def get_font_size(self):
        if self.value > 10000: return 12
        if self.value > 1000: return 16
        if self.value > 100: return 20
        return 24

    def update_visuals(self):
        bg, fg = self.get_color()
        self.frame.config(bg=bg)
        self.label.config(text=str(self.value) if self.value > 0 else "", bg=bg, fg=fg, font=("Arial", self.get_font_size(), "bold"))

    def get_coords(self, row, col):
        x = col * (self.size + self.padding * 2) + self.padding
        y = row * (self.size + self.padding * 2) + self.padding
        return x, y

    def place_at(self, row, col):
        x, y = self.get_coords(row, col)
        self.frame.place(x=x, y=y)

    def destroy(self):
        self.frame.destroy()

class Game2048Tool:
    def __init__(self, root):
        self.root = root
        self.root.title("2048 Visualization Tool")
        self.grid_size = 4
        self.tile_size = 80
        self.padding = 5
        
        # Mode: "Normal" or "Hint"
        self.mode = tk.StringVar(value="Normal") 
        
        # Logical grid (integers)
        self.grid = [[0] * self.grid_size for _ in range(self.grid_size)]
        
        # Visual tiles (Tile objects) - mapped by ID or just managed dynamically
        # For simple animation, we can just rebuild tiles or track them.
        # Tracking is better for sliding.
        self.tiles = {} # (r, c) -> Tile object. Wait, moving tiles change r,c. 
        # Better: keep a list of active Tile objects and sync them.
        # Actually, let's keep it simple: Map (r,c) to Tile object. 
        # When moving, we update the map.
        self.visual_grid = [[None] * self.grid_size for _ in range(self.grid_size)]
        
        self.history = []
        self.score = 0
        self.animating = False
        
        # UI Setup
        self.setup_ui()
        
        # Start game
        self.spawn_tile()
        self.spawn_tile()
        self.sync_visuals()

    def setup_ui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg="#faf8ef")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Top Bar (Mode Selection & Info)
        top_frame = tk.Frame(main_frame, bg="#faf8ef")
        top_frame.pack(fill=tk.X, pady=10)
        
        tk.Radiobutton(top_frame, text="Normal Mode", variable=self.mode, value="Normal", bg="#faf8ef", command=self.on_mode_change).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(top_frame, text="Hint Mode", variable=self.mode, value="Hint", bg="#faf8ef", command=self.on_mode_change).pack(side=tk.LEFT, padx=10)
        
        self.info_label = tk.Label(main_frame, text="", font=("Arial", 14), bg="#faf8ef")
        self.info_label.pack(pady=5)
        
        # Game Area
        game_area = tk.Frame(main_frame, bg="#faf8ef")
        game_area.pack()
        
        # Grid Frame (Container for tiles)
        # Size = 4 * 80 + 8 * 5 = 320 + 40 = 360 approx
        grid_width = self.grid_size * (self.tile_size + 2 * self.padding)
        self.grid_frame = tk.Frame(game_area, bg="#bbada0", width=grid_width, height=grid_width)
        self.grid_frame.pack(side=tk.LEFT, padx=10)
        self.grid_frame.pack_propagate(False) # Prevent shrinking
        
        # Create background empty cells
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                x = j * (self.tile_size + 2 * self.padding) + self.padding
                y = i * (self.tile_size + 2 * self.padding) + self.padding
                f = tk.Frame(self.grid_frame, width=self.tile_size, height=self.tile_size, bg="#cdc1b4")
                f.place(x=x, y=y)
                
                # Bind clicks to background cells too
                f.bind("<Button-1>", lambda e, r=i, c=j: self.on_click(r, c, 1))
                f.bind("<Button-3>", lambda e, r=i, c=j: self.on_click(r, c, -1))

        # Controls Frame (Right side)
        controls_frame = tk.Frame(game_area, bg="#faf8ef")
        controls_frame.pack(side=tk.LEFT, padx=20, fill=tk.Y)
        
        # Direction Buttons Frame
        self.dir_frame = tk.Frame(controls_frame, bg="#faf8ef")
        
        btn_font = ("Arial", 12, "bold")
        tk.Button(self.dir_frame, text="↑", font=btn_font, command=lambda: self.move("Up"), width=5, height=2).grid(row=0, column=1, pady=5)
        tk.Button(self.dir_frame, text="←", font=btn_font, command=lambda: self.move("Left"), width=5, height=2).grid(row=1, column=0, padx=5)
        tk.Button(self.dir_frame, text="→", font=btn_font, command=lambda: self.move("Right"), width=5, height=2).grid(row=1, column=2, padx=5)
        tk.Button(self.dir_frame, text="↓", font=btn_font, command=lambda: self.move("Down"), width=5, height=2).grid(row=2, column=1, pady=5)
        
        # Next Step Button (for Hint Mode)
        self.next_btn_frame = tk.Frame(controls_frame, bg="#faf8ef")
        tk.Button(self.next_btn_frame, text="Next Step", font=("Arial", 14, "bold"), command=self.next_step, width=12, height=2, bg="#8f7a66", fg="white").pack(pady=20)
        
        # Undo Button
        tk.Button(controls_frame, text="Undo", font=("Arial", 12), command=self.undo, width=10).pack(side=tk.BOTTOM, pady=20)
        
        self.instr_label = tk.Label(controls_frame, text="", bg="#faf8ef", justify=tk.LEFT)
        self.instr_label.pack(side=tk.BOTTOM, pady=10)
        
        # Initial Mode Setup
        self.on_mode_change()

    def on_mode_change(self):
        # Reset or update UI state
        if self.mode.get() == "Normal":
            self.next_btn_frame.pack_forget()
            self.dir_frame.pack(side=tk.TOP, pady=20)
            self.instr_label.config(text="Normal Mode:\nStandard 2048 rules.\nNo Hints.\n\nHint Mode:\nModify tiles with mouse.\nAuto-move button.")
        else:
            self.dir_frame.pack_forget()
            self.next_btn_frame.pack(side=tk.TOP, pady=20)
            self.instr_label.config(text="Hint Mode:\nLeft Click: x2\nRight Click: /2\n'Next Step': Auto move")
            
        self.update_ai_hint()

    def on_click(self, r, c, direction):
        if self.mode.get() != "Hint":
            return # Only allow editing in Hint mode
            
        self.save_state()
        val = self.grid[r][c]
        
        if direction == 1: # Left click: x2
            if val == 0: val = 2 # Start from 2
            else: val *= 2
        else: # Right click: /2
            if val <= 2: val = 0 # Clear if 2 or less
            else: val //= 2
            
        self.grid[r][c] = val
        self.sync_visuals()
        self.update_ai_hint()
        
    def next_step(self):
        if self.mode.get() != "Hint": return
        
        best_move = self.get_best_move()
        if best_move != "None":
            self.move(best_move)
            self.info_label.config(text=f"Executed: {best_move}")

    def save_state(self):
        self.history.append([row[:] for row in self.grid])
        if len(self.history) > 50: self.history.pop(0)

    def undo(self):
        if self.history and not self.animating:
            self.grid = self.history.pop()
            self.sync_visuals()
            self.update_ai_hint()

    def spawn_tile(self):
        empty_cells = [(i, j) for i in range(4) for j in range(4) if self.grid[i][j] == 0]
        if empty_cells:
            r, c = random.choice(empty_cells)
            self.grid[r][c] = 2 if random.random() < 0.9 else 4

    def sync_visuals(self):
        # Recreate all tiles based on grid
        # This is a brute-force sync, useful for undo/init/spawn
        # For moves, we use animation instead.
        for i in range(4):
            for j in range(4):
                if self.visual_grid[i][j]:
                    self.visual_grid[i][j].destroy()
                    self.visual_grid[i][j] = None
                
                if self.grid[i][j] != 0:
                    t = Tile(self.grid_frame, self.grid[i][j], i, j, self.tile_size, self.padding)
                    self.visual_grid[i][j] = t
                    # Bind clicks to tiles
                    t.label.bind("<Button-1>", lambda e, r=i, c=j: self.on_click(r, c, 1))
                    t.label.bind("<Button-3>", lambda e, r=i, c=j: self.on_click(r, c, -1))
                    t.frame.bind("<Button-1>", lambda e, r=i, c=j: self.on_click(r, c, 1))
                    t.frame.bind("<Button-3>", lambda e, r=i, c=j: self.on_click(r, c, -1))

    def move(self, direction):
        if self.animating: return
        
        self.save_state()
        
        # Calculate moves
        moves, new_grid, score_gain = self.calc_moves(self.grid, direction)
        
        if not moves and self.grid == new_grid:
            self.history.pop() # No change
            return

        self.animating = True
        
        # Animation
        steps = 10
        delay = 10 # ms
        
        # Helper to animate
        def animate_step(step):
            if step >= steps:
                # End animation
                self.grid = new_grid
                self.sync_visuals()
                
                # Post-move logic
                if self.mode.get() == "Normal":
                    self.spawn_tile()
                    self.sync_visuals() # Sync again for new tile
                    self.info_label.config(text="") # No hint in normal mode
                else:
                    self.update_ai_hint()
                
                self.animating = False
                return

            progress = (step + 1) / steps
            for m in moves:
                # m = {from: (r,c), to: (r,c), merge: bool}
                r1, c1 = m['from']
                r2, c2 = m['to']
                
                tile = self.visual_grid[r1][c1]
                if tile:
                    # Interpolate
                    x1, y1 = tile.get_coords(r1, c1)
                    x2, y2 = tile.get_coords(r2, c2)
                    cur_x = x1 + (x2 - x1) * progress
                    cur_y = y1 + (y2 - y1) * progress
                    tile.frame.place(x=cur_x, y=cur_y)
            
            self.root.after(delay, lambda: animate_step(step + 1))

        animate_step(0)

    def calc_moves(self, grid, direction):
        # Returns: list of moves, new_grid, score
        # Move format: {'from': (r,c), 'to': (r,c), 'merge': bool}
        moves = []
        new_grid = [[0]*4 for _ in range(4)]
        score = 0
        merged = [[False]*4 for _ in range(4)]
        
        # Define traversal order based on direction
        # We always iterate from the side we are moving TOWARDS
        if direction == "Up":
            rows = range(4)
            cols = range(4)
            dr, dc = -1, 0
        elif direction == "Down":
            rows = range(3, -1, -1)
            cols = range(4)
            dr, dc = 1, 0
        elif direction == "Left":
            rows = range(4)
            cols = range(4)
            dr, dc = 0, -1
        elif direction == "Right":
            rows = range(4)
            cols = range(3, -1, -1)
            dr, dc = 0, 1
            
        # Copy grid to temp working grid to track positions
        # Actually, simpler: just simulate standard 2048 logic but track source
        # We need to process cell by cell in the correct order
        
        # State tracking: where did each cell come from?
        # Let's do a simulation per column/row
        
        source_grid = [[(r,c) for c in range(4)] for r in range(4)]
        res_grid = [[0]*4 for _ in range(4)]
        
        # Generic logic using vectors
        # For each line (row or col depending on direction)
        for i in range(4):
            # Extract line
            if direction in ["Left", "Right"]:
                line = [(r, i) for r in range(4)] # Just placeholders, we need values
                # Wait, this is getting complex. Let's stick to per-direction logic.
                pass
        
        # Let's reuse the logic style but specific for each direction
        # to ensure we capture "moves".
        
        if direction == "Left":
            for r in range(4):
                target_c = 0
                for c in range(4):
                    if grid[r][c] != 0:
                        if target_c > 0 and res_grid[r][target_c-1] == grid[r][c] and not merged[r][target_c-1]:
                            # Merge
                            res_grid[r][target_c-1] *= 2
                            merged[r][target_c-1] = True
                            moves.append({'from': (r,c), 'to': (r, target_c-1), 'merge': True})
                        else:
                            # Move to empty
                            res_grid[r][target_c] = grid[r][c]
                            if c != target_c:
                                moves.append({'from': (r,c), 'to': (r, target_c), 'merge': False})
                            target_c += 1
                            
        elif direction == "Right":
            for r in range(4):
                target_c = 3
                for c in range(3, -1, -1):
                    if grid[r][c] != 0:
                        if target_c < 3 and res_grid[r][target_c+1] == grid[r][c] and not merged[r][target_c+1]:
                            res_grid[r][target_c+1] *= 2
                            merged[r][target_c+1] = True
                            moves.append({'from': (r,c), 'to': (r, target_c+1), 'merge': True})
                        else:
                            res_grid[r][target_c] = grid[r][c]
                            if c != target_c:
                                moves.append({'from': (r,c), 'to': (r, target_c), 'merge': False})
                            target_c -= 1

        elif direction == "Up":
            for c in range(4):
                target_r = 0
                for r in range(4):
                    if grid[r][c] != 0:
                        if target_r > 0 and res_grid[target_r-1][c] == grid[r][c] and not merged[target_r-1][c]:
                            res_grid[target_r-1][c] *= 2
                            merged[target_r-1][c] = True
                            moves.append({'from': (r,c), 'to': (target_r-1, c), 'merge': True})
                        else:
                            res_grid[target_r][c] = grid[r][c]
                            if r != target_r:
                                moves.append({'from': (r,c), 'to': (target_r, c), 'merge': False})
                            target_r += 1

        elif direction == "Down":
            for c in range(4):
                target_r = 3
                for r in range(3, -1, -1):
                    if grid[r][c] != 0:
                        if target_r < 3 and res_grid[target_r+1][c] == grid[r][c] and not merged[target_r+1][c]:
                            res_grid[target_r+1][c] *= 2
                            merged[target_r+1][c] = True
                            moves.append({'from': (r,c), 'to': (target_r+1, c), 'merge': True})
                        else:
                            res_grid[target_r][c] = grid[r][c]
                            if r != target_r:
                                moves.append({'from': (r,c), 'to': (target_r, c), 'merge': False})
                            target_r -= 1

        return moves, res_grid, score

    def update_ai_hint(self):
        if self.mode.get() == "Normal":
            self.info_label.config(text="")
            return
            
        self.info_label.config(text="Calculating...")
        self.root.update_idletasks() # Force UI update
        best_move = self.get_best_move()
        self.info_label.config(text=f"Best Move: {best_move}")

    # --- AI Logic (Reused) ---
    def get_best_move(self):
        # Optimized Dynamic Depth
        empty_count = sum(row.count(0) for row in self.grid)
        
        # Base depth - go deep!
        if empty_count >= 8: depth = 3
        elif empty_count >= 6: depth = 4
        elif empty_count >= 2: depth = 5
        else: depth = 7 # Critical
            
        best_score = -float('inf')
        best_move = "None"
        moves = ["Up", "Down", "Left", "Right"]
        
        # Pre-filter moves
        valid_moves = []
        for move in moves:
            grid_copy = [row[:] for row in self.grid]
            grid_next, moved = self.simulate_move(grid_copy, move)
            if moved:
                valid_moves.append((move, grid_next))
        
        if not valid_moves: return "None"

        for move, grid_next in valid_moves:
            score = self.expectimax(grid_next, depth - 1, False)
            if score > best_score:
                best_score = score
                best_move = move
                
        return best_move

    def simulate_move(self, grid, direction):
        # Simplified move logic just for AI
        new_grid = [[0]*4 for _ in range(4)]
        merged = [[False]*4 for _ in range(4)]
        moved = False
        
        if direction == "Left":
            for r in range(4):
                target_c = 0
                for c in range(4):
                    if grid[r][c] != 0:
                        if target_c > 0 and new_grid[r][target_c-1] == grid[r][c] and not merged[r][target_c-1]:
                            new_grid[r][target_c-1] *= 2
                            merged[r][target_c-1] = True
                            moved = True
                        else:
                            new_grid[r][target_c] = grid[r][c]
                            if c != target_c: moved = True
                            target_c += 1
        elif direction == "Right":
            for r in range(4):
                target_c = 3
                for c in range(3, -1, -1):
                    if grid[r][c] != 0:
                        if target_c < 3 and new_grid[r][target_c+1] == grid[r][c] and not merged[r][target_c+1]:
                            new_grid[r][target_c+1] *= 2
                            merged[r][target_c+1] = True
                            moved = True
                        else:
                            new_grid[r][target_c] = grid[r][c]
                            if c != target_c: moved = True
                            target_c -= 1
        elif direction == "Up":
            for c in range(4):
                target_r = 0
                for r in range(4):
                    if grid[r][c] != 0:
                        if target_r > 0 and new_grid[target_r-1][c] == grid[r][c] and not merged[target_r-1][c]:
                            new_grid[target_r-1][c] *= 2
                            merged[target_r-1][c] = True
                            moved = True
                        else:
                            new_grid[target_r][c] = grid[r][c]
                            if r != target_r: moved = True
                            target_r += 1
        elif direction == "Down":
            for c in range(4):
                target_r = 3
                for r in range(3, -1, -1):
                    if grid[r][c] != 0:
                        if target_r < 3 and new_grid[target_r+1][c] == grid[r][c] and not merged[target_r+1][c]:
                            new_grid[target_r+1][c] *= 2
                            merged[target_r+1][c] = True
                            moved = True
                        else:
                            new_grid[target_r][c] = grid[r][c]
                            if r != target_r: moved = True
                            target_r -= 1
                            
        return new_grid, moved

    def expectimax(self, grid, depth, is_player):
        if depth == 0: return self.evaluate(grid)
        
        if is_player:
            best_score = -float('inf')
            can_move = False
            for move in ["Up", "Down", "Left", "Right"]:
                grid_next, moved = self.simulate_move([row[:] for row in grid], move)
                if moved:
                    can_move = True
                    score = self.expectimax(grid_next, depth - 1, False)
                    best_score = max(best_score, score)
            
            if not can_move: return self.evaluate(grid)
            return best_score
        else:
            empty_cells = [(i, j) for i in range(4) for j in range(4) if grid[i][j] == 0]
            if not empty_cells: return self.evaluate(grid)
            
            # Robust Sampling
            if len(empty_cells) > 6:
                cells_to_check = random.sample(empty_cells, 6)
            else:
                cells_to_check = empty_cells
            
            avg_score = 0
            for r, c in cells_to_check:
                # 2 case
                grid[r][c] = 2
                score2 = self.expectimax(grid, depth - 1, True)
                
                # 4 case
                score4 = score2
                if depth <= 2 or len(empty_cells) <= 4:
                    grid[r][c] = 4
                    score4 = self.expectimax(grid, depth - 1, True)
                
                grid[r][c] = 0
                avg_score += 0.9 * score2 + 0.1 * score4
                
            return avg_score / len(cells_to_check)

    def evaluate(self, grid):
        empty_cells = sum(row.count(0) for row in grid)
        
        # Smoothness
        smoothness = 0
        for r in range(4):
            for c in range(4):
                if grid[r][c] != 0:
                    val = math.log2(grid[r][c])
                    if c < 3 and grid[r][c+1] != 0:
                        val_right = math.log2(grid[r][c+1])
                        smoothness -= abs(val - val_right)
                    if r < 3 and grid[r+1][c] != 0:
                        val_down = math.log2(grid[r+1][c])
                        smoothness -= abs(val - val_down)
        
        # Monotonicity
        mono_left = 0; mono_right = 0; mono_up = 0; mono_down = 0
        for r in range(4):
            for c in range(3):
                current = grid[r][c]
                next_val = grid[r][c+1]
                if current > next_val: 
                    mono_left += next_val - current
                else: 
                    mono_right += current - next_val
        
        for c in range(4):
            for r in range(3):
                current = grid[r][c]
                next_val = grid[r+1][c]
                if current > next_val: 
                    mono_up += next_val - current
                else: 
                    mono_down += current - next_val

        monotonicity = max(mono_left, mono_right) + max(mono_up, mono_down)
        
        # Snake Pattern Heuristic
        snake_weights = [
            [2**15, 2**14, 2**13, 2**12],
            [2**8,  2**9,  2**10, 2**11],
            [2**7,  2**6,  2**5,  2**4],
            [2**0,  2**1,  2**2,  2**3]
        ]
        
        snake_score = 0
        for r in range(4):
            for c in range(4):
                if grid[r][c] != 0:
                    snake_score += grid[r][c] * snake_weights[r][c]

        return snake_score + (empty_cells * 10000) + (monotonicity * 100) + (smoothness * 10)

if __name__ == "__main__":
    root = tk.Tk()
    game = Game2048Tool(root)
    root.mainloop()
