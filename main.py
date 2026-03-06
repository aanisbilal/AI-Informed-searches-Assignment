import pygame
import math
import random
import time
from queue import PriorityQueue

pygame.init()

ROWS = int(input("Enter grid rows: "))
COLS = int(input("Enter grid columns: "))
density = float(input("Enter obstacle density (0-1): "))

WIDTH = 700
GRID_AREA = 600
CELL = GRID_AREA // max(ROWS, COLS)

screen = pygame.display.set_mode((WIDTH, WIDTH))
pygame.display.set_caption("Dynamic Pathfinding Agent")

font = pygame.font.SysFont("Arial", 18)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (200, 200, 200)


class Node:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.x = col * CELL
        self.y = row * CELL
        self.color = WHITE
        self.parent = None

    def get_pos(self):
        return (self.row, self.col)

    def draw(self):
        pygame.draw.rect(screen, self.color, (self.x, self.y, CELL, CELL))
        pygame.draw.rect(screen, GRAY, (self.x, self.y, CELL, CELL), 1)

    def __eq__(self, other):
        return (
            isinstance(other, Node) and self.row == other.row and self.col == other.col
        )

    def __hash__(self):
        return hash((self.row, self.col))


def make_grid():
    grid = []
    for i in range(ROWS):
        grid.append([])
        for j in range(COLS):
            grid[i].append(Node(i, j))
    return grid


