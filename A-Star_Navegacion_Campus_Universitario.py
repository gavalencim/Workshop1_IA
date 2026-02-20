import heapq
import math

## 1. CAMPUS:

# 'C' = Cafetería, 'B' = Biblioteca, '#' = pared, ' ' = pasillo transitable
CAMPUS = [
# x:  0    1    2     3    4     5     6    7    8     9    10   11    12   13   14    15   16
    [" ", "#", " ",  " ", "#",  " ",  " ", "#", " ",  " ", "#", " ",  " ", "#", " ",  " ", " "],  # y=0
    [" ", "#", " ",  " ", "#",  " ",  " ", "#", " ",  " ", "#", " ",  " ", "#", " ",  " ", " "],  # y=1
    [" ", " ", "B30"," ", " ", "B31"," ", " ", "B32"," ", " ", "B33"," ", " ", "B34"," ", " "],  # y=2
    [" ", "#", " ",  "#", "#", " ",  "#", " ", "#",  "#", " ", "#",  " ", "#", " ",  "#", " "],  # y=3
    [" ", "#", " ",  " ", " ", " ",  "#", " ", "#",  " ", " ", "#",  " ", "#", " ",  "#", " "],  # y=4
    [" ", " ", " ",  "#", " ", " ",  " ", " ", " ",  "#", " ", " ",  " ", " ", " ",  "#", " "],  # y=5
    [" ", "#", " ",  " ", "B35"," ",  "#", " ", "B36"," ", "#", " ",  "B37"," ", "#", " ", "B38"],# y=6
    [" ", "#", "#",  " ", "#", " ",  "#", " ", "#",  " ", "#", " ",  "#", " ", "#",  " ", " "],  # y=7
    [" ", " ", " ",  " ", "#", " ",  " ", " ", "#",  " ", " ", " ",  "#", " ", " ",  " ", " "],  # y=8
    ["#", "#", " ",  "#", "#", " ",  "#", " ", " ",  " ", "#", " ",  "#", " ", "#",  "#", " "],  # y=9
    [" ", " ", " ",  " ", "#", " ",  "C", " ", "#",  " ", "#", " ",  " ", " ", "B",  " ", " "],  # y=10
    [" ", "#", "#",  " ", "#", " ",  "#", " ", "#",  " ", "#", " ",  "#", " ", "#",  " ", " "],  # y=11
    [" ", " ", " ",  " ", " ", " ",  " ", " ", " ",  " ", " ", " ",  " ", " ", " ",  " ", " "],  # y=12
    [" ", "#", " ",  "#", " ", "#",  " ", "#", " ",  "#", " ", "#",  " ", "#", " ",  "#", " "],  # y=13
    [" ", "#", " ",  " ", " ", " ",  " ", " ", " ",  " ", " ", " ",  " ", " ", " ",  "#", " "],  # y=14
    [" ", " ", " ",  "#", "#", "#",  " ", "#", "#",  "#", " ", "#",  "#", "#", " ",  " ", " "],  # y=15
]
ROWS = len(CAMPUS)      # 16 filas  → y ∈ [0, 15]
COLS = len(CAMPUS[0])   # 17 cols   → x ∈ [0, 16]

# Coordenadas por edificio
BUILDING_COORDS = {
    'B30': (2, 2),  'B31': (5, 2),  'B32': (8, 2),
    'B33': (11, 2), 'B34': (14, 2), 'B35': (4, 6),
    'B36': (8, 6),  'B37': (12, 6), 'B38': (16, 6),
    'Cafetería': (6, 10), 'Biblioteca': (14, 10),
}
COORD_TO_BUILDING = {v: k for k, v in BUILDING_COORDS.items()} 
# Edificios con ascensor
ELEVATOR_BUILDINGS = {'B32', 'B33', 'B35', 'B37', 'B38'} 
# Coordenadas de las direcciones de movimiento
DIRECTIONS = {
    'derecha':   ( 1,  0),
    'izquierda': (-1,  0),
    'abajo':     ( 0,  1),
    'arriba':    ( 0, -1),
}

## 2. CLASE "NODE"

class Node:

    def __init__(self, state, parent=None, action=None, g=0, h=0):
        self.state  = state
        self.parent = parent
        self.action = action
        self.g      = g
        self.h      = h
        self.f      = g + h
    
    # Comparaciones para el heap de prioridad
    def __lt__(self, other):
        return self.f < other.f

    def __eq__(self, other):
        return self.state == other.state

    def __hash__(self):
        return hash(self.state)

    def __repr__(self):
        x, y, floor = self.state # Tupla state que indica las coordenadas y el piso actual
        building = COORD_TO_BUILDING.get((x, y), 'Pasillo')
        return (f"Node(state={self.state}, building={building}, "
                f"g={self.g:.1f}, h={self.h:.2f}, f={self.f:.2f})")
    
    # Camino
    def path(self):
        nodes, current = [], self
        while current:
            nodes.append(current)
            current = current.parent
        return list(reversed(nodes)) # lista de nodos desde la raíz hasta este nodo
    
    def actions(self):
        return [n.action for n in self.path() if n.action is not None] # Lista de acciones desde la raiz hasta este nodo

