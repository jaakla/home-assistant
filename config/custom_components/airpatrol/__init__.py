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
    EVENT_HOMEASSISTANT_STOP, CONF_SCAN_INTERVAL,
    CONF_EMAIL, CONF_PASSWORD, CONF_USERNAME,
    HTTP_MOVED_PERMANENTLY, HTTP_BAD_REQUEST,
    HTTP_UNAUTHORIZED, HTTP_NOT_FOUND)

DOMAIN = 'airpatrol'
CONF_DEBUG = 'debug'
_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=timedelta(seconds=60)): cv.time_period,
        vol.Optional(CONF_DEBUG, default=False): cv.boolean
    }, extra=vol.ALLOW_EXTRA),
}, extra=vol.ALLOW_EXTRA)

async def async_setup(hass, config):
    """Setup Airpatrol device."""
    _LOGGER.debug("Create the main object")

    hass.data[DOMAIN] = AirPatrolDevice(hass, config)

    if hass.data[DOMAIN].get_cid():  # make sure login was successful
        hass.helpers.discovery.load_platform('sensor', DOMAIN, {}, config)

    return True

class AirPatrolDevice():
    def __init__(self, hass, config):

        self._hass          = hass
        self._username      = config.get(DOMAIN, {}).get(CONF_USERNAME,'')
        self._password      = config.get(DOMAIN, {}).get(CONF_PASSWORD,'')
        self._scan_interval = config.get(DOMAIN, {}).get(CONF_SCAN_INTERVAL)

        self._sonoff_debug  = config.get(DOMAIN, {}).get(CONF_DEBUG, False)
        self._sonoff_debug_log = []

        self._devices = []
        self._updated = None
        self._params = None  # params resp
        self._session = None # login resp

        self.SESSION_FILE = '/tmp/session_cache'
        self.LOGIN_URL = 'https://smartheat.airpatrol.eu/'

        self._params = self.cached_login(self._username,self._password)

    def get_cid(self):
        return self._session["cid"]

    def cached_login(self, username, password):
        try:
            _LOGGER.debug ('checking '+self.SESSION_FILE)
            with open(self.SESSION_FILE, 'rb') as fp:
                _LOGGER.debug ('reading '+self.SESSION_FILE)
                self._session = pickle.load(fp)

            # maybe previous session works?
            _LOGGER.debug ('update params')
            params = self.update_params()
            _LOGGER.debug ('using cached session with params='+str(params))

        except:
            _LOGGER.debug ('exception: '+str(sys.exc_info()[0]))
            params = None

        if params is None:
            # try to login for new session
            _LOGGER.debug ('try login')
            (session_details, headers) = self.do_login(username, password)
            if session_details is None:
                # login failed, exit
                _LOGGER.error ('login error')
                sys.exit(1)
            else:
                # login ok, save headers for next time
                _LOGGER.debug(json.dumps(session_details, indent=4, sort_keys=True))
                with open(self.SESSION_FILE, 'wb') as fp:
                    pickle.dump(headers, fp)
        else:
            _LOGGER.debug(json.dumps(params, indent=4, sort_keys=True))

        return params

    def do_login(self, username, password):

        _LOGGER.debug("Login with "+username+" "+password)
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml,*/*',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
        }

        response = requests.get(self.LOGIN_URL, headers=headers)

        headers['cookie'] = '; '.join([x.name + '=' + urllib.parse.unquote(x.value) for x in response.cookies])
        headers['content-type'] = 'application/json'
        headers['X-XSRF-TOKEN'] = urllib.parse.unquote(response.cookies['XSRF-TOKEN'])

        app_details = {
            'password' : password,
            'email' : username,
            'remember' : False
        }
        _LOGGER.debug("login with headers " + str(headers))

        r = requests.post('https://smartheat.airpatrol.eu/api/login', headers=headers, json=app_details)
        if r.status_code != 200:
            _LOGGER.error("login error returned "+str(r.status_code))
            return None

        # save controller id with headers as high-level cached session var
        headers['cid'] = r.json()['user']['controllers'][0]['CID']

        return (r.json(),headers)

    def get_params(self):
        _LOGGER.debug("get_params")
        if self._params is None or (self._updated is not None and datetime.now() > (self._updated + self._scan_interval)):
            return self.update_params()

        _LOGGER.debug("cached params returned")
        return self._params

    def update_params(self):
        _LOGGER.debug("update_params start with session " + str(self._session))
        url = 'https://smartheat.airpatrol.eu/api/controllers/' + self._session['cid'] + '/params'
        _LOGGER.debug("url "+url)
        req_details = {"parameters":
            [
                "GlobalEcoActive",
                "WifiRSSI",
                "OutdoorTemp",
                "HeatingWaterInletTemp",
                "HeatingWaterRetTemp",
                "HeatingWaterTempDiff",
                "HeatingWaterFlow",
                "CurrentPowerForHeatingHeatingWater"]
            }
        _LOGGER.debug("update_params head "+str(self._session))
        r = requests.post(url, headers=self._session, json=req_details)
        self._params = r.json()
        self._updated = datetime.now()
        _LOGGER.debug("update_params end")


        return self._params

    def get_diagnostic(self):
        url = 'https://smartheat.airpatrol.eu/api/controllers/'+self._session['cid']+'/diagnostic'
        r = requests.get(url, headers=self._session)
        return r.json()

    def get_zones(self):
        url = 'https://smartheat.airpatrol.eu/api/controllers/'+self._session['cid']+'/zones'
        r = requests.get(url, headers=self._session)
        return r.json()

    def get_sensors(self):
        url = 'https://smartheat.airpatrol.eu/api/controllers/'+self._session['cid']+'/temperature-sensors'
        r = requests.get(url, headers=self._session)
        return r.json()

    def temp_sensor_list(self):
        ap_sensors = self.get_sensors()
        sensors = []
        for sensor in ap_sensors["temperatureSensors"]:
            sensors.append(sensor["name"])
        return sensors

    def zone_list(self):
        ap_zones = self.get_zones()
        zones = []
        for zone in ap_zones["zones"]:
            zones.append(zone["name"])
        return zones

    def parameter_list(self):
        ap_params = self,get_params()
        params = []
        for param in ap_params["Parameters"]:
            params.append(param)
        return params

    def diagnostic_list(self):
        ap_diag = self.get_diagnostic()
        params = []
        for param in ap_diag:
            params.append(param)
        return params


