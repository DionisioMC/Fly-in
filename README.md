*This project has been created as part of the 42 curriculum by dcoelho.*

# Fly-in

## Description

**Fly-in** is a Python drone traffic simulation. The goal of the project is to simulate the movement of multiple drones through a network of interconnected hubs while respecting movement restrictions, connection capacities, and hub occupancy limits.

The simulation uses a map represented as a graph. Drones must travel from a starting hub to a destination hub, choosing routes that account for movement costs, congestion, restricted areas and priority areas.

The program calculates drone movements turn by turn, coordinating multiple drones to avoid exceeding hub and connection capacities.

### Main features

- Graph-based map representation.
- Multiple drones moving simultaneously.
- Shortest path calculation using Dijkstra's algorithm.
- Movement costs depending on hub zone type.
- Hub occupancy and connection capacity management.
- Restricted zones requiring an additional turn to move.
- Blocked zones that drones cannot enter.
- Turn-by-turn simulation output.
- Colored terminal output to improve readability.

## Instructions

### Requirements

- Python 3.10 or later.
- pip.
- Git.

The project uses **Pydantic v2** for data validation.

### Installation

Clone the repository:

```bash
git clone git@github.com:DionisioMC/Fly-in.git
cd Fly-in
```

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
make install
```

### Execution

Run the simulation with:

```bash
python3 fly_in.py map.txt

or

make
```

Replace `map.txt` with the path to the map file you want to simulate.

### Linting

The project includes two Makefile rules for code quality checks.

Run:

```bash
make lint

or

make lint-strict
```

This executes Flake8 and mypy to check code style and type annotations. However, lint-strict is more demanding.

## Algorithm and Implementation Strategy

### Map representation

The map is represented as an undirected graph:

- **Hubs:** zones where drones can be located.
- **Connections:** Connections linking two hubs.

Each hub contains information such as its name, coordinates, color, zone type, and maximum drone capacity.

Each connection defines the two connected hubs and the maximum number of drones allowed to use that connection simultaneously.

The map is parsed from an input file and validated using Pydantic models.

### Pathfinding: Dijkstra's algorithm

The simulation uses Dijkstra's algorithm to calculate paths between hubs.

Instead of considering only the number of connections, the algorithm assigns movement costs to hubs according to their zone types.

The current movement costs are:

| Zone | Movement cost |
|---|---:|
| Normal | 10 |
| Priority | 9 |
| Restricted | 20 |
| Blocked | Cannot be entered |

The algorithm also considers congestion:

- Hubs that have reached their capacity receive an additional cost.
- Connections that have reached their capacity receive an additional cost when considering the drone's next movement.

These penalties encourage drones to choose less congested routes when alternatives are available.

The resulting path is the lowest-cost path according to the current map conditions and planned occupancy.

### Drone movement

Each drone maintains its current position and movement state.

A drone can be in one of the following situations:

- Located at a hub.
- Moving directly to another hub.
- In transit to a restricted zone through a connection.
- Delivered to its destination.

Entering a restricted zone requires an additional turn.

When a drone starts this transit:

1. It leaves its current hub.
2. Its destination hub is reserved.
3. Its transit state is recorded.
4. On the following turn, it completes the transit and occupies the destination hub.

This prevents other drones from taking capacity already reserved by a drone in transit.

### Simultaneous movement resolution

Since multiple drones can attempt to move during the same turn, movements must be coordinated.

The simulation first calculates proposed movements and then resolves conflicts before applying them.

The resolution process considers:

- Maximum hub occupancy.
- Maximum connection capacity.
- Existing reservations for drones in transit.
- Reservations that will be released by completed transits.
- Drones leaving and entering hubs during the same turn.

If a proposed movement would exceed a capacity limit, it is rejected.

This approach ensures that the final state of each turn respects the map's constraints.

### Simulation loop

The simulation proceeds turn by turn:

1. Identify drones that can complete their transit.
2. Calculate the planned occupancy of hubs.
3. Find paths for drones that need to move.
4. Generate proposed movements.
5. Resolve capacity conflicts.
6. Complete existing transits.
7. Apply accepted movements.
8. Save the resulting state of the simulation.

The process repeats until all drones reach their destinations.

## Visual Representation

The simulation uses ANSI escape codes to display colored output in the terminal.

Colors improve readability by helping distinguish elements during execution.

The visual representation includes:

- Colored hub names.
- Distinct colors for different visual elements.
- Turn-by-turn drone positions.
- Explicit transit indicators showing when a drone is between hubs.

For example, a drone in transit is represented using an indicator such as:

```text
D1-start_hub-destiny_hub
```

This makes it easier to follow drone movements, identify transit operations, and understand how the simulation progresses.

The use of colors also makes the output easier to scan when several drones are moving simultaneously.

## Example

### Execution

```bash
python3 fly_in.py map.txt
```

## Project Structure

```text
Fly-in/
├── mapgen/
│   ├── __init__.py
│   ├── algorithm.py
│   ├── const.py
│   ├── models.py
│   ├── parser.py
│   └── pathfinder.py
├── maps/
├── .flake8
├── .gitignore
├── fly_in.py
├── Makefile
└── README.md
├── requirements.txt
```

The `mapgen/` module contains the project's core implementation, including data models, map parsing, and simulation logic.

## Resources

The following resources were useful for understanding and implementing the project:

### Python

- [Python Documentation](https://docs.python.org/3/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Python Heap Queue — heapq](https://docs.python.org/3/library/heapq.html)

### Algorithms and Graph Theory

- [Dijkstra's Algorithm — Wikipedia](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)
- [Introduction to Graph Theory — Wikipedia](https://en.wikipedia.org/wiki/Graph_theory)

### Data Validation

- [Pydantic Documentation](https://docs.pydantic.dev/latest/)

### Artificial Intelligence Usage

AI tools were used as development assistance during the project.

They were used for:

- Reviewing Python concepts, type annotations, and Pydantic v2.
- Improving code documentation through PEP 257 and Google-style docstrings.
- Structuring and drafting the `README`.