def draw_grid(grid):
    for row in grid:
        for node in row:
            node.draw()


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def euclidean(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def neighbors(grid, node):
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    result = []
    for d in dirs:
        r = node.row + d[0]
        c = node.col + d[1]
        if 0 <= r < ROWS and 0 <= c < COLS:
            if grid[r][c].color != BLACK:
                result.append(grid[r][c])
    return result


def reconstruct(node):
    path = []
    while node.parent:
        path.append(node)
        node = node.parent
    return path[::-1]


def search(grid, start, goal, algo, heuristic, dynamic=False):
    count = 0
    open_set = PriorityQueue()
    open_set.put((0, count, start))

    g_score = {start: 0}
    visited = set()
    frontier = set([start])
    visited_count = 0

    while not open_set.empty():
        # Clear previous frontier colors
        for row in grid:
            for node in row:
                if node.color == YELLOW:
                    node.color = WHITE

        # Spawn dynamic walls during search if enabled
        if dynamic and random.random() < 0.15:
            r = random.randint(0, ROWS - 1)
            c = random.randint(0, COLS - 1)
            random_node = grid[r][c]
            if random_node not in [start, goal] and random_node.color != BLACK:
                random_node.color = BLACK
                print(f"Wall spawned at ({r}, {c}) during search")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        current = open_set.get()[2]
        frontier.discard(current)

        if current == goal:
            return reconstruct(goal), visited_count

        visited.add(current)
        visited_count += 1

        if current != start:
            current.color = RED

        for n in neighbors(grid, current):
            temp_g = g_score[current] + 1

            if n not in g_score or temp_g < g_score[n]:
                g_score[n] = temp_g
                n.parent = current

                h = heuristic(n.get_pos(), goal.get_pos())
                if algo == "astar":
                    f = temp_g + h
                else:
                    f = h

                count += 1
                open_set.put((f, count, n))
                frontier.add(n)

        for fnode in frontier:
            if fnode not in visited and fnode != start:
                fnode.color = YELLOW

        draw_grid(grid)
        pygame.display.update()
        pygame.time.delay(5)

    return None, visited_count


def main():
    grid = make_grid()
    start = grid[0][0]
    goal = grid[ROWS - 1][COLS - 1]
    start.color = BLUE
    goal.color = GREEN

    algo = "astar"
    heuristic = manhattan
    dynamic = False

    running = True
    while running:
        screen.fill(WHITE)
        draw_grid(grid)

        info = font.render(
            f"Algo: {algo} | Heuristic: {heuristic.__name__} | Dynamic: {dynamic}",
            True,
            BLACK,
        )
        screen.blit(info, (10, 610))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if pygame.mouse.get_pressed()[0]:
                pos = pygame.mouse.get_pos()

                if pos[0] < GRID_AREA and pos[1] < GRID_AREA:
                    r = pos[1] // CELL
                    c = pos[0] // CELL

                    if r < ROWS and c < COLS:
                        node = grid[r][c]
                        if node not in [start, goal]:
                            node.color = BLACK if node.color != BLACK else WHITE

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    algo = "greedy"
                if event.key == pygame.K_2:
                    algo = "astar"
                if event.key == pygame.K_h:
                    heuristic = euclidean if heuristic == manhattan else manhattan
                if event.key == pygame.K_r:
                    for row in grid:
                        for node in row:
                            if node not in [start, goal]:
                                node.color = BLACK if random.random() < density else WHITE
                if event.key == pygame.K_d:
                    dynamic = not dynamic

                if event.key == pygame.K_SPACE:
                    # Reset previous search visualization
                    for row in grid:
                        for node in row:
                            if node not in [start, goal] and node.color in [RED, YELLOW, GREEN]:
                                node.color = WHITE
                            node.parent = None

                    t1 = time.time()
                    path, visited = search(grid, start, goal, algo, heuristic, dynamic)
                    t2 = time.time()

                    if path:
                        for node in path:
                            if node not in [start, goal]:
                                node.color = GREEN
                        
                        # Clear any walls that spawned on the final path
                        for node in path:
                            if node.color == BLACK:
                                node.color = GREEN

                    exec_time = round((t2 - t1) * 1000, 2)

                    dashboard = [
                        f"Nodes Visited: {visited}",
                        f"Path Cost: {len(path) if path else 0}",
                        f"Time (ms): {exec_time}",
                    ]

                    for i, text in enumerate(dashboard):
                        label = font.render(text, True, BLACK)
                        screen.blit(label, (350, 610 + i * 20))

                    pygame.display.update()

                    if dynamic and path:
                        current = start
                        step_index = 0
                        
                        while step_index < len(path) and current != goal:
                            # Randomly spawn new obstacles (NOT on path or current position)
                            if random.random() < 0.1:
                                r = random.randint(0, ROWS - 1)
                                c = random.randint(0, COLS - 1)
                                random_node = grid[r][c]
                                # Don't spawn on: start, goal, current position, or ANY node in the path
                                if random_node not in [start, goal, current] and random_node not in path and random_node.color != BLACK:
                                    random_node.color = BLACK
                            
                            # Get next step from remaining path
                            if step_index >= len(path):
                                break
                                
                            next_step = path[step_index]
                            
                            # Check if next step is blocked (became BLACK due to obstacle spawn)
                            if next_step.color == BLACK:
                                print("Path Blocked -> Replanning")

                                # Clear old path colors and reset parents
                                for row in grid:
                                    for node in row:
                                        node.parent = None
                                        if node.color == GREEN and node not in [start, goal]:
                                            node.color = WHITE

                                new_path, _ = search(grid, current, goal, algo, heuristic, dynamic)
                                
                                if new_path:
                                    path = new_path
                                    step_index = 0
                                    # Color new path
                                    for node in path:
                                        if node not in [start, goal]:
                                            node.color = GREEN
                                    continue
                                else:
                                    print("No path available!")
                                    break
                            
                            # Move agent to next step
                            current = next_step
                            if current.color != GREEN and current not in [start, goal]:
                                current.color = BLUE  # Agent color
                            
                            # Update display
                            screen.fill(WHITE)
                            draw_grid(grid)
                            info = font.render(
                                f"Dynamic Navigation: Agent Moving | Pos: ({current.row}, {current.col})",
                                True,
                                BLACK,
                            )
                            screen.blit(info, (10, 610))
                            pygame.display.update()
                            
                            # Handle events during movement
                            for event in pygame.event.get():
                                if event.type == pygame.QUIT:
                                    pygame.quit()
                                    exit()
                            
                            step_index += 1
                            pygame.time.delay(100)

    pygame.quit()


if __name__ == "__main__":
    main()
