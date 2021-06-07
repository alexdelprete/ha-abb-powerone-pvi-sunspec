[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

# home-assistant-abb-sunspec-modbus
Home assistant Custom Component to integrate data from ABB/Power-One/FIMER PV 3-phase Inverters that support SunSpec Modbus TCP (Sunspec M103 and M160). It also works with old inverters with the VSN300 wifi logger card, that implements a SunSpec to Aurora protocol adapter.

Registers' address map has been implemented following the vendor's specification document: https://github.com/alexdelprete/home-assistant-abb-sunspec-modbus/raw/master/ABB_SunSpec_Modbus.xlsx

# Installation
Copy contents of custom_components folder to your home-assistant config/custom_components folder or install through HACS.
After reboot of Home-Assistant, this integration can be configured through the integration setup UI

# Enabling Modbus TCP on the Inverter
Enable Modbus TCP client on the inverter or the VSN300, take note of the Unit ID (aka Slave ID) of the inverter (depends on the model, default on some models is 2 on others is 254, you can get it from the inverter if you don't want to go through trial/error process.
