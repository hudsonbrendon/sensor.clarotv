"""
A platform that provides information about programation on claro tv.

For more details on this component, refer to the documentation at
https://github.com/hudsonbrendon/sensor.clarotv
"""
import logging
from datetime import datetime, timedelta

import async_timeout
import homeassistant.helpers.config_validation as cv
import pytz
import voluptuous as vol
from dateutil.relativedelta import relativedelta
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.entity import Entity

CONF_CHANNEL_ID = "channel_id"
CONF_CHANNEL_NAME = "channel_name"
CONF_CHANNEL_LOGO = "channel_logo"
SCAN_INTERVAL = timedelta(minutes=10)

ICON = "mdi:video"

BASE_URL = "https://programacao.claro.com.br/gatekeeper/exibicao/select?q=id_cidade:1&wt=json&sort=dh_inicio%20asc&fl=dh_inicio%20st_titulo%20titulo%20id_programa%20id_exibicao&fq=dh_inicio:%5B{}%20TO%20{}%5D&fq=id_canal:{}"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_CHANNEL_ID): cv.string,
        vol.Required(CONF_CHANNEL_NAME): cv.string,
        vol.Required(CONF_CHANNEL_LOGO): cv.string,
    }
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup sensor platform."""
    channel_id = config["channel_id"]
    channel_name = config["channel_name"]
    channel_logo = config["channel_logo"]
    name = channel_name.capitalize()
    session = async_create_clientsession(hass)
    async_add_entities(
        [ClaroTVSensor(channel_id, channel_name, channel_logo, name, session)], True
    )


class ClaroTVSensor(Entity):
    """claro.com.br Sensor class"""

    def __init__(self, channel_id, channel_name, channel_logo, name, session):
        self._state = channel_name
        self._channel_id = channel_id
        self._channel_name = channel_name
        self._channel_logo = channel_logo
        self.session = session
        self._name = name
        self._programations = []

    async def async_update(self):
        """Update sensor."""
        _LOGGER.debug("%s - Running update", self._name)
        try:

            first_date = datetime.now(pytz.timezone("America/Sao_Paulo"))
            second_date = first_date + relativedelta(months=1)
            url = BASE_URL.format(
                first_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                second_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                self._channel_id,
            )
            async with async_timeout.timeout(10, loop=self.hass.loop):
                response = await self.session.get(url)
                programations = await response.json()

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

                for programation in programations.get("response").get("docs"):
                    self._programations.append(
                        dict(
                            title=programation["titulo"],
                            poster=self._channel_logo,
                            fanart=self._channel_logo,
                            runtime=programation["dh_inicio"]
                            .split("T")[1]
                            .split("Z")[0],
                            release=programation["dh_inicio"]
                            .split("T")[1]
                            .split("Z")[0],
                            airdate=programation["dh_inicio"]
                            .split("T")[1]
                            .split("Z")[0],
                        )
                    )

        except Exception as error:
            _LOGGER.debug("%s - Could not update - %s", self._name, error)

    @property
    def name(self):
        """Name."""
        return self._name

    @property
    def state(self):
        """State."""
        return self._state

    @property
    def programations(self):
        """Programations."""
        return [
            i
            for n, i in enumerate(self._programations)
            if i not in self._programations[n + 1 :]
        ]

    @property
    def icon(self):
        """Icon."""
        return ICON

    @property
    def device_state_attributes(self):
        """Attributes."""
        return {
            "data": self._programations,
        }
