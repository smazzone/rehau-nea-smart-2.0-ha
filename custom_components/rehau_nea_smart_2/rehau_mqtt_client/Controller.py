"""Controller module for the REHAU NEA SMART 2 integration."""
from collections.abc import Callable
from .utils import replace_keys, EnergyLevels, OperationModes, ClientTopics
from .handlers import update_temperature, update_energy_level, update_operating_mode
from .models import Installation, Zone, LiveEmu
from .MqttClient import MqttClient
from .exceptions import MqttClientError
from homeassistant.core import HomeAssistant


class Controller:
    """Controller class for the REHAU NEA SMART 2 integration."""

    def __init__(self, hass: HomeAssistant, email: str, password: str):
        """Initializ the Controller object.

        Args:
            email (str): The email address for authentication.
            password (str): The password for authentication.
        """
        self.id = "REHAU NEA SMART 2.0"
        self.name = "REHAU NEA SMART 2.0 Climate Control System"
        self.model = "Neasmart 2.0 Base Station"
        self.manufacturer = "Rehau"
        self.auth_username = email
        self.auth_password = password
        self.mqtt_client = None
        self.hass = hass

    async def connect(self):
        """Connect to the MQTT broker and authenticates the user."""
        self.mqtt_client = MqttClient(hass=self.hass, username=self.auth_username, password=self.auth_password)
        await self.mqtt_client.auth_user()

    async def disconnect(self):
        """Disconnect from the MQTT broker."""
        self.mqtt_client.disconnect()

    def is_connected(self, installation_unique: str):
        """Check if the installation is connected to the MQTT broker."""
        Installations = self.get_installations_as_dict()
        if Installations is None:
            return False
        for installation in Installations:
            if installation["unique"] == installation_unique:
                return installation["connected"]


    def is_authenticated(self):
        """Check if the user is authenticated.

        Returns:
            bool: True if authenticated, False otherwise.
        """
        return self.mqtt_client.is_authenticated()

    def get_installations(self) -> list[Installation]:
        """Retrieve the list of installations.

        Returns:
            list[Installation]: The list of installations.
        """
        installations = self.mqtt_client.get_installations()
        if installations is None:
            return None
        return [Installation(**installation) for installation in installations]

    def get_live_emus(self) -> list[LiveEmu]:
        """Retrieve the list of installations.

        Returns:
            list[Installation]: The list of installations.
        """
        live_emus = self.mqtt_client.get_live_emus()
        if live_emus is None:
            return None
        return [LiveEmu(**live_emu) for forlive_emu in live_emus]

    def get_installations_as_dict(self) -> list[dict]:
        """Retrieve the list of installations as a dictionary.

        Returns:
            list[dict]: The list of installations as a dictionary.
        """
        return self.mqtt_client.get_installations()

    def get_live_emus_as_dict(self) -> list[dict]:
        """Retrieve the list of installations as a dictionary.

        Returns:
            list[dict]: The list of installations as a dictionary.
        """
        return self.mqtt_client.get_live_emus()

    def get_live_didos_as_dict(self) -> list[dict]:
        """Retrieve the list of installations as a dictionary.

        Returns:
            list[dict]: The list of installations as a dictionary.
        """
        return self.mqtt_client.get_live_didos()

    def get_zones(self) -> list[Zone]:
        """Retrieve the list of zones.

        Returns:
            list[Zone]: The list of zones.
        """
        zones = []
        for installation in self.get_installations():
            for group in installation.groups:
                for zone in group.zones:
                    zones.append(zone)
        return zones

    def get_zone(self, zone_id: int) -> Zone:
        """Retrieve a specific zone by zone id.

        Args:
            zone_id (int): The zone id.

        Returns:
            Zone: The zone object.

        Raises:
            MqttClientError: If no zone is found for the given zone id.
        """
        for zone in self.get_zones():
            if zone.id == zone_id:
                return zone
        raise MqttClientError("No zone found for zone " + str(zone_id))

    def get_installation_unique_by_zone(self, zone_id: int) -> str:
        """Retrieve the unique installation identifier for a specific zone.

        Args:
            zone_id (int): The zone id.

        Returns:
            str: The unique installation identifier.

        Raises:
            MqttClientError: If no zone is found for the given zone id.
        """
        installations = self.get_installations_as_dict()
        for installation in installations:
            for group in installation["groups"]:
                for zone in group["zones"]:
                    if zone["id"] == zone_id:
                        return installation["unique"]
        raise MqttClientError("No zone found for zone " + str(zone_id))

    def get_zone_value_by_key(self, key: str, zone_id: int):
        """Retrieve the value of a specific key for a specific zone.

        Args:
            key (str): The key to retrieve the value for.
            zone_id (int): The zone id.

        Returns:
            Any: The value of the key.

        Raises:
            MqttClientError: If no zone is found for the given zone id or if no value is found for the key.
        """
        installations = self.get_installations_as_dict()
        for installation in installations:
            for group in installation["groups"]:
                for zone in group["zones"]:
                    if zone["id"] == zone_id:
                        if len(zone["channels"]) > 1 or key != "_id":
                            values = []
                            for channel in zone["channels"]:
                                if key in channel:
                                    values.append(channel[key])
                            if len(values) == 0:
                                raise MqttClientError(
                                    "No value found for key "
                                    + key
                                    + " in zone "
                                    + str(zone_id)
                                )
                            return sum(values) / len(values)
                        else:
                            raise MqttClientError(
                                "Multiple channels found for zone "
                                + str(zone_id)
                                + " cannot return _id"
                            )
        raise MqttClientError("No zone found for zone " + str(zone_id))

    def get_temperature(self, zone_id: int, unit="C") -> float:
        """Retrieve the temperature for a specific zone.

        Args:
            zone_id (int): The zone id.
            unit (str, optional): The unit of temperature. Defaults to "C".

        Returns:
            float: The temperature value.

        Raises:
            MqttClientError: If no zone is found for the given zone id.
        """
        temperature = self.get_zone_value_by_key("current_temperature", zone_id) / 10
        if unit == "C":
            temperature_celsius = (temperature - 32) / 1.8
            return round(temperature_celsius, 1)

        return temperature

    def get_humidity(self, zone_id: int) -> float:
        """Retrieve the humidity for a specific zone.

        Args:
            zone_id (int): The zone id.

        Returns:
            float: The humidity value.

        Raises:
            MqttClientError: If no zone is found for the given zone id.
        """
        return self.get_zone_value_by_key("humidity", zone_id)

    def set_temperature(self, payload: dict):
        """Set the temperature for a specific zone.

        Args:
            payload (dict): The payload containing the temperature and zone information.

        Returns:
            Any: The result of the message sending operation.

        Raises:
            MqttClientError: If the temperature or zone is not found in the payload.
        """
        if "temperature" not in payload:
            raise MqttClientError("No temperature found in payload")

        if "zone" not in payload:
            raise MqttClientError("No zone found in payload")

        temperature = payload["temperature"] * 10
        if "unit" not in payload or payload["unit"] == "C":
            temperature = temperature * 1.8 + 320

        int_temperature = int(temperature)

        temperature_request = replace_keys(
            {
                "controller": payload["controller"] if "controller" in payload else 0,
                "data": {"setpoint_used": int_temperature},
                "type": "REQ_TH",
                "zone": payload["zone"],
            },
            self.mqtt_client.get_referentials(),
        )

        update_temperature(self.get_installations_as_dict(), payload["zone"], int_temperature)
        return self.mqtt_client.send_message(ClientTopics.INSTALLATION.value, temperature_request)

    def get_energy_level(self, zone_id: int) -> EnergyLevels:
        """Retrieve the energy level for a specific zone.

        Args:
            zone_id (int): The zone id.

        Returns:
            EnergyLevels: The energy level.

        Raises:
            MqttClientError: If no zone is found for the given zone id.
        """
        energy_level = self.get_zone_value_by_key("energy_level", zone_id)
        return EnergyLevels(energy_level)

    def set_energy_level(self, payload: dict):
        """Set the energy level for a specific zone.

        Args:
            payload (dict): The payload containing the mode and zone information.

        Returns:
            Any: The result of the message sending operation.

        Raises:
            MqttClientError: If the mode or zone is not found in the payload.
        """
        if "mode" not in payload:
            raise MqttClientError("No mode found in payload")

        if "zone" not in payload:
            raise MqttClientError("No zone found in payload")

        energy_level_request = replace_keys(
            {
                "controller": payload["controller"] if "controller" in payload else 0,
                "data": {"mode_permanent": payload["mode"]},
                "type": "REQ_TH",
                "zone": payload["zone"],
            },
            self.mqtt_client.get_referentials(),
        )

        update_energy_level(self.get_installations_as_dict(), payload["zone"], payload["mode"])
        return self.mqtt_client.send_message(ClientTopics.INSTALLATION.value, energy_level_request)

    def get_global_energy_level(self) -> EnergyLevels:
        """Retrieve the global energy level.

        Returns:
            Any: The global energy level.

        Raises:
            MqttClientError: If no installations are found.
        """
        self.installations = self.get_installations_as_dict()
        return self.installations[0]["global_energy_level"]

    def set_global_energy_level(self, payload: dict):
        """Set the global energy level.

        Args:
            payload (dict): The payload containing the mode information.

        Returns:
            Any: The result of the message sending operation.

        Raises:
            MqttClientError: If the mode is not found in the payload.
        """
        if "mode" not in payload:
            raise MqttClientError("No mode found in payload")

        zones = {}
        for installation in self.get_installations_as_dict():
            zones[installation["unique"]] = []
            for group in installation["groups"]:
                for zone in group["zones"]:
                    zones[installation["unique"]].append(zone["number"])

        for _installation_unique, zones in zones.items():
            global_energy_level_request = replace_keys(
                {
                    "controller": payload["controller"]
                    if "controller" in payload
                    else 0,
                    "data": {"mode_used": payload["mode"], "zone_impacted": zones},
                    "type": "REQ_TH",
                },
                self.mqtt_client.get_referentials(),
            )

            return self.mqtt_client.send_message(ClientTopics.INSTALLATION.value, global_energy_level_request)

    def get_operation_mode(self) -> OperationModes:
        """Retrieve the operation mode.

        Returns:
            OperationModes: The operation mode.

        Raises:
            MqttClientError: If no installations are found.
        """
        installation = self.get_installations_as_dict()[0]
        return OperationModes(installation["operating_mode"])

    def set_operation_mode(self, mode: str|int):
        """Set the operation mode.

        Args:
            mode (str|int): The operation mode.

        Returns:
            Any: The result of the message sending operation.

        Raises:
            MqttClientError: If the mode is not found in the payload.
        """
        if mode is None:
            raise MqttClientError("No mode found in payload")

        # mode to string with 0 padding
        mode = str(mode).zfill(2)

        operation_mode_request = replace_keys(
            {
                "data": {"heat_cool": mode},
                "type": "REQ_TH",
            },
            self.mqtt_client.get_referentials(),
        )


        update_operating_mode(self.get_installations_as_dict(), self.mqtt_client.get_install_id, mode)
        return self.mqtt_client.send_message(ClientTopics.INSTALLATION.value, operation_mode_request)

    def is_ready(self) -> bool:
        """Check if the controller is connected to the MQTT broker.

        Returns:
            bool: True if connected, False otherwise.
        """
        return self.mqtt_client.is_ready()

    def register_callback(self, callback: Callable[[], None]) -> None:
        """Register callback, called when Roller changes state.

        Args:
            callback (Callable[[], None]): Callback to be called when Roller changes state.
        """
        self.mqtt_client.register_callback(callback)

    def remove_callback(self, callback: Callable[[], None]) -> None:
        """Remove previously registered callback.

        Args:
            callback (Callable[[], None]): Callback to be removed.
        """
        self.mqtt_client.remove_callback(callback)

    def get_installation_by_unique(self, installation_unique: str):
            """Return the installation."""
            Installations = self.get_installations_as_dict()
            if Installations is None:
                return False
            for installation in Installations:
                if installation["unique"] == installation_unique:
                    return installation
    
    def get_live_emu_by_unique(self, installation_unique: str):
            """Return the installation."""
            LiveEmus = self.get_live_emus_as_dict()
            if LiveEmus is None:
                return {"unique": installation_unique, "pumpOn": None, "mixed_circuit1_setpoint": None, "mixed_circuit1_supply": None, "mixed_circuit1_return": None, "mixed_circuit1_opening": None }
            for live_emu in LiveEmus:
                if live_emu["unique"] == installation_unique:
                    return live_emu
    
    def get_live_dido_by_unique(self, installation_unique: str):
            """Return the installation."""
            LiveDidos = self.get_live_didos_as_dict()
            if LiveDidos is None:
                return {"unique": installation_unique, "DI_1": None, "DI_2": None, "DI_3": None, "DI_4": None, "DI_5": None, "DO_1": None, "DO_2": None, "DO_3": None, "DO_4": None, "DO_5": None }
            for live_dido in LiveDidos:
                if live_dido["unique"] == installation_unique:
                    return live_dido

    def get_zone(self, zone_id: int) -> Zone:
        """Retrieve a specific zone by zone id.

        Args:
            zone_id (int): The zone id.

        Returns:
            Zone: The zone object.

        Raises:
            MqttClientError: If no zone is found for the given zone id.
        """
        for zone in self.get_zones():
            if zone.id == zone_id:
                return zone
        raise MqttClientError("No zone found for zone " + str(zone_id))

