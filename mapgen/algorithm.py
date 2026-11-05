from .models import Drone, Hub, Connection, Map
from .const import ZoneType, MovementCosts


class Algorithm:
    def __init__(self, map: Map):
        self.drones: list[Drone] = []
        for i in range(1, map.nb_drones + 1):
            self.drones.append(Drone(
                name=f"D{i}",
                current_hub=map.start_hub.name))
        self.start_hub = map.start_hub
        self.end_hub = map.end_hub
        self.hubs: list[Hub] = [map.start_hub, map.end_hub, *map.hubs]
        self.hub_dict: dict[str, Hub] = {
            hub.name: hub for hub in self.hubs
        }
        self.map: dict[str, list[str]] = {
            hub.name: [] for hub in self.hubs
        }
        for connection in map.connections:
            hub_1, hub_2 = connection.hub_1, connection.hub_2
            self.map[hub_1].append(hub_2)
            self.map[hub_2].append(hub_1)
        self.occupied_hubs: dict[str, list[Drone]] = {
            self.start_hub.name: self.drones.copy()
        }
        self.occupied_cons: dict[tuple[str, str], list[Drone]] = {}
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
        current = end
        path: list[str] = []
        if end == start:
            return [start]
        while current != start:
            path.append(current)
            current = traced_path[current]
        path.append(start)
        path.reverse()
        return path

    def resolve_movements(self, proposed_moves: list[tuple[Drone, str, str]]
                          ) -> list[tuple[Drone, str, str]]:
        accepted: list[tuple[Drone, str, str]] = proposed_moves.copy()
        changed: bool = True
        while changed:
            changed = False
            connection_usage: dict[tuple[str, str], int] = {}
            for drone in self.drones:
                if drone.in_transit and drone.transit_connection:
                    key = drone.transit_connection
                    connection_usage[key] = (
                        connection_usage.get(key, 0) + 1)
            for drone, origin, destination in accepted:
                key = self.get_con_key(origin, destination)
                connection_usage[key] = connection_usage.get(key, 0) + 1
            for key, count in connection_usage.items():
                capacity: int = self.connection_dict[key].max_link_capacity
                if count > capacity:
                    con_candidates: list[tuple[Drone, str, str]] = [
                        move for move in accepted
                        if self.get_con_key(move[1], move[2]) == key
                    ]
                    con_excess: int = count - capacity
                    for move in con_candidates[-con_excess:]:
                        accepted.remove(move)
                    changed = True
            for hub in self.hubs:
                if hub.name in (self.start_hub.name, self.end_hub.name):
                    continue
                current: int = len(self.occupied_hubs.get(hub.name, []))
                reserved: int = len(self.reserved_hubs.get(hub.name, []))
                outgoing: int = len(
                    list(filter(lambda move: move[1] == hub.name, accepted)))
                incoming: int = len(
                    list(filter(lambda move: move[2] == hub.name, accepted)))
                final_occupancy: int = current + reserved + incoming - outgoing
                if final_occupancy > hub.max_drones:
                    hub_candidates: list[tuple[Drone, str, str]] = [
                        move for move in accepted if move[2] == hub.name]
                    hub_excess: int = final_occupancy - hub.max_drones
                    for move in hub_candidates[-hub_excess:]:
                        accepted.remove(move)
                    changed = True
        return accepted

    def start_transit(self, drone: Drone, destination: str) -> None:
        origin = drone.current_hub
        key = self.get_con_key(origin, destination)
        self.occupied_hubs[origin].remove(drone)
        if not self.occupied_hubs[origin]:
            self.occupied_hubs.pop(origin, [])
        self.reserved_hubs.setdefault(destination, []).append(drone)
        self.occupied_cons.setdefault(key, []).append(drone)
        drone.in_transit = True
        drone.transit_destination = destination
        drone.transit_connection = key

    def complete_transit(self, drone: Drone) -> None:
        destination: str | None = drone.transit_destination
        key: tuple[str, str] | None = drone.transit_connection
        if destination is None or key is None:
            raise ValueError(f"{drone.name} has invalid transit information")
        self.reserved_hubs[destination].remove(drone)
        if not self.reserved_hubs[destination]:
            self.reserved_hubs.pop(destination)
        self.occupied_cons[key].remove(drone)
        if not self.occupied_cons[key]:
            self.occupied_cons.pop(key)
        drone.in_transit = False
        drone.transit_destination = None
        drone.transit_connection = None
        drone.current_hub = destination
        self.occupied_hubs.setdefault(destination, []).append(drone)
        if destination == self.end_hub.name:
            drone.delivered = True

    def get_shortest_path(self, start_hub: str, end_hub: str,
                          planned_occupancy: dict[str, int]
                          ) -> list[str]:
        queue: list[tuple[int, str]] = [(0, start_hub)]
        visited: set[str] = set()
        traced_path: dict[str, str] = {}
        costs: dict[str, int] = {start_hub: 0}
        while queue:
            current_cost, current_hub = queue.pop(0)
            if current_hub in visited:
                continue
            neighbors = [hub for hub in self.map[current_hub]]
            visited.add(current_hub)
            for neigh in neighbors:
                hub: Hub = self.hub_dict[neigh]
                if hub.zone == ZoneType.BLOCKED:
                    continue
                drones_in_hub: int = planned_occupancy.get(neigh, 0)
                hub_cost: int = MovementCosts[hub.zone.name].value
                move_cost: int = hub_cost + drones_in_hub
                new_cost: int = current_cost + move_cost
                if ((neigh not in costs) or (new_cost < costs[neigh])):
                    costs[neigh] = new_cost
                    traced_path[neigh] = current_hub
                    queue.append((new_cost, neigh))
            if current_hub == end_hub:
                break
            queue = sorted(queue, key=lambda pair: pair[0])
        return self.get_path(traced_path, start_hub, end_hub)

    def move_drone(self, drone: Drone, destiny_hub: str) -> None:
        if drone.current_hub in self.occupied_hubs.keys():
            self.occupied_hubs[drone.current_hub].remove(drone)
            if not self.occupied_hubs[drone.current_hub]:
                self.occupied_hubs.pop(drone.current_hub)
        drone.current_hub = destiny_hub
        if destiny_hub == self.end_hub.name:
            drone.delivered = True
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
                simul_result[self.turn_num] = sorted(current_turn_moves,
                                                     key=lambda move:
                                                         move.split("-")[0])
        return simul_result
