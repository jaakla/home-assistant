"""AirPatrol unofficial Python API"""
import sys, pickle, datetime, requests, urllib, json
from datetime import timedelta
from datetime import datetime
import logging

#logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

class AirPatrol():
    def __init__(self, username, password, scan_interval = timedelta(seconds=60), logger = logging):

        self._username = username
        self._password = password
        self._scan_interval = scan_interval
        self._LOGGER = logger

        self._devices = []
        self._updated = None
        self._params = None  # params resp
        self._diagnostic = None
        self._zones = None
        self._tempsensors = None

        self._session = None # login resp

        self.SESSION_FILE = '/tmp/session_cache'
        self.LOGIN_URL = 'https://smartheat.airpatrol.eu/'

        self._params = self.cached_login(self._username,self._password)

# Higher level object getters
    def get_cid(self):
        return self._session["cid"]

# AirPatrol API Update methods:
    def update_all(self):
        if self._updated is None or (datetime.now() > (self._updated + self._scan_interval)):
             self._LOGGER.info("time to update all")
             self._params = self.update_params()
             self._diagnostic = self.update_diagnostic()
             self._zones = self.update_zones()
             self._tempsensors = self.update_sensors()
             self._updated = datetime.now()
             self._LOGGER.debug("updated all")
        else:
             self._LOGGER.debug("no need to update yet")

    def get_params(self):
        self._LOGGER.debug("get_params")
        if self._params is None:
            return self.update_params()

        self._LOGGER.debug("cached params returned")
        return self._params

    def get_diagnostic(self):
        if self._diagnostic is None:
            return self.update_diagnostic()
        return self._diagnostic

    def get_zones(self):
        if self._zones is None:
            return self.update_zones()
        return self._zones

    def get_tempsensors(self):
        if self._tempsensors is None:
            return self.update_sensors
        return self._tempsensors


### Transport methods:

    def update_params(self):
        self._LOGGER.debug("update_params start with session " + str(self._session))
        url = 'https://smartheat.airpatrol.eu/api/controllers/' + self._session['cid'] + '/params'
        self._LOGGER.debug("url "+url)
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
        self._LOGGER.debug("update_params head "+str(self._session))
        r = requests.post(url, headers=self._session, json=req_details)
        self._params = r.json()
        self._LOGGER.debug("update_params end")
        return self._params

    def update_diagnostic(self):
        url = 'https://smartheat.airpatrol.eu/api/controllers/'+self._session['cid']+'/diagnostic'
        r = requests.get(url, headers=self._session)
        return r.json()

    def update_zones(self):
        url = 'https://smartheat.airpatrol.eu/api/controllers/'+self._session['cid']+'/zones'
        r = requests.get(url, headers=self._session)
        return r.json()

    def update_sensors(self):
        url = 'https://smartheat.airpatrol.eu/api/controllers/'+self._session['cid']+'/temperature-sensors'
        r = requests.get(url, headers=self._session)
        return r.json()

    def cached_login(self, username, password):
        try:
            self._LOGGER.debug ('checking '+self.SESSION_FILE)
            with open(self.SESSION_FILE, 'rb') as fp:
                self._LOGGER.debug ('reading '+self.SESSION_FILE)
                self._session = pickle.load(fp)

            # maybe previous session works?
            self._LOGGER.debug ('update params')
            params = self.update_params()
            self._LOGGER.debug ('using cached session with params='+str(params))

        except:
            self._LOGGER.debug ('exception: '+str(sys.exc_info()[0]))
            params = None

        if params is None:
            # try to login for new session
            self._LOGGER.debug ('try login')
            (session_details, headers) = self.do_login(username, password)
            if session_details is None:
                # login failed, exit
                self._LOGGER.error ('login error')
                sys.exit(1)
            else:
                # login ok, save headers for next time
                self._LOGGER.debug(json.dumps(session_details, indent=4, sort_keys=True))
                with open(self.SESSION_FILE, 'wb') as fp:
                    pickle.dump(headers, fp)
        else:
            self._LOGGER.debug(json.dumps(params, indent=4, sort_keys=True))

        return params

    def do_login(self, username, password):

        self._LOGGER.debug("Login with "+username+" "+password)
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
        self._LOGGER.debug("login with headers " + str(headers))

        r = requests.post('https://smartheat.airpatrol.eu/api/login', headers=headers, json=app_details)
        if r.status_code != 200:
            self._LOGGER.error("login error returned "+str(r.status_code))
            return None

        # save controller id with headers as high-level cached session var
        headers['cid'] = r.json()['user']['controllers'][0]['CID']

        return (r.json(),headers)