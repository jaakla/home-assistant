"""AirPatrol Smartheat Platform integration."""
import sys, json, time, random, pprint, base64, requests, hmac, hashlib, re
import pickle, urllib
import logging, time, hmac, hashlib, random, base64, json, socket, requests, re, threading, hashlib, string
import voluptuous as vol
from datetime import timedelta
from datetime import datetime

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers import discovery
from homeassistant.helpers import config_validation as cv
from homeassistant.const import (
    EVENT_HOMEASSISTANT_STOP,
    CONF_SCAN_INTERVAL,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_USERNAME,
    HTTP_MOVED_PERMANENTLY,
    HTTP_BAD_REQUEST,
    HTTP_UNAUTHORIZED,
    HTTP_NOT_FOUND,
)

from config.custom_components.airpatrol_api import AirPatrol

DOMAIN = "airpatrol"
CONF_DEBUG = "debug"
_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=timedelta(seconds=60)
                ): cv.time_period,
                vol.Optional(CONF_DEBUG, default=False): cv.boolean,
            },
            extra=vol.ALLOW_EXTRA,
        ),
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass, config):
    """Setup Airpatrol device."""
    _LOGGER.debug("Create the main object")

    hass.data[DOMAIN] = AirPatrolDevice(hass, config)

    if hass.data[DOMAIN].get_cid():  # make sure login was successful
        hass.helpers.discovery.load_platform("sensor", DOMAIN, {}, config)

    return True


class AirPatrolDevice:
    """thin HA-specific wrapper for device"""

    def __init__(self, hass, config):

        self._hass = hass
        self._username = config.get(DOMAIN, {}).get(CONF_USERNAME, "")
        self._username = config.get(DOMAIN, {}).get(CONF_PASSWORD, "")
        self._scan_interval = config.get(DOMAIN, {}).get(CONF_SCAN_INTERVAL)

        self._device = AirPatrol(self._username, self._username, self._scan_interval)

    def get_cid(self):
        return self._device.get_cid()

    def update_all(self):
        return self._device.update_all()

    def get_params(self):
        return self._device.get_params()

    def get_diagnostic(self):
        return self._device.get_diagnostic()

    def get_zones(self):
        return self._device.get_zones()

    def get_tempsensors(self):
        return self._device.get_tempsensors()
