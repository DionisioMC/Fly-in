from heapq import heappush, heappop
from .const import MovementCosts, ZoneType
from .models import Hub, Map, Connection


class PathFinder:
    """Find routes between hubs while considering movement constraints.

    Builds a graph representation of the map and uses Dijkstra's
    algorithm to calculate paths. Path costs account for zone movement
    costs, hub occupancy, and connection capacity.
    """
    def __init__(self, map: Map, hubs: list[Hub]) -> None:
        """Initialize the pathfinder using the provided map.

        Builds the adjacency list, hub lookup dictionary, connection
        lookup dictionary, and set of hubs with unlimited capacity.

        Args:
            map: Map containing hubs and their connections.
            hubs: List of all hubs available on the map.
        """
        self.map: dict[str, list[str]] = {
            hub.name: [] for hub in hubs
        }
        for con in map.connections:
            self.map[con.hub_1].append(con.hub_2)
            self.map[con.hub_2].append(con.hub_1)
        self.unlimited_hubs: set[str] = {map.start_hub.name, map.end_hub.name}
        self.con_dict: dict[tuple[str, str], Connection] = {
            (con.hub_1, con.hub_2): con
            for con in map.connections
        }
        self.hub_dict: dict[str, Hub] = {
            hub.name: hub for hub in hubs
        }

    @staticmethod
    def get_con_key(hub_1: str, hub_2: str) -> tuple[str, str]:
        """Generate a canonical key for a connection between two hubs.

        Sorts the hub names alphabetically so that a connection has the
        same key regardless of the order in which its endpoints are given.

        Args:
            hub_1: Name of the first hub.
            hub_2: Name of the second hub.

        Returns:
            tuple[str, str]: Alphabetically ordered pair of hub names.
        """
        return ((hub_1, hub_2) if hub_1 < hub_2
                else (hub_2, hub_1))

    def _get_path(self, traced_path: dict[str, str], start: str, end: str
                  ) -> list[str]:
        """Reconstruct a path using the predecessor dictionary.

        Args:
            traced_path: Dictionary mapping each visited hub to its
                predecessor in the calculated path.
            start: Name of the starting hub.
            end: Name of the destination hub.

        Returns:
            list[str]: Ordered list of hub names forming the path,
            including the starting and destination hubs.
        """
        path: list[str] = [end]
        while path[-1] != start:
            path.append(traced_path[path[-1]])
        path.reverse()
        return path

    def get_shortest_path(
            self, start_hub: str, end_hub: str,
            planned_occupancy: dict[str, int],
            con_usage: dict[tuple[str, str], int]) -> list[str]:
        """Calculate the lowest-cost path between two hubs.

        Uses Dijkstra's algorithm to find a route while avoiding blocked
        zones and accounting for movement costs, planned hub occupancy,
        and connection usage.

        Args:
            start_hub: Name of the hub from which the route begins.
            end_hub: Name of the destination hub.
            planned_occupancy: Dictionary mapping hub names to their
                expected occupancy during the current turn.
            con_usage: Dictionary mapping connection keys to the number
                of drones currently planned to use each connection.

        Returns:
            list[str]: Ordered list of hub names representing the
            lowest-cost path. Returns an empty list if no valid path
            exists.
        """
        queue: list[tuple[int, str]] = [(0, start_hub)]
        visited: set[str] = set()
        traced_path: dict[str, str] = {}
        costs: dict[str, int] = {start_hub: 0}
        while queue:
            current_cost, current_hub = heappop(queue)
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
                hub_load: int = planned_occupancy.get(neigh, 0)
                is_full: bool = (neigh not in self.unlimited_hubs
                                 and hub_load >= hub.max_drones)
                con_key: tuple[str, str] = self.get_con_key(current_hub,
                                                            neigh)
                is_con_full: bool = (
                    current_hub == start_hub and con_usage.get(con_key, 0)
                    >= self.con_dict[con_key].max_link_capacity)
                turn_cost: int = MovementCosts.NORMAL.value
                new_cost: int = (
                    current_cost + MovementCosts[hub.zone.name].value
                    + (turn_cost if is_full else 0)
                    + (2 * turn_cost if is_con_full else 0))
                if neigh not in costs or new_cost < costs[neigh]:
                    costs[neigh] = new_cost
                    traced_path[neigh] = current_hub
                    heappush(queue, (new_cost, neigh))
        if end_hub not in costs:
            return []
        return self._get_path(traced_path, start_hub, end_hub)
