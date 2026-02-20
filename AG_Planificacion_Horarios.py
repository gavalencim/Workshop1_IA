import random
from typing import List, Tuple
import matplotlib.pyplot as plt


# Cursos: (nombre, número de estudiantes)
courses = [
    ('MAT', 45),  # 0
    ('FIS', 30),  # 1
    ('QUI', 35),  # 2
    ('PRG', 40),  # 3
    ('LIT', 25),  # 4
    ('HIS', 30),  # 5
    ('ING', 35),  # 6
    ('EDF', 50)   # 7
]

# Bloques de tiempo disponibles
time_blocks = [1, 2, 3, 4, 5]
block_names = {
    1: 'Lun 8-10',
    2: 'Lun 10-12',
    3: 'Mie 8-10',
    4: 'Mie 10-12',
    5: 'Vie 8-10'
}

# Salones: {nombre: capacidad}
rooms = {
    'A': 40,
    'B': 30,
    'C': 50
}

# Índices de cursos que comparten profesor (no pueden ser simultáneos)
same_professor = [
    (0, 1),  # MAT y FIS
    (2, 3)   # QUI y PRG
]

print("✓ Configuración cargada")
print(f"  Cursos: {len(courses)}")
print(f"  Bloques: {len(time_blocks)}")
print(f"  Salones: {len(rooms)}")

# ══════════════════════════════════════════════════════════════
# TAREA 1: FITNESS
# ══════════════════════════════════════════════════════════════

def fitness(individual):
    score = 200

    # ── DURA 1: Conflictos de salón ─────────────────────────────
    # Comparamos todos los pares posibles de cursos.
    # Si dos cursos distintos comparten bloque Y salón al mismo
    # tiempo, es imposible → penalización grave.
    for i in range(len(individual)):
        for j in range(i + 1, len(individual)):
            block_i, room_i = individual[i]
            block_j, room_j = individual[j]
            if block_i == block_j and room_i == room_j:
                score -= 50

    # ── DURA 2: Capacidad insuficiente ──────────────────────────
    # courses[i][1] = número de estudiantes del curso i
    # rooms[room]   = capacidad del salón
    # Si no caben todos los estudiantes, penalizamos.
    for i in range(len(individual)):
        block, room = individual[i]
        _, students = courses[i]
        if students > rooms[room]:
            score -= 50

    # ── DURA 3: Profesores compartidos ──────────────────────────
    # same_professor es una lista de pares (idx_curso_1, idx_curso_2).
    # Si ambos cursos del par caen en el mismo bloque, el profesor
    # estaría en dos lugares a la vez → imposible.
    for c1, c2 in same_professor:
        if individual[c1][0] == individual[c2][0]:
            score -= 50

    # ── BLANDA 1: Bloques tardíos ────────────────────────────────
    # Los bloques 4 y 5 son menos deseables; penalizamos suavemente.
    for block, room in individual:
        if block >= 4:
            score -= 5

    # ── BLANDA 2: Desperdicio de espacio ─────────────────────────
    # Un curso pequeño (<35 estudiantes) en un salón grande (>45)
    # desperdicia capacidad que otro curso podría necesitar.
    for i in range(len(individual)):
        block, room = individual[i]
        _, students = courses[i]
        if students < 35 and rooms[room] > 45:
            score -= 3

    return score

# ══════════════════════════════════════════════════════════════
# TAREA 2: CROSSOVER
# ══════════════════════════════════════════════════════════════

def crossover(parent1, parent2):
    # Elegimos un punto de corte aleatorio entre 1 y 7.
    # No puede ser 0 (el hijo sería igual al padre 2) ni 8
    # (el hijo sería igual al padre 1).
    cut = random.randint(1, 7)

    # El hijo toma los genes 0..cut-1 del padre 1
    # y los genes cut..7 del padre 2.
    child = parent1[:cut] + parent2[cut:]
    return child


# ══════════════════════════════════════════════════════════════
# TAREA 3: MUTACIÓN
# ══════════════════════════════════════════════════════════════

