"""Support for the AirPatrol Smartheat controller."""
import logging

import voluptuous as vol

from homeassistant.components.climate import PLATFORM_SCHEMA, ClimateDevice
from homeassistant.components.climate.const import (
    ATTR_PRESET_MODE,
    ATTR_SWING_MODE,
    ATTR_CURRENT_HUMIDITY,
    ATTR_CURRENT_TEMPERATURE,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    ATTR_TARGET_TEMP_STEP,
    ATTR_HVAC_MODE,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    PRESET_AWAY,
    PRESET_NONE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)
from . import DOMAIN


HA_STATE_TO_AIRPATROL = {
    HVAC_MODE_HEAT: "1",
    HVAC_MODE_OFF: "0",
}

AIRPATROL_TO_HA_STATE = {
    "1": HVAC_MODE_HEAT,
    "0": HVAC_MODE_OFF,
}

HA_PRESET_TO_AIRPATROL = {PRESET_AWAY: "on", PRESET_NONE: "off"}

HA_ATTR_TO_AIRPATROL = {
    ATTR_PRESET_MODE: "en_hol",
    ATTR_SWING_MODE: "f_dir",
    ATTR_CURRENT_HUMIDITY: "htemp",
    ATTR_TEMPERATURE: "otemp",
    ATTR_TARGET_TEMP_HIGH: "stemp",
}


def setup_platform(hass, config, add_entities, discovery_info=None):
    # We only want this platform to be set up via discovery.
    _LOGGER.debug("setup_platform ")
    if discovery_info is None:
        _LOGGER.debug("discovery_info is None... ")
        return

    entities = []

    # load all device parameters, add as entities

    hass.data[DOMAIN].update_all()  # update values

    params = hass.data[DOMAIN].get_params()
    zones = hass.data[DOMAIN].get_zones()
    diagnostic = hass.data[DOMAIN].get_diagnostic()
    tempsensors = hass.data[DOMAIN].get_tempsensors()

    device = hass.data[DOMAIN]
    _LOGGER.debug("adding climate zones... ")
    for zone in zones["zones"]:
        num = zone["ZoneNumber"]
        name = zone["name"]
        zone_parameters = zone["Parameters"]
        _LOGGER.debug("adding zone " + name + " device "+str(device))

        climate_zone = AirPatrolClimateZone(device, name, num, zone_parameters)
        entities.append(climate_zone)

    add_entities(entities)


class AirPatrolClimateZone(ClimateDevice):
    """Representation of a AirPatrol SmartHeat zone."""

    def __init__(self, device, name, zonenumber, parameters):
        """Initialize the climate device."""
        _LOGGER.debug("adding AirPatrolClimateZone " + name)
        self._name = name
        self._zonenumber = zonenumber
        self._parameters = parameters
        self._device = device

        self._supported_features = SUPPORT_TARGET_TEMPERATURE

    async def _set(self, settings):
        """Set device settings using API."""
        # TODO

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._supported_features

    @property
    def name(self):
        """Return the name of the thermostat, if any."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._zonenumber

    @property
    def temperature_unit(self):
        """Return the unit of measurement which this thermostat uses."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        _LOGGER.debug(
            "get current_temperature " + self._name + "=" + self._parameters["RoomTemp"]
        )
        return float(self._parameters["RoomTemp"])

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return float(self._parameters["RoomTempSetpoint"])

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return 1

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        await self._set(kwargs)

    @property
    def hvac_mode(self):
        """Return current operation ie. heat, off."""
        ap_mode = self._parameters["HeatingStatus"]
        return AIRPATROL_TO_HA_STATE.get(ap_mode, HVAC_MODE_HEAT)

    @property
    def hvac_modes(self):
        """Return the list of available operation modes."""
        return list(HA_STATE_TO_AIRPATROL)

    async def async_set_hvac_mode(self, hvac_mode):
        """Set HVAC mode."""
        await self._set({ATTR_HVAC_MODE: hvac_mode})

    @property
    def preset_mode(self):
        """Return the preset_mode."""
        if self._parameters["CurrentOperatingMode"] == "global_eco":
            return PRESET_AWAY
        return PRESET_NONE

    async def async_set_preset_mode(self, preset_mode):
        """Set preset mode."""
        # TOO

    @property
    def preset_modes(self):
        """List of available preset modes."""
        return list(HA_PRESET_TO_AIRPATROL)

    async def async_update(self):
        """Retrieve latest state."""
        #_LOGGER.debug("async_update of " + self._name)
        #await self._device.update_all()

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._name
