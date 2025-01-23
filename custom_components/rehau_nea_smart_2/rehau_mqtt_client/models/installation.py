"""Type definitions for the installation data."""
from typing import Optional
from pydantic import BaseModel


class Cooling(BaseModel):
    """Type definition for cooling data.

    Cooling represents the cooling setpoints for a Channel.
    It contains normal and reduced temperature values.
    """

    normal: int
    reduced: int


class Heating(BaseModel):
    """Type definition for heating data.

    Heating represents the heating setpoints for a Channel.
    It contains normal, reduced, and standby temperature values.
    """

    normal: int
    reduced: int
    standby: int


class Setpoints(BaseModel):
    """Type definition for setpoints data.

    Setpoints represent the temperature setpoints for a Channel,
    including cooling and heating setpoints, as well as minimum and maximum values.
    """

    cooling: Cooling
    heating: Heating
    min: int
    max: int


class Channel(BaseModel):
    """Type definition for channel data.

    A Channel represents an individual control unit within a Zone.
    It contains data such as target and current temperatures, energy levels,
    operating modes, humidity, demand, and setpoints.
    """

    id: str
    target_temperature: Optional[int]
    current_temperature: int
    energy_level: int
    operating_mode: int
    humidity: int
    demand: int
    setpoints: Setpoints


class Zone(BaseModel):
    """Type definition for zone data.

    A Zone is a collection of Channels. It represents a specific area or room
    within a Group. Each Zone has an identifier, name, number, and a list of Channels.
    """

    id: str
    name: str
    number: int
    channels: list[Channel]


class Group(BaseModel):
    """Type definition for group data.

    A Group is a collection of Zones. It represents a larger section or category
    within an Installation. Each Group has an identifier, name, and a list of Zones.
    """

    id: str
    group_name: str
    zones: list[Zone]


class Installation(BaseModel):

    """Type definition for installation data.

    An Installation is the top-level entity that contains multiple Groups.
    It represents the entire system setup. Each Installation has an identifier,
    unique key, global energy level, connection status, operating mode,
    a list of Groups, and outside temperature data.
    """

    id: str
    unique: str
    global_energy_level: int
    connected: bool
    operating_mode: int
    groups: list[Group]
    outside_temp: int
    outsideTempFiltered: int

class LiveEmu(BaseModel):
    """
    LiveEmu represents the live status of an Emu device in the installation.
    """
    unique: str
    pumpOn: bool
    mixed_circuit1_setpoint: Optional[int]
    mixed_circuit1_supply: Optional[int]
    mixed_circuit1_return: Optional[int]
    mixed_circuit1_opening: Optional[int]

class LiveDido(BaseModel):
    """Type definition for live digital input/output data.

    LiveDido represents the live status of digital inputs and outputs in the installation.
    It contains the status of five digital inputs (DI) and five digital outputs (DO).
    """

    unique: str
    DI_1: bool
    DI_2: bool
    DI_3: bool
    DI_4: bool
    DI_5: bool
    DO_1: bool
    DO_2: bool
    DO_3: bool
    DO_4: bool
    DO_5: bool
