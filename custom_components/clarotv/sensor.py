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
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    CONF_NAME,
    CONF_RESOURCES,
    STATE_UNKNOWN,
)
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


def get_data(channel_id, channel_name, channel_logo):
    """Get The request from the api"""
    first_date = datetime.now(pytz.timezone("America/Sao_Paulo"))
    second_date = first_date + relativedelta(months=1)
    programations = []
    url = BASE_URL.format(
        first_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        second_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        channel_id,
    )
    response = requests.get(url)
    if response.ok:
        programations.append(
            {
                "title_default": "$title",
                "line1_default": "",
                "line2_default": "$release",
                "line3_default": "$runtime",
                "line4_default": channel_name,
                "icon": "mdi:arrow-down-bold",
            }
        )

        for programation in response.json().get("response").get("docs"):
            programations.append(
                dict(
                    title=programation["titulo"],
                    poster=channel_logo,
                    fanart=channel_logo,
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


class ClaroTVSensor(SensorEntity):
    def __init__(self, hass, name, channel_id, channel_name, channel_logo, interval):
        """Inizialize sensor"""
        self._state = STATE_UNKNOWN
        self._hass = hass
        self.interval = interval
        self._channel_id = channel_id
        self._channel_name = channel_name
        self._channel_logo = channel_logo
        self._name = name

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
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {ATTR_ATTRIBUTION: ATTRIBUTION}

    @property
    def device_state_attributes(self):
        """Attributes."""
        return {"data": Throttle(self.interval)(self.update)}

    def update(self):
        """Get the latest update fron the api"""
        return get_data(self._channel_id, self._channel_name, self._channel_logo)
