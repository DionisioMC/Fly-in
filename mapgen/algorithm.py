from .models import Drone, Hub, Connection, Map
from .const import ZoneType, MovementCosts
import heapq


class Algorithm:
    def __init__(self, map: Map):
        self.drones: list[Drone] = [
            Drone(name=f"D{i}", current_hub=map.start_hub.name)
            for i in range(1, map.nb_drones + 1)
        ]
        self.start_hub = map.start_hub
        self.end_hub = map.end_hub
        self.hubs: list[Hub] = [map.start_hub, map.end_hub, *map.hubs]
        self.hub_dict: dict[str, Hub] = {
            hub.name: hub for hub in self.hubs
        }
        self.map: dict[str, list[str]] = {
            hub.name: [] for hub in self.hubs
        }
        for con in map.connections:
            self.map[con.hub_1].append(con.hub_2)
            self.map[con.hub_2].append(con.hub_1)
        self.occupied_hubs: dict[str, list[Drone]] = {
            self.start_hub.name: self.drones.copy()
        }
        self.turn_num = 0
        self.connection_dict: dict[tuple[str, str], Connection] = {
            (con.hub_1, con.hub_2): con
            for con in map.connections
        }
        self.reserved_hubs: dict[str, list[Drone]] = {}

    def get_con_key(self, hub_1: str, hub_2: str) -> tuple[str, str]:
        return ((hub_1, hub_2) if hub_1 < hub_2
                else (hub_2, hub_1))

    def get_path(self, traced_path: dict[str, str], start: str, end: str
                 ) -> list[str]:
        path: list[str] = [end]
        while path[-1] != start:
            path.append(traced_path[path[-1]])
        path.reverse()
        return path

    def resolve_movements(self, proposed_moves: list[tuple[Drone, str, str]]
                          ) -> list[tuple[Drone, str, str]]:
        accepted: list[tuple[Drone, str, str]] = proposed_moves.copy()
        while True:
            keys = [self.get_con_key(move[1], move[2]) for move in accepted]
            connection_usage: dict[tuple[str, str], int] = {}
            for key in keys:
                connection_usage[key] = connection_usage.get(key, 0) + 1
            fixed: bool = False
            for key, count in connection_usage.items():
                excess = count - self.connection_dict[key].max_link_capacity
                if excess > 0:
                    drop = set([i for i, k in enumerate(keys) if k == key]
                               [-excess:])
                    accepted = [m for i, m in enumerate(accepted) if i not in
                                drop]
                    fixed = True
                    break
            if fixed:
                continue
            for hub in self.hubs:
                if hub.name in (self.start_hub.name, self.end_hub.name):
                    continue
                incoming: int = len([m for m in accepted if m[2] == hub.name])
                outgoing: int = len([m for m in accepted if m[1] == hub.name])
                occupancy: int = (len(self.occupied_hubs.get(hub.name, []))
                                  + len(self.reserved_hubs.get(hub.name, []))
                                  + incoming - outgoing)
                excess = occupancy - hub.max_drones
                if excess > 0:
                    drop = set([i for i, m in enumerate(accepted)
                                if m[2] == hub.name][-excess:])
                    accepted = [m for i, m in enumerate(accepted) if i not in
                                drop]
                    fixed = True
                    break
            if not fixed:
                return accepted

    def _leave_hub(self, drone: Drone) -> None:
        origin = drone.current_hub
        self.occupied_hubs[origin].remove(drone)
        if not self.occupied_hubs[origin]:
            self.occupied_hubs.pop(origin)

    def start_transit(self, drone: Drone, destination: str) -> None:
        self._leave_hub(drone)
        self.reserved_hubs.setdefault(destination, []).append(drone)
        drone.in_transit = True
        drone.transit_destination = destination
        drone.transit_connection = self.get_con_key(drone.current_hub,
                                                    destination)

    def complete_transit(self, drone: Drone) -> None:
        destination: str | None = drone.transit_destination
        if destination is None:
            raise ValueError(f"{drone.name} has invalid transit information")
        self.reserved_hubs[destination].remove(drone)
        if not self.reserved_hubs[destination]:
            self.reserved_hubs.pop(destination)
        drone.current_hub = destination
        drone.in_transit = False
        drone.transit_destination = None
        drone.transit_connection = None
        drone.delivered = destination == self.end_hub.name
        self.occupied_hubs.setdefault(destination, []).append(drone)

    def get_shortest_path(self, start_hub: str, end_hub: str,
                          planned_occupancy: dict[str, int]
                          ) -> list[str]:
        queue: list[tuple[int, str]] = [(0, start_hub)]
        visited: set[str] = set()
        traced_path: dict[str, str] = {}
        costs: dict[str, int] = {start_hub: 0}
        while queue:
            current_cost, current_hub = heapq.heappop(queue)
            if current_hub in visited:
                continue
            if current_hub == end_hub:
                break
            visited.add(current_hub)
            for neigh in self.map[current_hub]:
                if neigh in visited:
                    continue
                hub: Hub = self.hub_dict[neigh]
                if hub.zone == ZoneType.BLOCKED:
                    continue
                new_cost: int = (current_cost + MovementCosts[hub.zone.name].
                                 value + planned_occupancy.get(neigh, 0))
                if new_cost < costs.get(neigh, 0):
                    costs[neigh] = new_cost
                    traced_path[neigh] = current_hub
                    heapq.heappush(queue, (new_cost, neigh))
        if end_hub not in costs:
            return []
        return self.get_path(traced_path, start_hub, end_hub)

    def move_drone(self, drone: Drone, destiny_hub: str) -> None:
        self._leave_hub(drone)
        drone.current_hub = destiny_hub
        drone.delivered = destiny_hub == self.end_hub.name
        self.occupied_hubs.setdefault(destiny_hub, []).append(drone)

    def run(self) -> dict[int, list[str]]:
        simul_result: dict[int, list[str]] = {}
        while not all(drone.delivered for drone in self.drones):
            self.turn_num += 1
            proposed_moves: list[tuple[Drone, str, str]] = []
            transits_to_complete: list[Drone] = []
            current_turn_moves: list[str] = []
            planned_occupancy: dict[str, int] = {
                hub.name: len(self.occupied_hubs.get(hub.name, []))
                + len(self.reserved_hubs.get(hub.name, []))
                for hub in self.hubs
            }
            for drone in self.drones:
                if drone.delivered:
                    continue
                if drone.in_transit:
                    transits_to_complete.append(drone)
                    continue
                drone.path = self.get_shortest_path(
                    drone.current_hub, self.end_hub.name, planned_occupancy)
                if len(drone.path) < 2:
                    continue
                origin: str = drone.current_hub
                dest: str = drone.path[1]
                proposed_moves.append((drone, origin, dest))
                planned_occupancy[origin] -= 1
                planned_occupancy[dest] += 1
            accepted_moves: list[tuple[Drone, str, str]] = (
                self.resolve_movements(proposed_moves))
            for drone, origin, destination in accepted_moves:
                hub = self.hub_dict[destination]
                if hub.zone == ZoneType.RESTRICTED:
                    self.start_transit(drone, destination)
                    current_turn_moves.append(
                        f"{drone.name}-transit->{destination}")
                else:
                    self.move_drone(drone, destination)
                    current_turn_moves.append(
                        f"{drone.name}-{destination}")
            for drone in transits_to_complete:
                transit_destination: str | None = drone.transit_destination
                self.complete_transit(drone)
                current_turn_moves.append(
                    f"{drone.name}-{transit_destination}")
            if current_turn_moves:
                simul_result[self.turn_num] = sorted(
                    current_turn_moves,
                    key=lambda move: int(move.split("-")[0][1:]))
        return simul_result
