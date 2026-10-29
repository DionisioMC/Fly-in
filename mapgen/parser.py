from typing import Any
from .models import Hub, Connection


class Parser:
    @staticmethod
    def parse(raw_data: list[str]) -> dict[str, Any]:
        data: list[str] = list(filter(lambda line: line and not line.
                                      startswith("#"), raw_data))
        if not data[0].startswith("nb_drones:"):
            raise ValueError("Map file must start with: nb_drones: "
                             "<positive_integer>\nLine: 1")
        elif (len([line for line in data if line.startswith("start_hub: ")])
              == 0):
            raise ValueError("Map file must have one 'start_hub' property")
        elif (len([line for line in data if line.startswith("start_hub: ")])
              > 1):
            error = [(index, line) for index, line in enumerate(raw_data) if
                     line.startswith("start_hub: ")][1]
            raise ValueError("There can only be one 'start_hub' property in "
                             f"the map file\nLine: {error[0] + 1}")
        elif (len([line for line in data if line.startswith("end_hub: ")])
              == 0):
            raise ValueError("Map file must have one 'end_hub' property")
        elif (len([line for line in data if line.startswith("end_hub: ")])
              > 1):
            error = [(index, line) for index, line in enumerate(raw_data) if
                     line.startswith("end_hub: ")][1]
            raise ValueError("There can only be one 'end_hub' property in the "
                             f"map file\nLine: {error[0] + 1}")
        map: dict[str, Any] = {}
        hubs: list[Hub] = []
        connections: list[Connection] = []

        def parse_metadata(
            data: str,
            allowed_keys: list[str],
        ) -> dict[str, Any]:
            data = data.strip()
            if not (data.startswith("[") and data.endswith("]")):
                raise ValueError("Metadata must be enclosed in square brackets"
                                 )
            metadata: dict[str, Any] = {}
            for item in data[1:-1].split():
                if "=" not in item:
                    raise ValueError(f"Invalid metadata entry '{item}'")
                key, value = item.split("=", 1)
                if key not in allowed_keys:
                    raise ValueError(f"Unknown metadata key '{key}'")
                if key in metadata:
                    raise ValueError(f"Duplicate metadata key '{key}'")
                if not value:
                    raise ValueError(f"Missing value for metadata key '{key}'")
                metadata[key] = value
            return metadata

        def parse_hub(data: str) -> dict[str, Any]:
            data_list = data.split(" ", 3)
            metadata: dict[str, Any] = {}
            if len(data_list) == 4:
                metadata = parse_metadata(data_list[3], ["color", "zone",
                                                         "max_drones"])
            hub: dict[str, Any] = {
                "name": data_list[0],
                "coords": (data_list[1], data_list[2]),
                **metadata
            }
            return hub

        def parse_con(data: str) -> dict[str, Any]:
            data_list = data.split(" ", 1)
            hub_1, hub_2 = data_list[0].split("-")
            metadata: dict[str, Any] = {}
            if len(data_list) == 2:
                metadata = parse_metadata(data_list[1], ["max_link_capacity"])
            con: dict[str, Any] = {
                "hub_1": hub_1 if hub_1 < hub_2 else hub_2,
                "hub_2": hub_2 if hub_1 < hub_2 else hub_1,
                **metadata
            }
            return con
        for line in data:
            key, value = line.split(":", 1)
            if key == "hub":
                hubs.append(Hub(**parse_hub(value.strip())))
            elif key == "connection":
                connections.append(Connection(**parse_con(value.strip())
                                              ))
            else:
                map[key] = value.strip()
            map["hubs"] = hubs
            map["connections"] = connections
        parsed_start: dict[str, Any] = parse_hub(map["start_hub"])
        parsed_start.pop("max_drones", None)
        parsed_end: dict[str, Any] = parse_hub(map["end_hub"])
        parsed_end.pop("max_drones", None)
        map["start_hub"] = Hub(**parsed_start)
        map["end_hub"] = Hub(**parsed_end)
        return map