## 3. CLASE "PROBLEM" ABSTRACTA

class Problem:

    def __init__(self, initial, goal):
        self.initial = initial
        self.goal    = goal

    def actions(self, state):
        raise NotImplementedError

    def result(self, state, action):
        raise NotImplementedError

    def is_goal(self, state):
        raise NotImplementedError

    def heuristic(self, state):
        raise NotImplementedError

    def action_cost(self, state, action):
        #Costo de ejecutar una acción
        raise NotImplementedError
    
## 4. CLASE "CAMPUSPROBLEM" QUE HEREDA DE PROBLEM, HAY QUE SOBREESCRIBIR SUS MÉTODOS
## AQUÍ SE ENCUENTRA LA LÓGICA DEL PROBLEMA ESPECÍFICO

class CampusProblem(Problem):

    # Mapa
    @staticmethod #No necesita acceder a la clase padre
    def _cell(x, y):
        if 0 <= y < ROWS and 0 <= x < COLS:
            return CAMPUS[y][x]
        return None # Celdas del mapa con verificación de que no se salga de las fronteras

    @staticmethod
    def _walkable(x, y):
        c = CampusProblem._cell(x, y)
        return c is not None and c != '#' # Celdas transitables

    @staticmethod
    def _building(x, y):
        return COORD_TO_BUILDING.get((x, y), 'Pasillo') # Verifica si está en un edificio o un pasillo 
    
    # Sobre el problema específico
    def actions(self, state):
        x, y, floor = state # Toma los componente de state y los separa
        building    = self._building(x, y) # Método de la clase Problem, verifica estado actual
        available   = [] # Lista acción-costo
        
        # Movimientos en el plano (solo piso 1)
        if floor == 1:
            for name, (dx, dy) in DIRECTIONS.items(): # Por cada nombre de direccion en el diccionario de direcciones,
                if self._walkable(x + dx, y + dy): # Si la celda es transitable,
                    available.append((name, 1)) # Agrega dicha celda y su costo que es 1

        # Ascensor (solo edificios habilitados, pisos 1-3)
        if building in ELEVATOR_BUILDINGS: # Si estamos en un edificio con ascensor,
            if floor < 3:
                available.append(('subir_ascensor', 3)) # Subimos si estamos en un piso menor que 3
            if floor > 1:
                available.append(('bajar_ascensor', 3)) # Bajamos si estamo en unpiso mayor que 1

        # Escaleras (cualquier edificio, no pasillos)
        if building != 'Pasillo':
            for p in range(1, 4 - floor):   # pisos que puede subir
                available.append((f'subir_escaleras_{p}piso', 7 + p))
            for p in range(1, floor):        # pisos que puede bajar
                available.append((f'bajar_escaleras_{p}piso', 5))

        return available # Acciones válidas

    def result(self, state, action): # Aplica una acción y devuelve el nuevo estado tras la acción
        x, y, floor = state # Desglosa la tupla de estado en sus 3 variables

        if action in DIRECTIONS: # Si la accion es izquierda, derecha, arriba o abajo: 
            dx, dy = DIRECTIONS[action]  # Se sacan los valores del diccionario de direcciones
            return (x + dx, y + dy, floor) # Se suman los valores para devolver el nuevo estado

        if action == 'subir_ascensor':
            return (x, y, floor + 1)
        if action == 'bajar_ascensor':
            return (x, y, floor - 1)

        if action.startswith('subir_escaleras_'):
            p = int(action.split('_')[2][0])   # extrae el número de pisos
            return (x, y, floor + p)
        if action.startswith('bajar_escaleras_'):
            p = int(action.split('_')[2][0])
            return (x, y, floor - p)

        raise ValueError(f"Acción desconocida: {action}")
    
    def is_goal(self, state): # Llegó al destino?
        x, y, floor = state # Desglosa los valores del estado en sus 3 variables
        gx, gy, gf  = self.goal # Desglosa los valores del destino en sus 3 variables
        return (x, y) == (gx, gy) and floor == gf # Compara el estado y el destino para saber si ya llegó

    def heuristic(self, state): # Heurística
        x,  y,  _  = state
        gx, gy, _  = self.goal
        return math.sqrt((x - gx) ** 2 + (y - gy) ** 2)

    def action_cost(self, state, action): # Costo de la acción
        for act, cost in self.actions(state):
            if act == action:
                return cost
        raise ValueError(f"Acción {action} no válida en estado {state}")

## 5. CLASE A*, PUEDE USAR CUALQUIER INSTANCIA DE PROBLEM  

