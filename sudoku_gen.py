"""
Pure In-Memory Sudoku Generator
No file dependencies - everything happens in RAM
"""

import random
from copy import deepcopy


class SudokuGen:
    """Lightweight solvable sudoku generator - zero file I/O"""
    
    def __init__(self):
        self.grid = None
        self.solution = None
    
    def _is_valid(self, grid, row, col, num):
        """Check if num is valid at position"""
        # Check row
        if num in grid[row]:
            return False
        
        # Check column
        if num in [grid[i][col] for i in range(9)]:
            return False
        
        # Check 3x3 box
        box_r, box_c = 3 * (row // 3), 3 * (col // 3)
        for i in range(box_r, box_r + 3):
            for j in range(box_c, box_c + 3):
                if grid[i][j] == num:
                    return False
        
        return True
    
    def _fill_solution(self, grid):
        """Recursively fill grid to create valid solution"""
        for row in range(9):
            for col in range(9):
                if grid[row][col] == 0:
                    nums = list(range(1, 10))
                    random.shuffle(nums)
                    
                    for num in nums:
                        if self._is_valid(grid, row, col, num):
                            grid[row][col] = num
                            if self._fill_solution(grid):
                                return True
                            grid[row][col] = 0
                    
                    return False
        return True
    
    def _count_solutions(self, grid, limit=2):
        """Count solutions up to limit"""
        count = [0]
        test = deepcopy(grid)
        
        def backtrack():
            if count[0] >= limit:
                return
            
            for row in range(9):
                for col in range(9):
                    if test[row][col] == 0:
                        for num in range(1, 10):
                            if self._is_valid(test, row, col, num):
                                test[row][col] = num
                                backtrack()
                                test[row][col] = 0
                        return
            count[0] += 1
        
        backtrack()
        return count[0]
    
    def generate(self, difficulty='medium'):
        """
        Generate solvable sudoku puzzle with unique solution
        
        Args:
            difficulty: 'easy' (45-54 clues), 'medium' (30-40), 'hard' (17-25)
        
        Returns:
            list: 9x9 grid with zeros as empty cells
        """
        # Generate complete solution
        self.grid = [[0] * 9 for _ in range(9)]
        self._fill_solution(self.grid)
        self.solution = deepcopy(self.grid)
        
        # Create puzzle by removing clues
        puzzle = deepcopy(self.solution)
        
        if difficulty == 'easy':
            clues = random.randint(45, 54)
        elif difficulty == 'hard':
            clues = random.randint(17, 25)
        else:  # medium
            clues = random.randint(30, 40)
        
        # Remove cells while maintaining unique solution
        cells = [(r, c) for r in range(9) for c in range(9)]
        random.shuffle(cells)
        
        for row, col in cells:
            current_clues = sum(1 for i in range(9) for j in range(9) if puzzle[i][j] != 0)
            if current_clues <= clues:
                break
            
            backup = puzzle[row][col]
            puzzle[row][col] = 0
            
            # Verify unique solution
            if self._count_solutions(puzzle) != 1:
                puzzle[row][col] = backup
        
        self.grid = puzzle
        return puzzle
    
    def solve(self, puzzle):
        """Solve a puzzle"""
        solution = deepcopy(puzzle)
        
        def backtrack():
            for row in range(9):
                for col in range(9):
                    if solution[row][col] == 0:
                        for num in range(1, 10):
                            if self._is_valid(solution, row, col, num):
                                solution[row][col] = num
                                if backtrack():
                                    return True
                                solution[row][col] = 0
                        return False
            return True
        
        backtrack()
        return solution
    
    def display(self, grid):
        """Pretty print grid"""
        lines = []
        for i in range(9):
            if i % 3 == 0 and i != 0:
                lines.append("------+-------+------")
            
            row = ""
            for j in range(9):
                if j % 3 == 0 and j != 0:
                    row += "| "
                row += str(grid[i][j]) + " " if grid[i][j] != 0 else ". "
            lines.append(row)
        
        return "\n".join(lines)


# Quick test
if __name__ == "__main__":
    gen = SudokuGen()
    
    puzzle = gen.generate('hard')
    print("PUZZLE:")
    print(gen.display(puzzle))
    
    print("\nSOLVED:")
    solution = gen.solve(puzzle)
    print(gen.display(solution))
