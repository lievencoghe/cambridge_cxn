"""
Support for interface with a Cambridge Audio CXN media player.

For more details about this platform, please refer to the documentation at
https://github.com/lievencoghe/cambridge_cxn
"""

import json
import logging
import urllib.request
import voluptuous as vol
import homeassistant.util.dt as dt_util

from homeassistant.components.media_player import MediaPlayerEntity, PLATFORM_SCHEMA

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
    SUPPORT_SHUFFLE_SET,
    SUPPORT_REPEAT_SET,
    SUPPORT_SEEK
)

from homeassistant.const import CONF_HOST, CONF_NAME, STATE_OFF, STATE_ON, STATE_PAUSED, STATE_PLAYING, STATE_IDLE, STATE_STANDBY
import homeassistant.helpers.config_validation as cv

__version__ = "0.6"

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
    | SUPPORT_VOLUME_STEP
    | SUPPORT_SHUFFLE_SET
    | SUPPORT_REPEAT_SET
    | SUPPORT_SEEK
)

SUPPORT_CXN_PREAMP = (
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
    | SUPPORT_SHUFFLE_SET
    | SUPPORT_REPEAT_SET
    | SUPPORT_SEEK
)

DEFAULT_NAME = "Cambridge Audio CXN"
DEVICE_CLASS = "receiver"

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


