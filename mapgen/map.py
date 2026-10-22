from pydantic import BaseModel, Field, model_validator
from .models import Hub, Connection


class Map(BaseModel):
    nb_drones: int = Field(ge=1)
    start_hub: Hub
    end_hub: Hub
    hubs: list[Hub]
    connections: list[Connection]

    @model_validator(mode="after")
    def validate_hub(self) -> "Map":
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
            raise ValueError("Every connection pair of connected hubs must be "
                             "unique")
        for connection in self.connections:
            if connection.hub_1 not in hub_names:
                raise ValueError("Unknown Hub in connection "
                                 f"'{connection.hub_1}'")
            elif connection.hub_2 not in hub_names:
                raise ValueError("Unknown Hub in connection "
                                 f"'{connection.hub_2}'")
        return self
