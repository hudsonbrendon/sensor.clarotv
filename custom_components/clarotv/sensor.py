import logging
from datetime import datetime, timedelta

import homeassistant.helpers.config_validation as cv
import pytz
import requests
import voluptuous as vol
from dateutil.relativedelta import relativedelta
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import STATE_UNKNOWN
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

ICON = "mdi:television-classic"

SCAN_INTERVAL = timedelta(seconds=60)

ATTRIBUTION = "Data provided by clarotv api"

DOMAIN = "clarotv"

CONF_CHANNEL_ID = "channel_id"
CONF_CHANNEL_NAME = "channel_name"
CONF_CHANNEL_LOGO = "channel_logo"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_CHANNEL_ID): cv.string,
        vol.Required(CONF_CHANNEL_NAME): cv.string,
        vol.Required(CONF_CHANNEL_LOGO): cv.string,
    }
)

BASE_URL = "https://programacao.claro.com.br/gatekeeper/exibicao/select?q=id_cidade:1&wt=json&sort=dh_inicio%20asc&fl=dh_inicio%20st_titulo%20titulo%20id_programa%20id_exibicao&fq=dh_inicio:%5B{}%20TO%20{}%5D&fq=id_canal:{}"


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the currency sensor"""

    channel_id = config["channel_id"]
    channel_name = config["channel_name"]
    channel_logo = config["channel_logo"]
    name = channel_name.capitalize()

    add_entities(
        [
            ClaroTVSensor(
                hass, name, channel_id, channel_name, channel_logo, SCAN_INTERVAL
            )
        ],
        True,
    )


class ClaroTVSensor(Entity):
    def __init__(self, hass, name, channel_id, channel_name, channel_logo, interval):
        """Inizialize sensor"""
        self._state = STATE_UNKNOWN
        self._hass = hass
        self._interval = interval
        self._channel_id = channel_id
        self._channel_name = channel_name
        self._channel_logo = channel_logo
        self._name = name
        self._programations = []

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
        now = datetime.now(pytz.timezone("America/Sao_Paulo"))
        return now.strftime("%d-%m-%Y %H:%M:%S")

    @property
    def device_state_attributes(self):
        """Attributes."""
        return {"data": self._programations}

    def update(self):
        """Get the latest update fron the api"""
        first_date = datetime.now(pytz.timezone("America/Sao_Paulo"))
        second_date = first_date + relativedelta(months=1)
        url = BASE_URL.format(
            first_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            second_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            self._channel_id,
        )
        response = requests.get(url)
        if response.ok:
            self._programations.append(
                {
                    "title_default": "$title",
                    "line1_default": "",
                    "line2_default": "$release",
                    "line3_default": "$runtime",
                    "line4_default": self._channel_name,
                    "icon": "mdi:arrow-down-bold",
                }
            )

            for programation in response.json().get("response").get("docs"):
                self._programations.append(
                    dict(
                        title=programation["titulo"],
                        poster=self._channel_logo,
                        fanart=self._channel_logo,
                        runtime=programation["dh_inicio"].split("T")[1].split("Z")[0],
                        release=programation["dh_inicio"].split("T")[1].split("Z")[0],
                        airdate=programation["dh_inicio"].split("T")[1].split("Z")[0],
                    )
                )

        else:
            _LOGGER.error("{} Request error".format(self._name))
