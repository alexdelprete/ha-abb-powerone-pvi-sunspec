# ha-abb-powerone-pvi-sunspec

[![GitHub Release][releases-shield]][releases]
[![BuyMeCoffee][buymecoffee-shield]][buymecoffee]
[![Community Forum][forum-shield]][forum]

**This project is not endorsed by, directly affiliated with, maintained, authorized, or sponsored by ABB or FIMER**

# Introduction

HA Custom Component to integrate data from ABB/Power-One/FIMER PV mono-phase and three-phase inverters that support SunSpec Modbus Models M1/M103/M160, natively or through the VSN300/VSN700 wifi logger card. The VSN300/VSN700 cards provide a SunSpec to Aurora protocol adapter so that all modbus commands are translated to the proprietary Aurora protocol.

The component has been originally developed by @binsentsu for SolarEdge inverters, I adapted it, adding some features, rewriting all the registers' mapping, for my Power-One Aurora PVI-10.0-OUTD 3-phase inverter to which I added a VSN300 card. It has also been tested with an ABB TRIO-8.5-TL-OUTD-S through a VSN300 and REACT2-3.6-TL through a VSN700 datalogger.

Register address map has been implemented following the vendor's specification documentation, available in the [doc](https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/tree/master/doc) folder.


### Features

- Installation/Configuration through Config Flow UI
- Separate sensor per register
- Configurable TCP modbus port, also at runtime (no restart needed)
- Configurable modbus slave address, also at runtime (no restart needed)
- Configurable register map base address, also at runtime (no restart needed)
- Configurable polling interval, also at runtime (no restart needed)
- Supports SunSpec models M1, M103, M160

# Installation through HACS

This integration is available in [HACS][hacs] official repository. Click this button to open HA directly on the integration page so you can easily install it:

[![Quick installation link](https://my.home-assistant.io/badges/hacs_repository.svg)][my-hacs]

1. Either click the button above, or navigate to HACS in Home Assistant and:
   - 'Explore & Download Repositories'
   - Search for 'ABB Power-One PVI SunSpec'
   - Download
2. Restart Home Assistant
3. Go to Settings > Devices and Services > Add Integration
4. Search for and select 'ABB Power-One PVI SunSpec' (if the integration is not found, do a hard-refresh (ctrl+F5) in the browser)
5. Proceed with the configuration

# Manual Installation

Download the source code archive from the release page. Unpack the archive and copy the contents of custom_components folder to your home-assistant config/custom_components folder. Restart Home Assistant, and then the integration can be added and configured through the native integration setup UI. If you don't see it in the native integrations list, press ctrl-F5 to refresh the browser while you're on that page and retry.

# Enabling Modbus TCP on the inverter

Enable Modbus TCP client on the VSN300, take note of the Unit ID (aka Slave ID) of the inverter (depends on the model, default on some models is 2 on others is 247) and during the configuration of the component, use the appropriate Slave address. Another important parameter is the registers map base address, default is 40000 but it may vary. All these parameters can be reconfigured after installation, clicking CONFIGURE on the integration.

# Configuration

Configuration is done via config flow right after adding the integration. After the first configuration you can change parameters (except custom name and ip/hostname) at runtime through the integration page configuration, without the need to restart HA (this works since v2.5.0). 

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

[![BuyMeCoffee][buymecoffee-shield]][buymecoffee]

---

[buymecoffee]: https://www.buymeacoffee.com/alexdelprete
[buymecoffee-shield]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-green?style=for-the-badge
[hacs]: https://hacs.xyz
[my-hacs]: https://my.home-assistant.io/redirect/hacs_repository/?owner=alexdelprete&repository=ha-abb-powerone-pvi-sunspec&category=integration
[forum-shield]: https://img.shields.io/badge/community-forum-darkred?style=for-the-badge
[forum]: https://community.home-assistant.io/t/custom-component-abb-power-one-fimer-pv-inverters-sunspec-modbus-tcp/316363?u=alexdelprete
[releases-shield]: https://img.shields.io/github/v/release/alexdelprete/ha-abb-powerone-pvi-sunspec?style=for-the-badge&color=darkgreen
[releases]: https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/releases
