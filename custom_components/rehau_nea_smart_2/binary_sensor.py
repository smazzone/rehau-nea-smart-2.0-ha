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
				RehauNeasmart2BinarySensorForLiveEmu(
					controller, live_emu, "pumpOn", "Pump is on", entity_description
				)
			)
			live_dido = controller.get_live_dido_by_unique(installation.unique)
			devices.append(
				RehauNeasmart2BinarySensorForLiveDido(
					controller, live_dido, "DO_1", "Digital Output 1", entity_description
				)
			)
			devices.append(
				RehauNeasmart2BinarySensorForLiveDido(
					controller, live_dido, "DO_2", "Digital Output 2", entity_description
				)
			)
			devices.append(
				RehauNeasmart2BinarySensorForLiveDido(
					controller, live_dido, "DO_3", "Digital Output 3", entity_description
				)
			)
			devices.append(
				RehauNeasmart2BinarySensorForLiveDido(
					controller, live_dido, "DO_4", "Digital Output 4", entity_description
				)
			)
			devices.append(
				RehauNeasmart2BinarySensorForLiveDido(
					controller, live_dido, "DO_5", "Digital Output 5", entity_description
				)
			)
			devices.append(
				RehauNeasmart2BinarySensorForLiveDido(
					controller, live_dido, "DI_1", "Digital Input 1", entity_description
				)
			)
			devices.append(
				RehauNeasmart2BinarySensorForLiveDido(
					controller, live_dido, "DI_2", "Digital Input 2", entity_description
				)
			)
			devices.append(
				RehauNeasmart2BinarySensorForLiveDido(
					controller, live_dido, "DI_3", "Digital Input 3", entity_description
				)
			)
			devices.append(
				RehauNeasmart2BinarySensorForLiveDido(
					controller, live_dido, "DI_4", "Digital Input 4", entity_description
				)
			)
			devices.append(
				RehauNeasmart2BinarySensorForLiveDido(
					controller, live_dido, "DI_5", "Digital Input 5", entity_description
				)
			)
	async_add_entities(devices)


class RehauNeasmart2BinarySensorForLiveEmu(BinarySensorEntity):

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
		live_emu = self._controller.get_live_emu_by_unique(self._installation_unique)
		return live_emu.get(self._propertyname)

class RehauNeasmart2BinarySensorForLiveDido(BinarySensorEntity):

	def __init__(self, controller: Controller, live_dido: dict, propertyname: str, name: str, entity_description: SensorEntityDescription):
		self._live_dido = live_dido
		self._controller = controller
		self._available = True
		self._name = f"{name}"
		self._propertyname = propertyname
		self._installation_unique = live_dido["unique"]
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
		live_dido = self._controller.get_live_dido_by_unique(self._installation_unique)
		return live_dido.get(self._propertyname)