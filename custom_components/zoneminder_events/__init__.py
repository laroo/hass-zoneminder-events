"""Support for ZoneMinder Events."""
import logging
from time import sleep

import voluptuous as vol
from zoneminder.zm import ZoneMinder

from homeassistant.const import (
    ATTR_ID,
    ATTR_NAME,
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PATH,
    CONF_SSL,
    CONF_TTL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.discovery import async_load_platform

_LOGGER = logging.getLogger(__name__)

DOMAIN = "zoneminder_events"

CONF_PATH_ZMS = "path_zms"

DEFAULT_PATH = "/zm/"
DEFAULT_PATH_ZMS = "/zm/cgi-bin/nph-zms"
DEFAULT_SSL = False
DEFAULT_TIMEOUT = 10
DEFAULT_VERIFY_SSL = True
DEFAULT_ALARM_TTL = 5

HOST_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_PATH, default=DEFAULT_PATH): cv.string,
        vol.Optional(CONF_PATH_ZMS, default=DEFAULT_PATH_ZMS): cv.string,
        vol.Optional(CONF_SSL, default=DEFAULT_SSL): cv.boolean,
        vol.Optional(CONF_USERNAME): cv.string,
        vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): cv.boolean,
        vol.Optional(CONF_TTL, default=DEFAULT_ALARM_TTL): cv.positive_int,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.All(cv.ensure_list, [HOST_CONFIG_SCHEMA])}, extra=vol.ALLOW_EXTRA
)

SERVICE_TRIGGER_ALARM = "trigger_alarm"
TRIGGER_ALARM_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_NAME): cv.string,
        vol.Required(ATTR_ID): cv.positive_int,
    }
)

STATE_URL_ALARM_STATUS = "api/monitors/alarm/id:{}/command:status.json"
STATE_URL_ALARM_ON = "api/monitors/alarm/id:{}/command:on.json"
STATE_URL_ALARM_OFF = "api/monitors/alarm/id:{}/command:off.json"


async def async_setup(hass, config):
    """Set up the ZoneMinder Events component."""

    if hass.config_entries.async_entries(DOMAIN):
        _LOGGER.info("Already in config")
        return True

    if DOMAIN not in config:
        _LOGGER.info("Domain not in config")
        return True

    hass.data.setdefault(DOMAIN, {})

    success = True

    for conf in config[DOMAIN]:
        zm_name = conf.get(CONF_NAME)
        hass.data[DOMAIN].setdefault(zm_name, {})

        protocol = "https" if conf[CONF_SSL] else "http"
        host_name = conf[CONF_HOST]
        server_origin = f"{protocol}://{host_name}"
        
        _LOGGER.info("ZM conf: %s", server_origin)

        zm_client = ZoneMinder(
            server_origin,
            conf.get(CONF_USERNAME),
            conf.get(CONF_PASSWORD),
            conf.get(CONF_PATH),
            conf.get(CONF_PATH_ZMS),
            conf.get(CONF_VERIFY_SSL),
        )
        _LOGGER.info("ZM client: %s", zm_client)

        hass.data[DOMAIN][zm_name]['client'] = zm_client
        hass.data[DOMAIN][zm_name]['ttl'] = {}
        # success = zm_client.login() and success

    def trigger_alarm(call):
        """Trigger ZoneMinder alarm."""
        zm_name = call.data[ATTR_NAME]
        monitor_id = call.data[ATTR_ID]

        if zm_name not in hass.data[DOMAIN]:
            _LOGGER.error("Invalid ZoneMinder host provided: %s", zm_name)

        _LOGGER.info("ZM trigger_alarm: %s - monitor %s", zm_name, monitor_id)

        if monitor_id not in hass.data[DOMAIN][zm_name]['ttl']:
            hass.data[DOMAIN][zm_name]['ttl'][monitor_id] = None

        zm_client = hass.data[DOMAIN][zm_name]['client']
        zm_client.login()

        def get_alarm_status():
            result = zm_client.get_state(STATE_URL_ALARM_STATUS.format(monitor_id))
            #_LOGGER.info(f"get_alarm_status: '{result}'")
            status = result.get('status')
            _LOGGER.info(f"get_alarm_status: '{status}' ({type(status)})")
            return status

        def set_alarm_on():
            result = zm_client.get_state(STATE_URL_ALARM_ON.format(monitor_id))
            #_LOGGER.info(f"set_alarm_on: '{result}'")
            status = result.get('status')
            _LOGGER.info(f"set_alarm_on: '{status}' ({type(status)})")
            return status

        def set_alarm_off():
            result = zm_client.get_state(STATE_URL_ALARM_OFF.format(monitor_id))
            #_LOGGER.info(f"set_alarm_off: '{result}'")
            status = result.get('status')
            _LOGGER.info(f"set_alarm_off: '{status}' ({type(status)})")
            return status

        try:
            if get_alarm_status() == "0":
                set_alarm_on()
                hass.data[DOMAIN][zm_name]['ttl'][monitor_id] = 5

                while hass.data[DOMAIN][zm_name]['ttl'][monitor_id]:
                    _LOGGER.info(f"Alarm TTL (sec): {hass.data[DOMAIN][zm_name]['ttl'][monitor_id]}")
                    sleep(1)
                    hass.data[DOMAIN][zm_name]['ttl'][monitor_id] -= 1
                
                set_alarm_off()
                
            else:
                _LOGGER.info("Alarm already enabled...")
                hass.data[DOMAIN][zm_name]['ttl'][monitor_id] += 5

        except Exception as e:
            _LOGGER.info(f"Error: {e}")


    if DOMAIN not in hass.services.async_services():
        _LOGGER.debug("Registering service")
        hass.services.async_register(
            DOMAIN,
            SERVICE_TRIGGER_ALARM,
            trigger_alarm,
            schema=TRIGGER_ALARM_SCHEMA,
        )
    else:
        _LOGGER.debug("Service already registered")

    _LOGGER.info("ZM BOOTED")

    return success
