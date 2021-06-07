[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

# home-assistant-abb-sunspec-modbus
Home Assistant Custom Component to integrate data from ABB/Power-One/FIMER PV 3-phase Inverters with support for SunSpec Modbus TCP (Sunspec M103 and M160), native or through the VSN300 wifi logger card, that provides a SunSpec to Aurora protocol adapter so that all modbus commands are translated to the proprietary Aurora protocol.

The component has been originally developed by @binsentsu for SolarEdge inverters, I adapted it for my Power-One Aurora PVI-10.0-OUTD 3-phase inverter to which I added a VSN300 card. It has not been tested on other models.

Registers' address map has been implemented following the vendor's specification document: https://github.com/alexdelprete/home-assistant-abb-sunspec-modbus/raw/master/ABB_SunSpec_Modbus.xlsx

# Installation
Copy contents of custom_components folder to your home-assistant config/custom_components folder or install it through HACS, adding this as a custom repository: https://github.com/alexdelprete/home-assistant-abb-sunspec-modbus/

Restart Home Assistant, and then the integration can be configured through the native integration setup UI.

# Enabling Modbus TCP on the Inverter
Enable Modbus TCP client on the inverter or the VSN300, take note of the Unit ID (aka Slave ID) of the inverter (depends on the model, default on some models is 2 on others is 254, you can get it from the inverter if you don't want to go through trial/error process.