def update_temperature(installations: list[Installation], zone_id: str, temperature: float) -> list[Installation]:
    """Update temperature."""
    for installation in installations:
        for group in installation["groups"]:
            for zone in group["zones"]:
                if zone["id"] == zone_id:
                    for channel in zone["channels"]:
                        channel["target_temperature"] = temperature

    return installations

def update_energy_level(installations: list[Installation], zone_id: str, energy_level: int) -> list[Installation]:
    """Update energy level."""
    for installation in installations:
        for group in installation["groups"]:
            for zone in group["zones"]:
                if zone["id"] == zone_id:
                    for channel in zone["channels"]:
                        channel["energy_level"] = energy_level

    return installations

def get_global_energy_level(installation) -> EnergyLevels:
    """Calculate the global energy level based on the provided installation dictionary.

    Args:
        installation (dict): A dictionary representing the installation.

    Returns:
        EnergyLevels: The maximum EnergyLevels value representing the global energy level.
    """
    mode_count = {
        EnergyLevels.PRESENT_MODE.value: 0,
        EnergyLevels.ABSENT_MODE.value: 0,
        EnergyLevels.STANDBY_MODE.value: 0,
        EnergyLevels.TIMING_MODE.value: 0,
        EnergyLevels.PARTY_MODE.value: 0,
        EnergyLevels.HOLIDAY_MODE.value: 0,
    }

    for group in installation["groups"]:
        for zone in group["zones"]:
            for channel in zone["channels"]:
                if channel["mode_permanent"] == EnergyLevels.PRESENT_MODE.value:
                    mode_count[EnergyLevels.PRESENT_MODE.value] += 1
                elif channel["mode_permanent"] == EnergyLevels.ABSENT_MODE.value:
                    mode_count[EnergyLevels.ABSENT_MODE.value] += 1
                elif channel["mode_permanent"] == EnergyLevels.STANDBY_MODE.value:
                    mode_count[EnergyLevels.STANDBY_MODE.value] += 1
                elif channel["mode_permanent"] == EnergyLevels.TIMING_MODE.value:
                    mode_count[EnergyLevels.TIMING_MODE.value] += 1
                elif channel["mode_permanent"] == EnergyLevels.PARTY_MODE.value:
                    mode_count[EnergyLevels.PARTY_MODE.value] += 1
                elif channel["mode_permanent"] == EnergyLevels.HOLIDAY_MODE.value:
                    mode_count[EnergyLevels.HOLIDAY_MODE.value] += 1

    return EnergyLevels(max(mode_count, key=mode_count.get))
