from heapq import heappush, heappop
from .const import MovementCosts, ZoneType
from .models import Hub, Map, Connection


class PathFinder:
    def __init__(self, map: Map, hubs: list[Hub]) -> None:
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
        return ((hub_1, hub_2) if hub_1 < hub_2
                else (hub_2, hub_1))

    def _get_path(self, traced_path: dict[str, str], start: str, end: str
                  ) -> list[str]:
        path: list[str] = [end]
        while path[-1] != start:
            path.append(traced_path[path[-1]])
        path.reverse()
        return path

    def get_shortest_path(
            self, start_hub: str, end_hub: str,
            planned_occupancy: dict[str, int],
            con_usage: dict[tuple[str, str], int]) -> list[str]:
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
