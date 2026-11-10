from .models import Drone, Map, Hub
from .const import ZoneType
from .pathfinder import PathFinder


class Algorithm:
    def __init__(self, map: Map):
        self.drones: list[Drone] = [
            Drone(name=f"D{i}", current_hub=map.start_hub.name)
            for i in range(1, map.nb_drones + 1)
        ]
        start_hub: Hub = map.start_hub
        self.end_hub: Hub = map.end_hub
        self.hubs: list[Hub] = [start_hub, map.end_hub, *map.hubs]
        self.pathfinder: PathFinder = PathFinder(map, self.hubs)
        self.turn_num = 0
        self.reserved_hubs: dict[str, list[Drone]] = {}
        self.occupied_hubs: dict[str, list[Drone]] = {
            start_hub.name: self.drones.copy()
        }

    def _leave_hub(self, drone: Drone) -> None:
        origin = drone.current_hub
        self.occupied_hubs[origin].remove(drone)
        if not self.occupied_hubs[origin]:
            self.occupied_hubs.pop(origin)

    def _start_transit(self, drone: Drone, destination: str) -> None:
        self._leave_hub(drone)
        self.reserved_hubs.setdefault(destination, []).append(drone)
        drone.in_transit = True
        drone.transit_destination = destination
        drone.transit_connection = self.pathfinder.get_con_key(
            drone.current_hub, destination)

    def _complete_transit(self, drone: Drone) -> None:
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
        drone.delivered = (destination == self.end_hub.name)
        self.occupied_hubs.setdefault(destination, []).append(drone)

    def _move_drone(self, drone: Drone, destiny_hub: str) -> None:
        self._leave_hub(drone)
        drone.current_hub = destiny_hub
        drone.delivered = destiny_hub == self.end_hub.name
        self.occupied_hubs.setdefault(destiny_hub, []).append(drone)

    def _resolve_movements(self, proposed_moves: list[tuple[Drone, str, str]],
                           transit_usage: dict[tuple[str, str], int]
                           ) -> list[tuple[Drone, str, str]]:
        accepted: list[tuple[Drone, str, str]] = proposed_moves.copy()
        while True:
            keys: list[tuple[str, str]] = [
                self.pathfinder.get_con_key(move[1], move[2]) for move
                in accepted]
            incoming: dict[str, int] = {}
            outgoing: dict[str, int] = {}
            con_usage: dict[tuple[str, str], int] = dict(transit_usage)
            for key in keys:
                con_usage[key] = con_usage.get(key, 0) + 1
            for _, origin, dest in accepted:
                outgoing[origin] = outgoing.get(origin, 0) + 1
                incoming[dest] = incoming.get(dest, 0) + 1
            drop: set[int] = set()
            for key in dict.fromkeys(keys):
                excess: int = (con_usage[key] - self.pathfinder.con_dict[key]
                               .max_link_capacity)
                if excess > 0:
                    idxs = [i for i, k in enumerate(keys)
                            if k == key]
                    if idxs:
                        drop = set(idxs[-excess:])
                        break
            if not drop:
                for hub in self.hubs:
                    if hub.name in self.pathfinder.unlimited_hubs:
                        continue
                    current: int = len(self.occupied_hubs.get(hub.name, ()))
                    reserved: int = len(self.reserved_hubs.get(hub.name, ()))
                    occupancy: int = (current + reserved
                                      + incoming.get(hub.name, 0)
                                      - outgoing.get(hub.name, 0))
                    excess = occupancy - hub.max_drones
                    if excess > 0:
                        idxs = [i for i, m in enumerate(accepted)
                                if m[2] == hub.name]
                        if idxs:
                            drop = set(idxs[-excess:])
                            break
                if not drop:
                    return accepted
            accepted = [m for i, m in enumerate(accepted) if i not in drop]

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
            con_usage: dict[tuple[str, str], int] = {}
            for drone in self.drones:
                if drone.in_transit and drone.transit_connection:
                    key = drone.transit_connection
                    con_usage[key] = con_usage.get(key, 0) + 1
            transit_usage: dict[tuple[str, str], int] = dict(con_usage)
            for drone in self.drones:
                if drone.delivered:
                    continue
                if drone.in_transit:
                    transits_to_complete.append(drone)
                    continue
                drone.path = self.pathfinder.get_shortest_path(
                    drone.current_hub, self.end_hub.name, planned_occupancy,
                    con_usage)
                if len(drone.path) < 2:
                    continue
                origin: str = drone.current_hub
                dest: str = drone.path[1]
                key = self.pathfinder.get_con_key(origin, dest)
                if (con_usage.get(key, 0) >= self.pathfinder.con_dict[key]
                        .max_link_capacity):
                    continue
                proposed_moves.append((drone, origin, dest))
                planned_occupancy[origin] -= 1
                planned_occupancy[dest] += 1
                con_usage[key] = con_usage.get(key, 0) + 1
            accepted_moves: list[tuple[Drone, str, str]] = (
                self._resolve_movements(proposed_moves, transit_usage))
            for drone, _, destination in accepted_moves:
                hub = self.pathfinder.hub_dict[destination]
                if hub.zone == ZoneType.RESTRICTED:
                    self._start_transit(drone, destination)
                    current_turn_moves.append(
                        f"{drone.name}-transit->{destination}")
                else:
                    self._move_drone(drone, destination)
                    current_turn_moves.append(
                        f"{drone.name}-{destination}")
            for drone in transits_to_complete:
                transit_destination: str | None = drone.transit_destination
                self._complete_transit(drone)
                current_turn_moves.append(
                    f"{drone.name}-{transit_destination}")
            if not accepted_moves and not transits_to_complete:
                raise ValueError(f"Simulation stuck at turn {self.turn_num}")
            if current_turn_moves:
                simul_result[self.turn_num] = sorted(
                    current_turn_moves,
                    key=lambda move: int(move.split("-")[0][1:]))
        return simul_result
