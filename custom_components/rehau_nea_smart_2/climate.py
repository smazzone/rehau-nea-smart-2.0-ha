"""Platform for climate integration."""
import logging
from .rehau_mqtt_client import Installation, Zone
from .rehau_mqtt_client.Controller import Controller

from .const import (
    DOMAIN,
    NAME,
    VERSION,
    PRESET_ENERGY_LEVELS_MAPPING,
    PRESET_ENERGY_LEVELS_MAPPING_REVERSE,
    PRESET_CLIMATE_MODES_MAPPING,
    PRESET_CLIMATE_MODES_MAPPING_REVERSE,
)
from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityDescription,
    ClimateEntityFeature,
    HVACMode,
    HVACAction
)
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.const import ATTR_TEMPERATURE

_LOGGER = logging.getLogger(__name__)

ENTITY_DESCRIPTIONS = (
    ClimateEntityDescription(
        key="rehau_nea_smart_2",
        name="Integration Climate",
        icon="mdi:home-thermometer",
        translation_key="rehauneasmart2",
    ),
)


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up the climate platform."""
    controller: Controller = hass.data[DOMAIN][entry.entry_id]
    installations: list[Installation] = controller.get_installations()

    devices = []

    for entity_description in ENTITY_DESCRIPTIONS:
        for installation in installations:
            for group in installation.groups:
                for zone in group.zones:
                    devices.append(
                        RehauNeaSmart2RoomClimate(controller, zone, installation.operating_mode, installation.unique, entity_description)
                    )

    async_add_devices(devices)


class IntegrationRehauNeaSmart2Climate(ClimateEntity, RestoreEntity):
    """Representation of a Rehau Nea Smart 2 climate entity."""

    _attr_has_entity_name = False
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    should_poll = False

    def __init__(self, controller: Controller, zone: Zone, operating_mode: str, installation_unique: str):
        """Initialize the Rehau Nea Smart 2 climate entity."""
        self._controller = controller
        self._state = None
        self._installation_unique = installation_unique
        channel = zone.channels[0]

        attributes = {
            "id": zone.id,
            "name": zone.name,
            "zone_number": zone.number,
            "current_temp": channel.current_temperature,
            "target_temp": channel.target_temperature,
            "mode": channel.energy_level,
            "max_temp": channel.setpoints.max,
            "min_temp": channel.setpoints.min,
            "operation_mode": operating_mode,
            "heating_normal": channel.setpoints.heating.normal,
            "heating_reduced": channel.setpoints.heating.reduced,
            "heating_standby": channel.setpoints.heating.standby,
            "cooling_normal": channel.setpoints.cooling.normal,
            "cooling_reduced": channel.setpoints.cooling.reduced,
            "current_humidity": channel.humidity
        }

        for attribute in attributes:
            setattr(self, f"_{attribute}", attributes[attribute])

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name=NAME,
            model=VERSION,
            manufacturer=NAME,
        )


    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        self._controller.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        """Run when this Entity will be removed from HA."""
        self._controller.remove_callback(self.async_write_ha_state)

    @property
    def device_info(self):
        """Return device information for the climate entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._controller.id)},
            name=self._controller.name,
            manufacturer=self._controller.manufacturer,
            model=self._controller.model,
        )

    @property
    def available(self) -> bool:
        """Return True if the climate entity is available."""
        return self._controller.is_connected(self._installation_unique)


