import random
import math
import time

class Game2048Simulator:
    def __init__(self):
        self.grid_size = 4
        self.grid = [[0] * self.grid_size for _ in range(self.grid_size)]
        self.spawn_tile()
        self.spawn_tile()
        
    def spawn_tile(self):
        empty_cells = [(i, j) for i in range(4) for j in range(4) if self.grid[i][j] == 0]
        if empty_cells:
            r, c = random.choice(empty_cells)
            self.grid[r][c] = 2 if random.random() < 0.9 else 4

    def simulate_move(self, grid, direction):
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

    def run(self):
        moves = 0
        while True:
            best_move = self.get_best_move()
            if best_move == "None":
                break
                
            self.grid, moved = self.simulate_move(self.grid, best_move)
            if not moved:
                break
                
            self.spawn_tile()
            moves += 1
            
            # Print status every 500 moves to keep log clean
            if moves % 500 == 0:
                max_val = max(max(row) for row in self.grid)
                # print(f"Moves: {moves}, Max Tile: {max_val}")
        
        max_val = max(max(row) for row in self.grid)
        return max_val, moves

if __name__ == "__main__":
    print("Starting simulation (20 runs)...")
    results = []
    start_time = time.time()
    
    for i in range(20):
        sim = Game2048Simulator()
        max_val, moves = sim.run()
        results.append(max_val)
        print(f"Run {i+1}: Max Tile = {max_val}, Moves = {moves}")
        
    print("-" * 30)
    print(f"Summary:")
    print(f"Runs: {len(results)}")
    print(f"Success Rate (>= 2048): {len([r for r in results if r >= 2048]) / len(results) * 100}%")
    avg_score = sum(results) / len(results)
    print(f"Average Max Tile: {avg_score}")
    print(f"Best Run: {max(results)}")
    print(f"Time Taken: {time.time() - start_time:.2f}s")
