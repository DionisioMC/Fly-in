from pydantic import BaseModel, Field, model_validator
from .const import ZoneType


class Hub(BaseModel):
    """Represent a hub (node) on the drone map.

    Attributes:
        name: Unique identifier of the hub. Cannot contain dashes.
        coords: X and Y coordinates representing the hub's position.
        color: Display color used when rendering the hub.
        zone: Zone type determining the hub's movement rules.
        max_drones: Maximum number of drones allowed at the hub.
    """
    name: str
    coords: tuple[int, int]
    color: str = Field(default="white")
    zone: ZoneType = ZoneType.NORMAL
    max_drones: int = Field(ge=1, default=1)

    @model_validator(mode="after")
    def validate_hub(self) -> "Hub":
        """Validate the hub's name.

        Ensures that the hub name does not contain dashes.

        Returns:
            Hub: The validated hub instance.

        Raises:
            ValueError: If the hub name contains a dash.
        """
        if "-" in self.name:
            raise ValueError("Hub names cannot contain dashes")
        return self


class Connection(BaseModel):
    """Represent a connection between two hubs.

    Attributes:
        hub_1: Name of the first connected hub.
        hub_2: Name of the second connected hub.
        max_link_capacity: Maximum number of drones allowed on the
            connection simultaneously.
    """
    hub_1: str
    hub_2: str
    max_link_capacity: int = Field(ge=1, default=1)

    @model_validator(mode="after")
    def validate_connection(self) -> "Connection":
        """Validate the names of the connected hubs.

        Ensures that neither hub name contains dashes.

        Returns:
            Connection: The validated connection instance.

        Raises:
            ValueError: If either hub name contains a dash.
        """
        if "-" in self.hub_1 or "-" in self.hub_2:
            raise ValueError("Hub names cannot contain dashes")
        return self


class Drone(BaseModel):
    """Represent a drone operating on the map.

    Attributes:
        name: Unique identifier of the drone.
        current_hub: Name of the hub where the drone is currently located.
        path: List of hub names representing the drone's planned route.
        in_transit: Indicates whether the drone is currently in transit.
        transit_dest: Destination hub reserved by the drone during transit.
        transit_con: Connection currently being used by the drone.
        delivered: Indicates whether the drone has reached its destination.
    """
    name: str
    current_hub: str
    path: list[str] = []
    in_transit: bool = False
    transit_dest: str = ""
    transit_con: tuple[str, str] = ("", "")
    delivered: bool = False


class Map(BaseModel):
    """Represent the complete drone transportation map.

    Contains the starting and ending hubs, intermediate hubs, available
    connections, and the total number of drones participating in the
    simulation.

    Attributes:
        nb_drones: Number of drones to simulate. Must be at least one.
        start_hub: Hub where all drones begin.
        end_hub: Destination hub that all drones must reach.
        hubs: List of intermediate hubs on the map.
        connections: List of available connections between hubs.
    """
    nb_drones: int = Field(ge=1)
    start_hub: Hub
    end_hub: Hub
    hubs: list[Hub]
    connections: list[Connection]

    @model_validator(mode="after")
    def validate_hub(self) -> "Map":
        """Validate hub and connection consistency across the map.

        Checks that:
            - Every hub has a unique name.
            - Every hub has unique coordinates.
            - Every connection is unique.
            - Every connection references existing hubs.
            - The starting and ending hubs are not blocked.

        Returns:
            Map: The validated map instance.

        Raises:
            ValueError: If any map consistency rule is violated.
        """
        hub_names: list[str] = [self.start_hub.name, self.end_hub.name,
                                *(hub.name for hub in self.hubs)]
        hub_coords: list[tuple[int, int]] = [self.start_hub.coords,
                                             self.end_hub.coords,
                                             *(hub.coords for hub in self.hubs)
                                             ]
        con_hubs: list[tuple[str, str]] = [(con.hub_1, con.hub_2) for con in
                                           self.connections]
        if len(hub_names) != len(set(hub_names)):
            raise ValueError("Every hub name must be unique")
        if len(hub_coords) != len(set(hub_coords)):
            raise ValueError("Every hubs coordenates must be unique")
        if len(con_hubs) != len(set(con_hubs)):
            raise ValueError("Every connection must be unique")
        for con in self.connections:
            if con.hub_1 not in hub_names:
                raise ValueError("Unknown Hub in connection "
                                 f"'{con.hub_1}'")
            elif con.hub_2 not in hub_names:
                raise ValueError("Unknown Hub in connection "
                                 f"'{con.hub_2}'")
        if (self.start_hub.zone == ZoneType.BLOCKED or
                self.end_hub.zone == ZoneType.BLOCKED):
            raise ValueError("start_hub and end_hub cannot be blocked zones")
        return self
