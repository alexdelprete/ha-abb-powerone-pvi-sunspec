[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

<a href="https://www.buymeacoffee.com/alexdelprete" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/black_img.png" alt="Buy Me A Coffee" style="height: auto !important;width: auto !important;" ></a><br>

# ha-abb-powerone-pvi-sunspec
Home Assistant Custom Component to integrate data from ABB/Power-One/FIMER PV 3-phase Inverters with support for SunSpec Modbus TCP (Sunspec M103 and M160), natively or through the VSN300 wifi logger card, that provides a SunSpec to Aurora protocol adapter so that all modbus commands are translated to the proprietary Aurora protocol.

The component has been originally developed by @binsentsu for SolarEdge inverters, I adapted it for my Power-One Aurora PVI-10.0-OUTD 3-phase inverter to which I added a VSN300 card. It has not been tested on other models.

Register address map has been implemented following the vendor's specification document: https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/raw/master/VSN300_SunSpec_register_map.xlsx

# Installation
Copy contents of custom_components folder to your home-assistant config/custom_components folder or install it through HACS, adding this as a custom repository: https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/

Restart Home Assistant, and then the integration can be configured through the native integration setup UI.

# Enabling Modbus TCP on the inverter
Enable Modbus TCP client on the inverter or the VSN300, take note of the Unit ID (aka Slave ID) of the inverter (depends on the model, default on some models is 2 on others is 254, you can get it from the inverter if you don't want to go through trial/error process.