class AStarSearch:
    
    def __init__(self, problem: Problem):
        self.problem    = problem
        self.open_list  = []
        self.closed_set = {}   # state → mejor g

    def search(self): # Ejecuta A* y retorna el nodo goal (con trazabilidad al padre) o None si no hay solución.
        problem = self.problem

        # Nodo raíz
        root = Node(
            state  = problem.initial,
            g      = 0,
            h      = problem.heuristic(problem.initial)
        )
        heapq.heappush(self.open_list, root)

        while self.open_list:
            node = heapq.heappop(self.open_list)

            # ── Goal test ──
            if problem.is_goal(node.state):
                return node

            # ── Nodo ya visitado con menor g ──
            if node.state in self.closed_set and self.closed_set[node.state] <= node.g:
                continue
            self.closed_set[node.state] = node.g

            # ── Expansión ──
            for action, cost in problem.actions(node.state):
                child_state = problem.result(node.state, action)
                child_g     = node.g + cost

                if child_state in self.closed_set and self.closed_set[child_state] <= child_g:
                    continue

                child = Node(
                    state  = child_state,
                    parent = node,
                    action = action,
                    g      = child_g,
                    h      = problem.heuristic(child_state)
                )
                heapq.heappush(self.open_list, child)

        return None   # Sin solución

## 6. VISUALIZACION EN CONSOLA

def visualize(path_nodes, start, goal):
    visual = [[cell for cell in row] for row in CAMPUS]

    # Marcar camino en piso 1
    for node in path_nodes:
        x, y, floor = node.state
        if floor == 1 and CAMPUS[y][x] == ' ':
            visual[y][x] = '·'

    # Inicio y Goal
    sx, sy, _ = start
    gx, gy, _ = goal
    visual[sy][sx] = 'S'
    visual[gy][gx] = 'G'

    sb = COORD_TO_BUILDING.get((sx, sy), 'Pasillo')
    gb = COORD_TO_BUILDING.get((gx, gy), 'Pasillo')

    print("\n╔══ MAPA DEL CAMPUS (piso 1) ══════════════════════════════════╗")
    print(f"  S = Inicio [{sb}]    G = Goal [{gb}]    · = Camino")
    print()
    print("     " + "".join(f"{x:<4}" for x in range(COLS)))
    print("     " + "─" * (COLS * 4))

    for y in range(ROWS):
        row_str = f"y={y:<2} │"
        for x in range(COLS):
            cell = visual[y][x]
            abbr = {'B': 'BIB', 'C': 'CAF'}.get(cell, cell)
            row_str += f"{abbr:<4}"
        print(row_str)

    print("╚" + "═" * 63 + "╝\n")

## 7. IMPRESION DE RESULTADOS 

def run(start_state, goal_state, label=""):
    problem = CampusProblem(initial=start_state, goal=goal_state)
    solver  = AStarSearch(problem)

    sb = COORD_TO_BUILDING.get((start_state[0], start_state[1]), 'Pasillo')
    gb = COORD_TO_BUILDING.get((goal_state[0],  goal_state[1]),  'Pasillo')

    print("=" * 65)
    print(f"  {label}")
    print(f"  Inicio  → {sb:<12} coord={start_state[:2]}  piso {start_state[2]}")
    print(f"  Destino → {gb:<12} coord={goal_state[:2]}  piso {goal_state[2]}")
    print("=" * 65)

    goal_node = solver.search()

    if goal_node is None:
        print("  ✗ No se encontró solución.\n")
        return

    path_nodes = goal_node.path()
    actions    = goal_node.actions()

    # ── Ruta de acciones ──
    print(f"\n  Ruta ({len(actions)} acciones):")
    for i, a in enumerate(actions, 1):
        print(f"    {i:>3}. {a}")

    # ── Secuencia de estados ──
    print(f"\n  Secuencia de estados:")
    for node in path_nodes:
        x, y, floor = node.state
        b = COORD_TO_BUILDING.get((x, y), 'Pasillo')
        print(f"       coord=({x:>2},{y:>2})  piso={floor}  [{b}]"
              f"   g={node.g}  h={node.h:.2f}  f={node.f:.2f}")

    print(f"\n  ✓ Costo total: {goal_node.g}")

    # ── Mapa visual ──
    visualize(path_nodes, start_state, goal_state)

## 8. PRUEBAS

if __name__ == "__main__":

    # Caso 1: B30 piso 1 → Cafetería piso 1
    run(
        start_state = (*BUILDING_COORDS['B30'],       1),
        goal_state  = (*BUILDING_COORDS['Cafetería'], 1),
        label       = "Caso 1 │ B30 piso 1  →  Cafetería piso 1"
    )

    # Caso 2: Cafetería piso 1 → Biblioteca piso 1
    run(
        start_state = (*BUILDING_COORDS['Cafetería'], 1),
        goal_state  = (*BUILDING_COORDS['Biblioteca'],1),
        label       = "Caso 2 │ Cafetería piso 1  →  Biblioteca piso 1"
    )

    # Caso 3: B32 piso 1 → B37 piso 3  (ascensor)
    run(
        start_state = (*BUILDING_COORDS['B32'], 1),
        goal_state  = (*BUILDING_COORDS['B37'], 3),
        label       = "Caso 3 │ B32 piso 1  →  B37 piso 3  (con ascensor)"
    )

    # Caso 4: B38 piso 2 → B35 piso 1
    run(
        start_state = (*BUILDING_COORDS['B38'], 2),
        goal_state  = (*BUILDING_COORDS['B35'], 1),
        label       = "Caso 4 │ B38 piso 2  →  B35 piso 1"
    )