class CambridgeCXNDevice(MediaPlayerEntity):
    def __init__(self, host, name):
        _LOGGER.info("Setting up Cambridge CXN")
        self._host = host
        self._max_volume = 100
        self._mediasource = ""
        self._min_volume = 0
        self._muted = False
        self._name = name
        self._pwstate = "NETWORK"
        self._should_setup_sources = True
        self._source_list = {}
        self._source_list_reverse = {}
        self._state = STATE_OFF
        self._volume = 0
        self._artwork_url = None
        self._preamp_mode = False
        self._shuffle_mode = "off"
        self._repeat_mode = "off"
        self._media_title = None
        self._media_artist = None
        self._media_album_name = None
        self._media_duration = None
        self._media_position = None
        self._media_position_updated_at = None
        _LOGGER.debug( "Set up Cambridge CXN with IP: %s", host)

    def _setup_sources(self):
        if self._should_setup_sources:
            _LOGGER.debug("Setting up CXN sources")
            sources = json.loads(self._command("/smoip/system/sources"))["data"]
            sources2 = sources.get("sources")
            self._source_list = {}
            self._source_list_reverse = {}

            for i in sources2:
                _LOGGER.debug("Setting up CXN sources... %s", i["id"])
                source = i["id"]
                configured_name = i["name"]
                self._source_list[source] = configured_name
                self._source_list_reverse[configured_name] = source

            presets = json.loads(self._command("/smoip/presets/list"))["data"]
            presets2 = presets.get("presets")
            for i in presets2:
                _LOGGER.debug("Setting up CXN sources... %s", i["id"])
                source = str(i["id"])
                configured_name = i["name"]
                self._source_list[source] = configured_name
                self._source_list_reverse[configured_name] = source

        self._should_setup_sources = False

    def set_shuffle(self, shuffle):
        action = "off"
        if shuffle:
            action = "all"

        self._command("/smoip/zone/play_control?mode_shuffle=" + action)

    def set_repeat(self, repeat):
        adjrepeat = repeat
        if repeat == "one":
            adjrepeat = "toggle"

        self._command("/smoip/zone/play_control?mode_repeat=" + adjrepeat)

    def media_play_pause(self):
        self._command("/smoip/zone/play_control?action=toggle")

    def media_pause(self):
        self._command("/smoip/zone/play_control?action=pause")

    def media_stop(self):
        self._command("/smoip/zone/play_control?action=stop")

    def media_play(self):
        if self.state == STATE_PAUSED:
            self.media_play_pause()

    def media_next_track(self):
        self._command("/smoip/zone/play_control?skip_track=1")

    def media_previous_track(self):
        self._command("/smoip/zone/play_control?skip_track=-1")

    def update(self):
        powerstate = self._getPowerState()
        self._pwstate = powerstate["data"]["power"]

        zonestate = self._getZoneState()
        zonestatedata = zonestate["data"]

        self._preamp_mode = zonestatedata["pre_amp_mode"]
        self._mediasource = zonestatedata["source"]

        if self._preamp_mode:
            self._muted = zonestatedata["mute"]
            self._volume = zonestatedata["volume_percent"] / 100
        else:
            self._muted = False
            self._volume = None

        playstate = self._getPlayState()
        playstatedata = playstate["data"]
        self._state = playstatedata["state"]

        try:
            playstatemetadata = playstatedata["metadata"]
            self._media_position_updated_at = dt_util.utcnow()
        except:
            self._media_artist = None
            self._media_title = None
            self._artwork_url = None
            self._media_album_name = None
            self._media_duration = None
            self._media_position = None
        try:
            self._media_title = playstatemetadata["title"]
        except:
            self._media_title = None
        try:
            self._media_artist = playstatemetadata["artist"]
        except:
            self._media_artist = None
        try:
            self._artwork_url = playstatemetadata["art_url"]
        except:
            self._artwork_url = None
        try:
            self._media_album_name = playstatemetadata["album"]
        except:
            self._media_album_name = None
        try:
            self._media_duration = playstatemetadata["duration"]
            self._media_position = playstatedata["position"]
        except:
            self._media_duration = None
            self._media_position = None
        try:
            self._shuffle_mode = playstatedata["mode_shuffle"]
            self._repeat_mode = playstatedata["mode_repeat"]
        except:
            self._shuffle_mode = "off"
            self._repeat_mode = "off"

        self._setup_sources()

    def _getZoneState(self):
        return json.loads(self._command("/smoip/zone/state"))

    def _getPlayState(self):
        return json.loads(self._command("/smoip/zone/play_state"))


    def _getPowerState(self):
        return json.loads(self._command("/smoip/system/power"))

    def _command(self, command):
        _LOGGER.debug("Sending command: %s", command)
        return urllib.request.urlopen("http://" + self._host + command).read()

    @property
    def is_volume_muted(self):
        return self._muted

    @property
    def name(self):
        return self._name

    @property
    def source_list(self):
        return sorted(list(self._source_list.values()))

    @property
    def state(self):
        _LOGGER.debug("PWSTATE: %s", self._pwstate)
        _LOGGER.debug("STATE: %s", self._state)
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
        if self._preamp_mode:
            return SUPPORT_CXN_PREAMP
        return SUPPORT_CXN

    @property
    def media_duration(self):
        return self._media_duration

    @property
    def media_position(self):
        return self._media_position

    @property
    def media_position_updated_at(self):
        return self._media_position_updated_at

    @property
    def media_album_name(self):
        return self._media_album_name

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
        self._command("/smoip/zone/state?mute=" + ("true" if mute else "false"))

    @property
    def source(self):
        return self._source_list[self._mediasource]

    @property
    def device_class(self):
        return DEVICE_CLASS

    @property
    def shuffle(self):
        return (self._shuffle_mode != "off")

    @property
    def repeat(self):
        return self._repeat_mode

    def mute_volume(self, mute):
        self._command("/smoip/zone/state?mute=" + ("true" if mute else "false"))

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
            self._command("/smoip/zone/state?source=" + reverse_source)
        else:
            self._command("/smoip/zone/recall_preset?preset=" + reverse_source)

    def set_volume_level(self, volume):
        vol_str = "/smoip/zone/state?volume_percent=" + str(int(volume * 100))
        self._command(vol_str)

    def media_seek(self, position):
        pos_str = "/smoip/zone/play_control?position=" + str(int(position))
        self._command(pos_str)

    def turn_on(self):
        self._command("/smoip/system/power?power=ON")

    def turn_off(self):
        self._command("/smoip/system/power?power=NETWORK")

    def volume_up(self):
        self._command("/smoip/zone/state?volume_step_change=+1")

    def volume_down(self):
        self._command("/smoip/zone/state?volume_step_change=-1")
