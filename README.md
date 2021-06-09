[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

# ha-abb-powerone-pvi-sunspec
Home Assistant Custom Component to integrate data from ABB/Power-One/FIMER PV Inverters that support SunSpec Modbus (Sunspec M103 and M160), natively or through the VSN300 wifi logger card. The VSN300 provides a SunSpec to Aurora protocol adapter so that all modbus commands are translated to the proprietary Aurora protocol.

The component has been originally developed by @binsentsu for SolarEdge inverters, I adapted it for my Power-One Aurora PVI-10.0-OUTD 3-phase inverter to which I added a VSN300 card. It has also been tested with an ABB TRIO-8.5-TL-OUTD-S through a VSN300.

Register address map has been implemented following the vendor's specification document: https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/raw/master/VSN300_SunSpec_register_map.xlsx

# Installation through HACS
Install it through HACS adding this as a custom repository: https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/

# Manual Installation
Copy contents of custom_components folder to your home-assistant config/custom_components folder. Restart Home Assistant, and then the integration can be added and configured through the native integration setup UI. If you don't see it in the native integrations list, press ctrl-F5 to refresh the browser while you're on that page and retry.

# Enabling Modbus TCP on the inverter
Enable Modbus TCP client on the VSN300, take note of the Unit ID (aka Slave ID) of the inverter (depends on the model, default on some models is 2 on others is 247).

# Coffee
If you like this integration, I'll gladly accept some quality coffee, but don't feel obliged. :)

<script type="text/javascript" src="https://cdnjs.buymeacoffee.com/1.0.0/button.prod.min.js" data-name="bmc-button" data-slug="alexdelprete" data-color="#FFDD00" data-emoji="☕"  data-font="Bree" data-text="Buy me a coffee" data-outline-color="#000000" data-font-color="#000000" data-coffee-color="#ffffff" ></script>
