# cambridge_cxn
Custom component for Home Assistant that integrates the Cambridge Audio CXN/CXNv2 network media player.
This integration will add a new Media Player entity to your Home Assistant installation.

Enable the component by adding following to `configuration.yaml`

```
media_player:
  - platform: cambridge_cxn
    host: 192.168.123.51
    name: Cambridge CXN
```
