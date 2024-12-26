"""Binary Sensor platform for rehau_nea_smart_2."""

from __future__ import annotations
import logging

from homeassistant.components.binary_sensor import (
	BinarySensorDeviceClass,
	BinarySensorEntity,
	BinarySensorEntityDescription,
)

from .rehau_mqtt_client import Installation, Zone, LiveEmu
from .rehau_mqtt_client.Controller import Controller

from .const import DOMAIN

ENTITY_DESCRIPTIONS = (
	BinarySensorEntityDescription(
		key="rehau_nea_smart_2",
		name="Integration Binary Sensor"
	),
)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
	"""Set up the binary_sensor platform."""
	controller: Controller = hass.data[DOMAIN][entry.entry_id]

	installations: list[Installation] = controller.get_installations()

	devices = []

	for entity_description in ENTITY_DESCRIPTIONS:
		for installation in installations:
			live_emu = controller.get_live_emu_by_unique(installation.unique)
			devices.append(
				RehauNeasmart2BinarySensorSensor(
					controller, live_emu, "pumpOn", "Pump is on", entity_description
				)
			)
	async_add_entities(devices)


class RehauNeasmart2BinarySensorSensor(SensorEntity, BinarySensorEntity):

	def __init__(self, controller: Controller, live_emu: dict, propertyname: str, name: str, entity_description: SensorEntityDescription):
		self._live_emu = live_emu
		self._controller = controller
		self._available = True
		self._name = f"{name}"
		self._propertyname = propertyname
		self._installation_unique = live_emu["unique"]
		self._unique_name = name.lower().replace(" ", "_")
		self._attr_unique_id = f"{self._installation_unique}_{self._unique_name}"
		self._attr_name = self._name
		self.entity_description = entity_description

	async def async_added_to_hass(self) -> None:
		"""Run when this Entity has been added to HA."""
		self._controller.register_callback(self.async_write_ha_state)

	async def async_will_remove_from_hass(self):
		"""Run when this Entity will be removed from HA."""
		self._controller.remove_callback(self.async_write_ha_state)
	
	@property
	def is_on(self) -> bool:
		"""Return true if the binary_sensor is on."""
		return live_emu.get(self._propertyname)