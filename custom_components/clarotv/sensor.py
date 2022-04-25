import json
import logging
import string
from collections import defaultdict
from datetime import datetime, timedelta

import homeassistant.helpers.config_validation as cv
import pytz
import requests
import voluptuous as vol
from dateutil.relativedelta import relativedelta
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import STATE_UNKNOWN
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from .const import ATTRIBUTION, BASE_URL, CONF_CHANNEL_ID, DOMAIN, NAME_LOGO_CHANNEL_URL

_LOGGER = logging.getLogger(__name__)

ICON = "mdi:television-classic"

SCAN_INTERVAL = timedelta(seconds=60)



PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_CHANNEL_ID): cv.string,
    }
)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the currency sensor"""

    channel_id = config["channel_id"]

    add_entities(
        [ClaroTVSensor(hass, channel_id, SCAN_INTERVAL)],
        True,
    )


class ClaroTVSensor(Entity):
    def __init__(self, hass, channel_id, interval):
        """Inizialize sensor"""
        self._state = STATE_UNKNOWN
        self._hass = hass
        self._interval = interval
        self._channel_id = channel_id
        self._name = ""
        self._programations = {}

    @property
    def name(self):
        """Return the name sensor"""
        return self._name

    @property
    def icon(self):
        """Return the default icon"""
        return ICON

    @property
    def state(self):
        """Return the state of the sensor"""
        return self._current_television_program()

    @property
    def extra_state_attributes(self):
        """Attributes."""
        return {"data": self._programations}

    def update(self):
        """Get the latest update fron the api"""
        self._programations = self._request()
        self._name = self._programations[0].get("line4_default")

    def _current_television_program(self):
        return self._programations[1]["title"]

    def _request(self):
        """Get The request from the api"""
        first_date = datetime.now(pytz.timezone("America/Sao_Paulo"))
        second_date = first_date + relativedelta(months=1)
        programations = []
        url = BASE_URL.format(
            first_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            second_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            self._channel_id,
        )
        channel_dict = {}

        channel_logo_url = NAME_LOGO_CHANNEL_URL.format(self._channel_id)

        retry_strategy = Retry(total=3, status_forcelist=[400, 401, 404, 500, 502, 503, 504], method_whitelist=["GET"])
        adapter = HTTPAdapter(max_retries=retry_strategy)
        http = requests.Session()
        http.mount("https://", adapter)

        logos = http.get(channel_logo_url)

        channel = logos.json().get("response").get("docs")[0]

        channels = http.get(url)

        programations.append(
            {
                "title_default": "$title",
                "line1_default": "",
                "line2_default": "$release",
                "line3_default": "$runtime",
                "line4_default": channel.get("nome"),
                "icon": "mdi:arrow-down-bold",
            }
        )

        for programation in channels.json().get("response").get("docs"):
            programations.append(
                    dict(
                        title=programation["titulo"],
                        poster=channel.get("url_imagem"),
                        fanart=channel.get("url_imagem"),
                        runtime=programation["dh_inicio"].split("T")[1].split("Z")[0],
                        release=programation["dh_inicio"].split("T")[1].split("Z")[0],
                        airdate=programation["dh_inicio"].split("T")[1].split("Z")[0],
                    )
                )
        return programations