def mutate(individual, prob=0.2):
    for i in range(len(individual)):
        if random.random() < prob:
            current_block, current_room = individual[i]
            mutation_type = random.choice([1, 2, 3])

            if mutation_type == 1:
                # Cambiar solo el bloque de tiempo
                new_block = random.choice(time_blocks)
                individual[i] = (new_block, current_room)

            elif mutation_type == 2:
                # Cambiar solo el salón
                new_room = random.choice(list(rooms.keys()))
                individual[i] = (current_block, new_room)

            else:
                # Cambiar ambos: bloque y salón
                new_block = random.choice(time_blocks)
                new_room = random.choice(list(rooms.keys()))
                individual[i] = (new_block, new_room)

    return individual

def selection(population):
    """Selección por torneo de 3 individuos."""
    tournament = random.sample(population, 3)
    return max(tournament, key=fitness)

def evolve(population, generations=50, verbose=True):
    """Ejecuta el algoritmo genético."""
    best_overall = None
    best_overall_fitness = float('-inf')
    
    for gen in range(generations):
        # Elitismo: mantener los 2 mejores
        sorted_pop = sorted(population, key=fitness, reverse=True)
        new_population = sorted_pop[:2]
        
        # Generar resto de población
        while len(new_population) < len(population):
            parent1 = selection(population)
            parent2 = selection(population)
            child = crossover(parent1, parent2)
            child = mutate(child)
            new_population.append(child)

        population = new_population
        
        # Mejor de esta generación
        best = max(population, key=fitness)
        best_fit = fitness(best)
        
        if best_fit > best_overall_fitness:
            best_overall = best
            best_overall_fitness = best_fit
        
        if verbose and (gen % 10 == 0 or gen == generations - 1):
            print(f"Gen {gen+1:3d}: Mejor fitness = {best_fit:6.1f}")
    
    return best_overall

print("✓ Funciones de evolución cargadas") 

# ══════════════════════════════════════════════════════════════
# BONUS: Visualización de la evolución con matplotlib
# ══════════════════════════════════════════════════════════════

def evolve_with_plot(population, generations=100):
    """
    Igual que evolve(), pero guarda el mejor fitness de cada
    generación y al final grafica la curva de evolución.
    """
    best_overall = None
    best_overall_fitness = float('-inf')
    history = []   # mejor fitness por generación

    for gen in range(generations):
        # Elitismo: los 2 mejores pasan directos
        sorted_pop = sorted(population, key=fitness, reverse=True)
        new_population = sorted_pop[:2]

        while len(new_population) < len(population):
            parent1 = selection(population)
            parent2 = selection(population)
            child = crossover(parent1, parent2)
            child = mutate(child)
            new_population.append(child)

        population = new_population

        best = max(population, key=fitness)
        best_fit = fitness(best)
        history.append(best_fit)

        if best_fit > best_overall_fitness:
            best_overall = best
            best_overall_fitness = best_fit

        if gen % 10 == 0 or gen == generations - 1:
            print(f"Gen {gen+1:3d}: Mejor fitness = {best_fit:6.1f}")

    # ── Gráfica ──────────────────────────────────────────────
    plt.figure(figsize=(10, 5))
    plt.plot(range(1, generations + 1), history, color='steelblue', linewidth=2)
    plt.axhline(y=200, color='green', linestyle='--', linewidth=1.5,
                label='Fitness perfecto (200)')
    plt.xlabel('Generación')
    plt.ylabel('Mejor Fitness')
    plt.title('Evolución del Fitness a lo largo de las generaciones')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

    return best_overall

# ══════════════════════════════════════════════════════════════
# Funciones extra
# ══════════════════════════════════════════════════════════════

def print_schedule(individual):
    """Imprime un horario de forma legible."""
    print("\n" + "="*60)
    print("HORARIO")
    print("="*60)
    for i, (block, room) in enumerate(individual):
        name, students = courses[i]
        print(f"{name:3s} | {block_names[block]:10s} | Salón {room} (Cap:{rooms[room]:2d}) | Est:{students:2d}")
    print("="*60)

def create_random_individual():
    """Crea un individuo aleatorio."""
    individual = []
    for i in range(len(courses)):
        block = random.choice(time_blocks)
        room = random.choice(list(rooms.keys()))
        individual.append((block, room))
    return individual

def create_population(size=20):
    """Crea una población inicial."""
    return [create_random_individual() for _ in range(size)]

# Probar
sample = create_random_individual()
print_schedule(sample)

if __name__ == "__main__":
    initial_pop = create_population(size=30)
    best_solution = evolve_with_plot(initial_pop, generations=100)
    print_schedule(best_solution)
    print(f"\nFitness final: {fitness(best_solution)}")