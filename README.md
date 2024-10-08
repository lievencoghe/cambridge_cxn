## Changes in this fork

- Speaker select. Soundmodes are used in Home Assistant for this.
- More idle states
- Can be added through HACS

The '.1' at the end of the version number denotes that I've added the above changes to whichever version lievencoghe has released.

# Original readme by lievencoghe

Custom component for Home Assistant that integrates the Cambridge Audio CXN/CXNv2 network media player.
This integration will add a new Media Player entity to your Home Assistant installation.

Create a directory called `cambridge_cxn` under the `custom_components` directory, and save the files from this repo in there.

Enable the component by adding following to `configuration.yaml`

```
media_player:
  - platform: cambridge_cxn
    host: 192.168.123.51
    name: Cambridge CXN
```
