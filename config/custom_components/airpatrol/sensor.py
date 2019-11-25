"""Some AirPatrol sensors"""
import logging
from datetime import timedelta

##import airpatrol

from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import Entity

from . import DOMAIN

# from custom_components.airpatrol import DOMAIN as AIRPATROL_DOMAIN, AirPatrolDevice


SCAN_INTERVAL = timedelta(seconds=30)
_LOGGER = logging.getLogger(__name__)

AIRPATROL_SENSORS = {
    "CurrentPowerForHeatingHeatingWater": {"uom": "W", "icon": "mdi:flash-outline"},
    "HeatingWaterFlow": {"uom": "m³/h", "icon": "mdi:swap-vertical-circle-outline"},
    "WifiRSSI": {"uom": "dB", "icon": "mdi:antenna"},
}


def setup_platform(hass, config, add_entities, discovery_info=None):
    # We only want this platform to be set up via discovery.
    if discovery_info is None:
        return

    _LOGGER.debug("setup_platform hass:" + str(hass))
    entities = []
    # load all device parameters, add as entities
    params = hass.data[DOMAIN].get_params()
    device = hass.data[DOMAIN]

    for param, value in params["Parameters"].items():
        if value.isnumeric():
            v = float(value)
        else:
            v = value
        _LOGGER.debug("adding sensor " + param)
        sensor = AirPatrolSensor(device, param, v)
        _LOGGER.debug("added sensor " + param)
        entities.append(sensor)

    add_entities(entities)


class AirPatrolSensor(Entity):
    """Single sensor entity"""

    def __init__(self, device, name, value):
        """Init with initial sensor name and value"""
        _LOGGER.debug("initing sensor " + name)
        self._state = value
        self._name = name
        self._device = device

    @property
    def state(self):
        """Return the state/value of the sensor."""
        return self._state

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unit_of_measurement(self):
        # if Temp in name, temperature
        if "Temp" in self._name:
            return TEMP_CELSIUS
        else:
            if self._name in AIRPATROL_SENSORS:
                return AIRPATROL_SENSORS[self._name]["uom"]
        return ""

    @property
    def icon(self):
        if "Temp" in self._name:
            return "mdi:thermometer"
        else:
            if self._name in AIRPATROL_SENSORS:
                return AIRPATROL_SENSORS[self._name]["icon"]

        return ""

    def update(self):
        # TODO: do http update in platform level, not for every sensor
        _LOGGER.debug("updating sensor " + self._name)
        params = self._device.get_params()
        _LOGGER.debug("got params " + str(params))
        for param, value in params["Parameters"].items():
            if param == self._name:
                if value.isnumeric():
                    v = float(value)
                else:
                    v = value
                self._state = v
        _LOGGER.debug("updated state is " + self._state)
