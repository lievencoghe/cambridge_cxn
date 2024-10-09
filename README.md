# cambridge_cxn
Custom component for Home Assistant that integrates the Cambridge Audio CXN/CXNv2 network media player.
This integration will add a new Media Player entity to your Home Assistant installation.

Create a directory called `cambridge_cxn` under the `custom_components` directory, and save the files from this repo in there.
Alternatively, you can install this using HACS. Add custom repository lievencoghe/cambridge_cxn 

Enable the component by adding following to `configuration.yaml`

```
media_player:
  - platform: cambridge_cxn
    host: 192.168.123.51
    name: Cambridge CXN
```

Restart HA to enable the custom component. Enjoy!
