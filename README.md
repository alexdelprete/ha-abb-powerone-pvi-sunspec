<a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=alexdelprete&repository=ha-abb-powerone-pvi-sunspec&category=integration" target="_blank"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Open your Home Assistant instance and open a repository inside the Home Assistant Community Store." /></a>
# ha-abb-powerone-pvi-sunspec

HA Custom Component to integrate data from ABB/Power-One/FIMER PV mono-phase and three-phase inverters that support SunSpec Modbus (Sunspec M1, M103, M160), natively or through the VSNx00 wifi logger card. The VSNx00 provides a SunSpec to Aurora protocol adapter so that all modbus commands are translated to the proprietary Aurora protocol.

The component has been originally developed by @binsentsu for SolarEdge inverters, I adapted it, adding some features, rewriting all the registers' mapping, for my Power-One Aurora PVI-10.0-OUTD 3-phase inverter to which I added a VSN300 card. It has also been tested with an ABB TRIO-8.5-TL-OUTD-S through a VSN300 and REACT2-3.6-TL through a VSN700 datalogger.

Register address map has been implemented following the vendor's specification documentation listed here:

- https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/raw/master/doc/SunSpec_VSN300register_map.xlsx
- https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/raw/master/doc/SunSpec_REACT2_PICS_Rev_003.xlsx
- https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/raw/master/doc/SunSpec_PICS-ABB-TRIO-50.0-TL-OUTD.xlsx

# Installation through HACS

This integration is available in HACS official repository. Click this button to open HA directly on the integration page so you can easily install it:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=alexdelprete&repository=ha-abb-powerone-pvi-sunspec&category=integration)

# Manual Installation

Copy contents of custom_components folder to your home-assistant config/custom_components folder. Restart Home Assistant, and then the integration can be added and configured through the native integration setup UI. If you don't see it in the native integrations list, press ctrl-F5 to refresh the browser while you're on that page and retry.

# Enabling Modbus TCP on the inverter

Enable Modbus TCP client on the VSN300, take note of the Unit ID (aka Slave ID) of the inverter (depends on the model, default on some models is 2 on others is 247) and during the configuration of the component, use the appropriate Slave address. Another important parameter is the registers map base address, default is 40000 but it may vary. All these parameters can be reconfigured after installation, clicking CONFIGURE on the integration.

# Configuration Parameters Explained

You can change configuration parameters (except custom name and ip/hostname) at runtime through the integration page configuration.

![](https://user-images.githubusercontent.com/7027842/214734702-bf899013-5e28-47b5-87a7-827e49ca465b.gif)

- **custom name**: custom name for the inverter, that will be used as prefix for sensors created by the component
- **ip/hostname**: IP/hostname of the inverter - this is used as unique_id, if you change it and reinstall you will lose historical data, that's why I advice to use hostname, so you can change IP without losing historical data
- **tcp port**: TCP port of the datalogger
- **slave id**: the unit id of the inverter in the chain: default is 254, if using VS300/VS700 it's usually 2
- **register map base address**: the base address from where the register map starts, usually it's 40000, but for ABB VSN300/VSN700 dataloggers it's 0
- **polling period**: frequency, in seconds, to read the registers and update the sensors

<img style="border: 5px solid #767676;border-radius: 10px;max-width: 350px;width: 40%;box-sizing: border-box;" src="https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/blob/master/gfxfiles/config.png?raw=true" alt="Config">

# Sensor screenshot
<img style="border: 5px solid #767676;border-radius: 10px;max-width: 350px;width: 40%;box-sizing: border-box;" src="https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/blob/master/gfxfiles/demo.png?raw=true" alt="Config">

# Coffee

If you like this integration, I'll gladly accept some quality coffee, but please don't feel obliged. :)

<a href="https://www.buymeacoffee.com/alexdelprete" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/black_img.png" alt="Buy Me A Coffee" style="height: auto !important;width: auto !important;" ></a><br>
