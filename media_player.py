"""
Support for interface with a Cambridge Audio CXN media player.

For more details about this platform, please refer to the documentation at
https://github.com/lievencoghe/cambridge_cxn
"""

import json
import logging
import urllib.request
import requests
import uuid
import voluptuous as vol

from homeassistant.components.media_player import MediaPlayerDevice, PLATFORM_SCHEMA

from homeassistant.components.media_player.const import (
    SUPPORT_PAUSE,
    SUPPORT_PLAY,
    SUPPORT_STOP,
    SUPPORT_PREVIOUS_TRACK,
    SUPPORT_NEXT_TRACK,
    SUPPORT_SELECT_SOURCE,
    SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON,
    SUPPORT_VOLUME_MUTE,
    SUPPORT_VOLUME_STEP,
    SUPPORT_VOLUME_SET,
)

from homeassistant.const import CONF_HOST, CONF_NAME, STATE_OFF, STATE_ON, STATE_PAUSED, STATE_PLAYING, STATE_IDLE, STATE_STANDBY
import homeassistant.helpers.config_validation as cv

__version__ = "0.1"

_LOGGER = logging.getLogger(__name__)

SUPPORT_CXN = (
    SUPPORT_PAUSE
    | SUPPORT_PLAY
    | SUPPORT_STOP
    | SUPPORT_PREVIOUS_TRACK
    | SUPPORT_NEXT_TRACK
    | SUPPORT_SELECT_SOURCE
    | SUPPORT_TURN_OFF
    | SUPPORT_TURN_ON
    | SUPPORT_VOLUME_MUTE
    | SUPPORT_VOLUME_STEP
    | SUPPORT_VOLUME_SET
)

DEFAULT_NAME = "Cambridge Audio CXN"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)


def setup_platform(hass, config, add_devices, discovery_info=None):
    host = config.get(CONF_HOST)
    name = config.get(CONF_NAME)

    if host is None:
        _LOGGER.error("No Cambridge CXN IP address found in configuration file")
        return

    add_devices([CambridgeCXNDevice(host, name)])


