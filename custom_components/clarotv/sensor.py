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

from .const import ATTRIBUTION, BASE_URL, CONF_CHANNEL_ID, DOMAIN, NAME_LOGO_CHANNEL_URL

_LOGGER = logging.getLogger(__name__)

ICON = "mdi:television-classic"

SCAN_INTERVAL = timedelta(seconds=60)



PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_CHANNEL_ID): cv.string,
    }
)

def get_data(channel_id):
    """Get The request from the api"""
    first_date = datetime.now(pytz.timezone("America/Sao_Paulo"))
    second_date = first_date + relativedelta(months=1)
    programations = []
    url = BASE_URL.format(
        first_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        second_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        channel_id,
    )
    channel = {}

    response = requests.get(NAME_LOGO_CHANNEL_URL.format(channel_id))

    if response.ok:
        channel = response.json().get("response").get("docs")[0]
    else:
        _LOGGER.error("Cannot perform the request")

    response = requests.get(url)
    if response.ok:
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

        for programation in response.json().get("response").get("docs"):
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
    else:
        _LOGGER.error("Cannot perform the request")
    return programations


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
        self._programations = get_data(self._channel_id)
        self._name = self._programations[0].get("line4_default")

    def _current_television_program(self):
        return self._programations[1]["title"]