class RehauNeaSmart2RoomClimate(IntegrationRehauNeaSmart2Climate):
    """Representation of a Rehau Nea Smart 2 room climate entity."""

    def __init__(
            self,
            controller: Controller,
            zone,
            operating_mode,
            installation_unique: str,
            entity_description: ClimateEntityDescription,
    ):
        """Initialize the Rehau Nea Smart 2 room climate entity."""
        super().__init__(controller, zone, operating_mode, installation_unique)
        self._attr_unique_id = f"{self._id}_thermostat"
        self._attr_name = f"{self._name} Thermostat"
        self._attr_supported_features |= ClimateEntityFeature.PRESET_MODE
        self._attr_supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE
        self._attr_hvac_modes = [HVACMode.AUTO, HVACMode.HEAT, HVACMode.COOL]
        self._attr_hvac_action = HVACAction.IDLE
        self._attr_preset_modes = list(PRESET_ENERGY_LEVELS_MAPPING.keys())
        self.entity_description = entity_description

        self._attr_preset_mode = PRESET_ENERGY_LEVELS_MAPPING_REVERSE[self._mode]
        self._attr_hvac_mode = PRESET_CLIMATE_MODES_MAPPING[self._operation_mode]
        self._attr_current_temperature = self.format_temperature(self._current_temp)
        self._attr_target_temperature = self.format_temperature(self._target_temp, True)
        self._attr_max_temp = self.format_temperature(self._max_temp)
        self._attr_min_temp = self.format_temperature(self._min_temp)
        self._attr_current_humidity = self._current_humidity

    def format_temperature(self, temperature, round_half=False) -> float:
        """Format the temperature."""
        converted_temperature = (temperature / 10 - 32) / 1.8

        if round_half:
            return round(2 * converted_temperature) / 2
        else:
            return round(converted_temperature, 1)

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        _LOGGER.debug(f"Getting current temperature for zone {self._zone_number} with name {self._name} and ID {self._id}")
        zone = self._controller.get_zone(self._id)
        if zone is not None:
            channel = zone.channels[0]
            _LOGGER.debug(f"Current temperature {self.format_temperature(channel.current_temperature)} for zone {self._zone_number} with name {self._name} and ID {self._id}")
            return self.format_temperature(channel.current_temperature)

        return self._attr_current_temperature

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        _LOGGER.debug(f"Getting target temperature for zone {self._zone_number} with name {self._name} and ID {self._id}")
        zone = self._controller.get_zone(self._id)
        if zone is not None:
            channel = zone.channels[0]
            if channel.target_temperature is not None: 
                return self.format_temperature(channel.target_temperature, True) if channel.target_temperature>0 else self.format_temperature(channel.current_temperature, True)
            else:
                return None

        return self._attr_target_temperature

    @property
    def current_humidity(self) -> float | None:
        """Return current humidity."""
        _LOGGER.debug(f"Getting current humidity for zone {self._zone_number} with name {self._name} and ID {self._id}")
        zone = self._controller.get_zone(self._id)
        if zone is not None:
            channel = zone.channels[0]
            _LOGGER.debug(f"Current humidity {channel.humidity} for zone {self._zone_number} with name {self._name} and ID {self._id}")
            return channel.humidity if channel.humidity>0 else None

        return self._attr_current_humidity

    @property
    def hvac_mode(self) -> str | None:
        """Return the current operation mode."""
        _LOGGER.debug(f"Getting operation mode for zone {self._zone_number} with name {self._name} and ID {self._id}")
        zone = self._controller.get_zone(self._id)
        if zone is not None:
            channel = zone.channels[0]
            return PRESET_CLIMATE_MODES_MAPPING[channel.operating_mode]

        return self._attr_hvac_mode
    
    @property
    def hvac_action(self) -> str | None:
        """Hvac action."""
        _LOGGER.debug(f"Getting HVAC action for zone {self._zone_number} with name {self._name} and ID {self._id}")
        zone = self._controller.get_zone(self._id)
        if zone is not None:
            channel = zone.channels[0]
            if channel.demand == 0:
                return HVACAction.IDLE
            else:
                if self._attr_hvac_mode == HVACMode.OFF:
                    return HVACAction.IDLE
                elif self._attr_hvac_mode == HVACMode.AUTO:
                    return HVACAction.COOLING
                elif self._attr_hvac_mode == HVACMode.HEAT:
                    return HVACAction.HEATING
                elif self._attr_hvac_mode == HVACMode.COOL:
                    return HVACAction.COOLING
        return self._attr_hvac_action

    @property
    def preset_mode(self) -> str | None:
        """Return the current energy level."""
        _LOGGER.debug(f"Getting energy level for zone {self._zone_number} with name {self._name} and ID {self._id}")
        zone = self._controller.get_zone(self._id)
        if zone is not None:
            channel = zone.channels[0]
            return PRESET_ENERGY_LEVELS_MAPPING_REVERSE[channel.energy_level]

        return self._attr_preset_mode

    async def async_set_preset_mode(self, preset_mode: str):
        """Set the preset mode of the climate entity."""
        mode = PRESET_ENERGY_LEVELS_MAPPING[preset_mode]
        _LOGGER.debug(f"Setting mode to {mode} for zone {self._zone_number} with name {self._name} and ID {self._id}")
        self._controller.set_energy_level({"zone": self._id, "mode": mode})

    async def async_set_temperature(self, **kwargs):
        """Set the target temperature of the climate entity."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        _LOGGER.debug(f"Setting temperature to {temperature} for zone {self._zone_number} with name {self._name} and ID {self._id}")
        self._controller.set_temperature({"zone": self._id, "temperature": temperature})

    async def async_set_hvac_mode(self, hvac_mode: str):
        """Set the HVAC mode of the climate entity."""
        operation_mode = PRESET_CLIMATE_MODES_MAPPING_REVERSE[hvac_mode]
        _LOGGER.debug(f"Setting operation mode to {operation_mode} for zone {self._zone_number} with name {self._name} and ID {self._id}")
        self._controller.set_operation_mode(operation_mode)

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
