from .models import Drone, Hub, Connection, Map
from .const import ZoneType, MovementCosts


class Algorithm:
    def __init__(self, map: Map):
        self.drones: list[Drone] = []
        for i in range(1, map.nb_drones + 1):
            self.drones.append(Drone(
                name=f"D{i}",
                current_hub=map.start_hub.name))
        self.nb_drones: int = map.nb_drones
        self.start_hub = map.start_hub
        self.end_hub = map.end_hub
        self.hubs: list[Hub] = [map.start_hub, map.end_hub, *map.hubs]
        self.hub_dict: dict[str, Hub] = {
            hub.name: hub for hub in self.hubs
        }
        self.connections: list[Connection] = map.connections
        self.build_map()
        self.occupied_hubs: dict[str, list[Drone]] = {}
        self.occupied_cons: dict[tuple[str, str], list[Drone]] = {}
        self.turn_num = 0
        self.turn_states: dict[int, dict[str, int]] = {}

    def can_move_hub(self, destiny_hub: str) -> bool:
        hub: Hub = self.hub_dict[destiny_hub]
        list_drones: list[Drone] = self.occupied_hubs.get(destiny_hub, [])
        if len(list_drones) >= hub.max_drones:
            return False
        return True

    def can_move_con(self, current_hub: str, destiny_hub: str) -> bool:
        name: tuple[str, str] = ((current_hub, destiny_hub) if
                                 current_hub < destiny_hub else
                                 (destiny_hub, current_hub))
        for connection in self.connections:
            hubs: tuple[str, str] = (connection.hub_1, connection.hub_2)
            if hubs == name:
                drones_in_con: list[Drone] = self.occupied_cons.get(name, [])
                if len(drones_in_con) >= connection.max_link_capacity:
                    return False
        return True

    def move_drone(self, drone: Drone, destiny_hub: str) -> None:
        if drone.current_hub in self.occupied_hubs.keys():
            self.occupied_hubs[drone.current_hub].remove(drone)
            if not self.occupied_hubs[drone.current_hub]:
                self.occupied_hubs.pop(drone.current_hub)
        name: tuple[str, str] = ((drone.current_hub, destiny_hub) if
                                 drone.current_hub < destiny_hub else
                                 (destiny_hub, drone.current_hub))
        if name not in self.occupied_cons.keys():
            self.occupied_cons[name] = []
        self.occupied_cons[name].append(drone)
        drone.current_hub = destiny_hub
        if destiny_hub == self.end_hub.name:
            drone.delivered = True
        if destiny_hub != self.end_hub.name:
            if destiny_hub not in self.occupied_hubs.keys():
                self.occupied_hubs[destiny_hub] = []
            self.occupied_hubs[destiny_hub].append(drone)
        self.occupied_cons[name].remove(drone)
        if not self.occupied_cons[name]:
            self.occupied_cons.pop(name)

    def run(self) -> dict[int, list[str]]:
        simul_result: dict[int, list[str]] = {}
        while not all(drone.delivered for drone in self.drones):
            self.turn_num += 1
            current_turn_moves: list[str] = []
            for drone in self.drones:
                if drone.delivered:
                    continue
                if drone.current_hub == self.end_hub.name:
                    drone.delivered = True
                    continue
                drone.path = self.get_shortest_path(drone.current_hub,
                                                    self.end_hub.name,
                                                    self.occupied_hubs)
                destiny_hub = drone.path[1]
                if drone.waiting_turns > 0:
                    drone.waiting_turns -= 1
                    continue
                elif not self.can_move_hub(destiny_hub):
                    continue
                elif not self.can_move_con(drone.current_hub,
                                           destiny_hub):
                    continue
                hub: Hub = self.hub_dict[destiny_hub]
                if hub.zone == ZoneType.RESTRICTED:
                    drone.waiting_turns = 1
                self.move_drone(drone, destiny_hub)
                current_turn_moves.append(f"{drone.name}-{destiny_hub}")
            if current_turn_moves:
                simul_result[self.turn_num] = current_turn_moves
            self.turn_states[self.turn_num] = {hub.name: 0 for hub in
                                               self.hubs}
            for drone in self.drones:
                self.turn_states[self.turn_num][drone.current_hub] += 1
        return simul_result

    def build_map(self) -> None:
        map: dict[str, list[str]] = {}
        for connection in self.connections:
            hub_1, hub_2 = connection.hub_1, connection.hub_2
            if hub_1 not in map.keys():
                map[hub_1] = []
            if hub_2 not in map.keys():
                map[hub_2] = []
            map[hub_1].append(hub_2)
            map[hub_2].append(hub_1)
        self.map: dict[str, list[str]] = map

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

    def get_shortest_path(self, start_hub: str, end_hub: str,
                          occupied_hubs: dict[str, list[Drone]]) -> list[str]:
        queue: list[tuple[int, str]] = []
        visited: set[str] = set()
        traced_path: dict[str, str] = {}
        costs: dict[str, int] = {}
        queue.append((0, start_hub))
        costs[start_hub] = 0
        while queue:
            current_cost, current_hub = queue.pop(0)
            if current_hub in visited:
                continue
            neighbors = [hub for hub in self.map[current_hub]]
            visited.add(current_hub)
            for neighbor in neighbors:
                hub: Hub = self.hub_dict[neighbor]
                drones_in_hub = len(
                    occupied_hubs.get(neighbor, []))
                hub_cost: int = MovementCosts[hub.zone.name].value
                move_cost: int = hub_cost + drones_in_hub
                new_cost: int = current_cost + move_cost
                if hub.zone == ZoneType.BLOCKED:
                    continue
                elif ((neighbor not in costs) or (new_cost < costs[neighbor])):
                    costs[neighbor] = new_cost
                    traced_path[neighbor] = current_hub
                    queue.append((new_cost, neighbor))
                elif (new_cost == costs[neighbor] and
                        hub.zone == ZoneType.PRIORITY):
                    traced_path[neighbor] = current_hub
                    queue.append((new_cost, neighbor))
            if current_hub == end_hub:
                break
            queue = sorted(queue, key=lambda pair: pair[0])
        return self.get_path(traced_path, start_hub, end_hub)
