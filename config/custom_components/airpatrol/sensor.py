"""Some AirPatrol sensors"""
import logging
from datetime import timedelta

##import airpatrol

from homeassistant.const import TEMP_CELSIUS, DEVICE_CLASS_BATTERY, DEVICE_CLASS_HUMIDITY, DEVICE_CLASS_POWER, DEVICE_CLASS_SIGNAL_STRENGTH, DEVICE_CLASS_TEMPERATURE
from homeassistant.helpers.entity import Entity

from . import DOMAIN

# from custom_components.airpatrol import DOMAIN as AIRPATROL_DOMAIN, AirPatrolDevice


_LOGGER = logging.getLogger(__name__)

AIRPATROL_SENSORS = {
    "CurrentPowerForHeatingHeatingWater": {"uom": "W", "icon": "mdi:flash-outline", "class": DEVICE_CLASS_POWER},
    "HeatingWaterFlow": {"uom": "m³/h", "icon": "mdi:swap-vertical-circle-outline", "class": ""},
    "WifiRSSI": {"uom": "dB", "icon": "mdi:antenna", "class": DEVICE_CLASS_SIGNAL_STRENGTH},
}


def setup_platform(hass, config, add_entities, discovery_info=None):
    # We only want this platform to be set up via discovery.
    if discovery_info is None:
        return

    _LOGGER.debug("setup_platform hass:" + str(hass))
    entities = []

    # load all device parameters, add as entities

    hass.data[DOMAIN].update_all()  # update values

    params = hass.data[DOMAIN].get_params()
    zones = hass.data[DOMAIN].get_zones()
    diagnostic = hass.data[DOMAIN].get_diagnostic()
    tempsensors = hass.data[DOMAIN].get_tempsensors()

    device = hass.data[DOMAIN]

    # 1. params data
    for param, value in params["Parameters"].items():
        if value.isnumeric():
            v = float(value)
        else:
            v = value
        _LOGGER.debug("adding sensor " + param)
        sensor = AirPatrolSensor(device, param, v)
        _LOGGER.debug("added sensor " + param)
        entities.append(sensor)

    # 2. temp sensors
    for tempsensor in tempsensors["temperatureSensors"]:
        num = tempsensor["number"]
        name = tempsensor["name"]
        temperature = tempsensor["temperature"]
        if temperature != "NA":
            v = float(temperature)
            _LOGGER.debug("adding tempsensor " + name)
            sensor = AirPatrolSensor(device, name, v)
            _LOGGER.debug("added tempsensor " + name)
            entities.append(sensor)
        else:
            _LOGGER.debug("NA for tempsensor " + name)

    # 3. zones
    for zone in zones["zones"]:
        num = zone["ZoneNumber"]
        name = zone["name"]
        zone_parameters = zone["Parameters"]
        _LOGGER.debug("adding zone " + name)
        for zone_param, value in zone_parameters.items():
            if "HeatingStatus" == zone_param:
                v = True if value == "1" else False
            elif value.isnumeric():
                v = float(value)
            else:
                v = value
            _LOGGER.debug("adding zone_param " + zone_param)
            sensor = AirPatrolSensor(device, name + ": " + zone_param, v)
            _LOGGER.debug("added zone_param " + zone_param)
            entities.append(sensor)

    # 4. diagnostic - something wrong?
    # for param, value in diagnostic.items():
    #    if value.isnumeric():
    #        v = float(value)
    #    else:
    #        v = value
    #    _LOGGER.debug("adding diag " + param)
    #    sensor = AirPatrolSensor(device, param, v)
    #    _LOGGER.debug("added diag " + param)
    #    entities.append(sensor)

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
    def device_class(self):
        """class of device"""
        if "Temp" in self._name:
            return DEVICE_CLASS_TEMPERATURE
        if "Humidity" in self._name:
            return DEVICE_CLASS_HUMIDITY
        if "Battery" in self._name:
            return DEVICE_CLASS_BATTERY
        if "RadioLink" in self._name:
            return DEVICE_CLASS_SIGNAL_STRENGTH
        if self._name in AIRPATROL_SENSORS:
            return AIRPATROL_SENSORS[self._name]["class"]
        return None

    @property
    def unit_of_measurement(self):
        # if Temp in name, temperature
        if "Temp" in self._name:
            return TEMP_CELSIUS
        if "Humidity" in self._name:
            return "%"
        if "Battery" in self._name:
            return "%"
        else:
            if self._name in AIRPATROL_SENSORS:
                return AIRPATROL_SENSORS[self._name]["uom"]
        return ""

    @property
    def icon(self):
        if "Temp" in self._name:
            return "mdi:thermometer"
        elif "Humidity" in self._name:
            return "mdi:water-percent"
        else:
            if self._name in AIRPATROL_SENSORS:
                return AIRPATROL_SENSORS[self._name]["icon"]

        return ""

    def update(self):
        _LOGGER.debug("updating sensor " + self._name)
        self._device.update_all()

        # read latest data for all possible sensors
        params = self._device.get_params()
        zones = self._device.get_zones()
        tempsensors = self._device.get_tempsensors()
        diagnostic = self._device.get_diagnostic()

        # find value from structs
        # 1. params update
        for param, value in params["Parameters"].items():
            if param == self._name:
                if value.isnumeric():
                    v = float(value)
                elif "Active" in param:
                    v = True if value == "1" else False
                else:
                    v = value

        # 2. tempSensors update
        for tempsensor in tempsensors["temperatureSensors"]:
            name = tempsensor["name"]
            if name == self._name:
                temperature = tempsensor["temperature"]
                if temperature != "NA":
                    v = float(temperature)
                else:
                    v = "NA"

        # 3. zone update
        for zone in zones["zones"]:
            name = zone["name"]
            zone_parameters = zone["Parameters"]
            for zone_param, value in zone_parameters.items():
                if name + ": " + zone_param == self._name:
                    if "HeatingStatus" == zone_param:
                        v = True if value == "1" else False
                    elif value.isnumeric():
                        v = float(value)
                    else:
                        v = value

        # 4. diagnostic
        for param, value in diagnostic.items():
            if param == self._name:
                if value.isnumeric():
                    v = float(value)
                else:
                    v = value

        # update value itself
        self._state = v
