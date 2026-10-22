from .map import Map
from .models import Drone, Hub, ZoneType


class Algorithm:
    def __init__(self, map: Map):
        self.drones: list[Drone] = []
        for i in range(1, map.nb_drones + 1):
            self.drones.append(Drone(
                name=f"D{i}",
                start_hub=map.start_hub.name,
                end_hub=map.end_hub.name))
        self.map = map

    def get_map(self, start_hub: str, end_hub: str, hub_dict: dict[str, Hub]
                ) -> dict[str, list[str]]:
        map_dict: dict[str, list[str]] = {}
        map_dict[start_hub] = list(
            map(lambda con: con.hub_1 if con.hub_2 == start_hub else con.hub_2,
                filter(lambda con: con.hub_1 == start_hub or
                       con.hub_2 == start_hub, self.map.connections))
        )
        map_dict[end_hub] = []
        for hub in [hub for hub in hub_dict.keys()]:
            map_dict[hub] = list(
                map(lambda con: con.hub_1 if con.hub_2 == hub else con.hub_2,
                    filter(lambda con: con.hub_1 == hub or con.hub_2 == hub,
                           self.map.connections))
            )
        return map_dict

    def has_path(self, start_hub: str, end_hub: str, map_dict: dict[
            str, list[str]]) -> bool:
        queue: list[str] = []
        visited: set[str] = set()
        queue.append(start_hub)
        visited.add(start_hub)
        came_from: dict[str, str] = {}
        while len(queue):
            current_hub: str = queue.pop(0)
            if current_hub == end_hub:
                break
            for hub in map_dict[current_hub]:
                if len(map_dict[hub]) and hub not in visited:
                    visited.add(hub)
                    came_from[hub] = current_hub
                    queue.append(hub)
        if not came_from.get(end_hub):
            return False
        return True

    def run(self) -> None:
        start_hub: str = self.map.start_hub.name
        end_hub: str = self.map.end_hub.name
        hub_dict: dict[str, Hub] = {
            start_hub: self.map.start_hub,
            end_hub: self.map.end_hub,
            **{hub.name: hub for hub in self.map.hubs
               if hub.zone != ZoneType.BLOCKED}
        }
        map_dict: dict[str, list[str]] = self.get_map(start_hub, end_hub,
                                                      hub_dict)
        if not self.has_path(start_hub, end_hub, map_dict):
            raise ValueError("There is no path from star_hub to end_hub")
