from .models import Drone, Map, Hub
from .const import ZoneType, Colors
from .pathfinder import PathFinder


class Algorithm:
    """Simulate drone movements across a map while respecting constraints.

    Manages drone positions, hub occupancy, connection capacities, and
    restricted-zone transit. Movement decisions are planned and resolved
    simultaneously at each turn.
    """
    def __init__(self, map: Map):
        """Initialize the simulation using the provided map.

        Args:
            map: Map containing the hubs, connections, and number of drones.
        """
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
        """Remove a drone from its current hub.

        Removes the hub from occupied_hubs if it becomes empty.

        Args:
            drone: Drone leaving its current hub.
        """
        origin = drone.current_hub
        self.occupied_hubs[origin].remove(drone)
        if not self.occupied_hubs[origin]:
            self.occupied_hubs.pop(origin)

    def _start_transit(self, drone: Drone, dest: str) -> None:
        """Start a drone's transit into a restricted destination.

        Removes the drone from its current hub and reserves a place at
        the destination until transit is completed.

        Args:
            drone: Drone entering transit.
            dest: Name of the restricted destination hub.
        """
        self._leave_hub(drone)
        self.reserved_hubs.setdefault(dest, []).append(drone)
        drone.in_transit = True
        drone.transit_dest = dest
        drone.transit_con = self.pathfinder.get_con_key(
            drone.current_hub, dest)

    def _complete_transit(self, drone: Drone) -> None:
        """Complete a drone's transit and place it at its destination.

        Updates the drone's position and transit status, releases its
        destination reservation, and marks it as delivered if it reaches
        the end hub.

        Args:
            drone: Drone whose transit is being completed.

        Raises:
            ValueError: If the drone has no recorded transit destination.
        """
        destination: str = drone.transit_dest
        self.reserved_hubs[destination].remove(drone)
        if not self.reserved_hubs[destination]:
            self.reserved_hubs.pop(destination)
        drone.current_hub = destination
        drone.in_transit = False
        drone.transit_dest = ""
        drone.transit_con = ("", "")
        drone.delivered = (destination == self.end_hub.name)
        self.occupied_hubs.setdefault(destination, []).append(drone)

    def _move_drone(self, drone: Drone, destiny_hub: str) -> None:
        """Move a drone directly to another hub.

        Updates hub occupancy and marks the drone as delivered if it
        reaches the end hub.

        Args:
            drone: Drone being moved.
            destiny_hub: Name of the destination hub.
        """
        self._leave_hub(drone)
        drone.current_hub = destiny_hub
        drone.delivered = destiny_hub == self.end_hub.name
        self.occupied_hubs.setdefault(destiny_hub, []).append(drone)

    def _resolve_movements(self, proposed_moves: list[tuple[Drone, str, str]],
                           transits_to_complete: list[Drone]
                           ) -> list[tuple[Drone, str, str]]:
        """Resolve proposed movements against connection and hub capacities.

        Iteratively rejects movements that exceed connection capacities
        or destination hub capacities. Accounts for reservations released
        by drones completing transit during the current turn.

        Args:
            proposed_moves: Proposed movements represented as
                (drone, origin hub, destination hub) tuples.
            transits_to_complete: Drones scheduled to complete transit
                during the current turn.

        Returns:
            List of accepted movements represented as
            (drone, origin hub, destination hub) tuples.
        """
        accepted: list[tuple[Drone, str, str]] = proposed_moves.copy()
        while True:
            keys: list[tuple[str, str]] = [
                self.pathfinder.get_con_key(move[1], move[2]) for move
                in accepted]
            incoming: dict[str, int] = {}
            outgoing: dict[str, int] = {}
            con_usage: dict[tuple[str, str], int] = {}
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
                    departing_reservations = sum(
                        1 for drone in transits_to_complete
                        if drone.transit_dest == hub.name
                    )
                    occupancy = (
                        current + reserved - departing_reservations
                        + incoming.get(hub.name, 0)
                        - outgoing.get(hub.name, 0)
                    )
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
        """Run the simulation until all drones reach the end hub.

        Plans and resolves movements once per turn, completes existing
        transits, and records the movements performed during each turn.

        Returns:
            Dictionary mapping each turn number to its list of drone
            movements.

        Raises:
            ValueError: If no drone can move or complete transit while
                at least one drone remains undelivered.
        """
        simul_result: dict[int, list[str]] = {}
        while not all(drone.delivered for drone in self.drones):
            self.turn_num += 1
            proposed_moves: list[tuple[Drone, str, str]] = []
            transits_to_complete: list[Drone] = [
                drone for drone in self.drones
                if drone.in_transit and not drone.delivered
            ]
            current_turn_moves: list[str] = []
            planned_occupancy: dict[str, int] = {
                hub.name: (
                    len(self.occupied_hubs.get(hub.name, []))
                    + len(self.reserved_hubs.get(hub.name, []))
                    - sum(
                        1 for drone in transits_to_complete
                        if drone.transit_dest == hub.name
                    )
                )
                for hub in self.hubs
            }
            con_usage: dict[tuple[str, str], int] = {}
            for drone in self.drones:
                if drone.delivered:
                    continue
                if drone.in_transit:
                    continue
                drone.path = self.pathfinder.get_shortest_path(
                    drone.current_hub, self.end_hub.name, planned_occupancy,
                    con_usage)
                if len(drone.path) < 2:
                    continue
                origin: str = drone.current_hub
                dest: str = drone.path[1]
                con_key = self.pathfinder.get_con_key(origin, dest)
                if (con_usage.get(con_key, 0) >= self.pathfinder.con_dict[
                        con_key].max_link_capacity):
                    continue
                proposed_moves.append((drone, origin, dest))
                planned_occupancy[origin] -= 1
                planned_occupancy[dest] += 1
                con_usage[con_key] = con_usage.get(con_key, 0) + 1
            accepted_moves: list[tuple[Drone, str, str]] = (
                self._resolve_movements(proposed_moves, transits_to_complete))
            for drone in transits_to_complete:
                transit_dest: str = drone.transit_dest
                color_dest: str = (self.pathfinder.hub_dict[dest].color
                                   .upper())
                if color_dest == Colors.RAINBOW.value:
                    color_dest = Colors.random_color().value
                colored_dest: str = (f"{Colors[color_dest].value}"
                                     f"{transit_dest}{Colors.END.value}")
                self._complete_transit(drone)
                current_turn_moves.append(
                    f"{drone.name}-{colored_dest}")
            for drone, org, dest in accepted_moves:
                hub = self.pathfinder.hub_dict[dest]
                if hub.zone == ZoneType.RESTRICTED:
                    self._start_transit(drone, dest)
                    color_org: str = (self.pathfinder.hub_dict[org].color
                                      .upper())
                    color_dest = (self.pathfinder.hub_dict[dest].color
                                  .upper())
                    if color_org == Colors.RAINBOW.value:
                        color_org = Colors.random_color().value
                    if color_dest == Colors.RAINBOW.value:
                        color_dest = Colors.random_color().value
                    colored_org: str = (f"{Colors[color_org].value}{org}"
                                        f"{Colors.END.value}")
                    colored_dest = (f"{Colors[color_dest].value}{dest}"
                                    f"{Colors.END.value}")
                    current_turn_moves.append(
                        f"{drone.name}-{colored_org}-{colored_dest}")
                else:
                    self._move_drone(drone, dest)
                    color: str = self.pathfinder.hub_dict[dest].color.upper()
                    if color == Colors.RAINBOW.value:
                        color = Colors.random_color().name
                    current_turn_moves.append(
                        f"{drone.name}-{Colors[color].value}{dest}"
                        f"{Colors.END.value}")
            if not accepted_moves and not transits_to_complete:
                raise ValueError(f"Simulation stuck at turn {self.turn_num}")
            if current_turn_moves:
                simul_result[self.turn_num] = sorted(
                    current_turn_moves,
                    key=lambda move: int(move.split("-")[0][1:]))
        return simul_result