class CambridgeCXNDevice(MediaPlayerDevice):
    def __init__(self, host, name):
        """Initialize the Cambridge CXN."""
        _LOGGER.info("Setting up Cambridge CXN")
        self._host = host
        self._max_volume = 100
        self._mediasource = ""
        self._min_volume = 0
        self._muted = False
        self._name = name
        self._pwstate = "NETWORK"
        self._should_setup_sources = True
        self._source_list = None
        self._source_list_reverse = None
        self._state = STATE_OFF
        self._volume = 0
        self._media_title = None
        self._media_artist = None
        self._artwork_url = None

        _LOGGER.debug(
            "Set up Cambridge CXN with IP: %s", host,
        )

        self.update()

    def _setup_sources(self):
        _LOGGER.debug("Setting up CXN sources")
        sources = json.loads(
            urllib.request.urlopen(
                "http://" + self._host + "/smoip/system/sources"
            ).read()
        )["data"]
        sources2 = sources.get("sources")
        self._source_list = {}
        self._source_list_reverse = {}
        for i in sources2:
            _LOGGER.debug("Setting up CXN sources... %s", i["id"])
            source = i["id"]
            configured_name = i["name"]
            self._source_list[source] = configured_name
            self._source_list_reverse[configured_name] = source

        presets = json.loads(
            urllib.request.urlopen(
                "http://" + self._host + "/smoip/presets/list"
            ).read()
        )["data"]
        presets2 = presets.get("presets")
        for i in presets2:
            _LOGGER.debug("Setting up CXN sources... %s", i["id"])
            source = str(i["id"])
            configured_name = i["name"]
            self._source_list[source] = configured_name
            self._source_list_reverse[configured_name] = source

    def media_play_pause(self):
        self.url_command("smoip/zone/play_control?action=toggle")

    def media_next_track(self):
        self.url_command("smoip/zone/play_control?skip_track=1")

    def media_previous_track(self):
        self.url_command("smoip/zone/play_control?skip_track=-1")

    def update(self):
        self._pwstate = json.loads(
            urllib.request.urlopen(
                "http://" + self._host + "/smoip/system/power"
            ).read()
        )["data"]["power"]
        self._volume = (
            json.loads(
                urllib.request.urlopen(
                    "http://" + self._host + "/smoip/zone/state"
                ).read()
            )["data"]["volume_percent"]
            / 100
        )
        self._mediasource = json.loads(
            urllib.request.urlopen("http://" + self._host + "/smoip/zone/state").read()
        )["data"]["source"]
        self._muted = json.loads(
            urllib.request.urlopen("http://" + self._host + "/smoip/zone/state").read()
        )["data"]["mute"]
        playstate = urllib.request.urlopen("http://" + self._host + "/smoip/zone/play_state").read()
        try:
            self._media_title = json.loads(playstate)["data"]["metadata"]["title"] 
        except:
            self._media_title = None
        try:
            self._media_artist = json.loads(playstate)["data"]["metadata"]["artist"]
        except:
            self._media_artist = None
        try:
            urllib.request.urlretrieve(json.loads(playstate)["data"]["metadata"]["art_url"], "/config/www/cxn-artwork.jpg")
            self._artwork_url = "/local/cxn-artwork.jpg?" + str(uuid.uuid4())
        except:
            self._artwork_url = None
        self._state = json.loads(playstate)["data"]["state"]
        
        if self._should_setup_sources:
            self._setup_sources()
            self._should_setup_sources = False

    def url_command(self, command):
        """Establish a telnet connection and sends `command`."""
        _LOGGER.debug("Sending command: %s", command)
        urllib.request.urlopen("http://" + self._host + "/" + command).read()

    @property
    def is_volume_muted(self):
        return self._muted

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def source(self):
        """Return the preset if source is IR (Internet Radio)."""
        if self._mediasource == "IR":
            presets = json.loads(
                urllib.request.urlopen(
                    "http://" + self._host + "/smoip/presets/list"
                ).read()
            )["data"]
            presets2 = presets.get("presets")
            for i in presets2:
                if i["is_playing"]:
                    return i["name"]
            # if nothing was found, then just return IR anyway
            return self._source_list[self._mediasource]
        else:
            return self._source_list[self._mediasource]

    @property
    def source_list(self):
        return sorted(list(self._source_list.values()))

    @property
    def state(self):
        if self._pwstate == "NETWORK":
            return STATE_OFF
        if self._pwstate == "ON":
            if self._state == "play":
                return STATE_PLAYING
            elif self._state == "pause":
                return STATE_PAUSED
            elif self._state == "stop":
                return STATE_IDLE
            else:
                return STATE_ON
        return None

    @property
    def supported_features(self):
        return SUPPORT_CXN

    @property
    def media_title(self):
        return self._media_title

    @property
    def media_artist(self):
        return self._media_artist

    @property
    def media_image_url(self):
        _LOGGER.debug("CXN Artwork URL: %s", self._artwork_url)
        return self._artwork_url

    @property
    def volume_level(self):
        return self._volume

    def mute_volume(self, mute):
        self.url_command("smoip/zone/state?mute=" + ("true" if mute else "false"))

    def select_source(self, source):
        reverse_source = self._source_list_reverse[source]
        if reverse_source in [
            "AIRPLAY",
            "CAST",
            "IR",
            "MEDIA_PLAYER",
            "SPDIF_COAX",
            "SPDIF_TOSLINK",
            "SPOTIFY",
            "USB_AUDIO",
            "ROON"
        ]:
            self.url_command("smoip/zone/state?source=" + reverse_source)
        else:
            self.url_command("smoip/zone/recall_preset?preset=" + reverse_source)

    def set_volume_level(self, volume):
        vol_str = "smoip/zone/state?volume_percent=" + str(int(volume * 100))
        self.url_command(vol_str)

    def turn_on(self):
        self.url_command("smoip/system/power?power=ON")

    def turn_off(self):
        self.url_command("smoip/system/power?power=NETWORK")

    def volume_up(self):
        self.url_command("smoip/zone/state?volume_step_change=+1")

    def volume_down(self):
        self.url_command("smoip/zone/state?volume_step_change=-1")
