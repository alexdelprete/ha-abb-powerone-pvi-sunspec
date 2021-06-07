## ABB SUNSPEC MODBUS

Home assistant Custom Component to integrate data from ABB/Power-One/FIMER PV 3-phase Inverters with support for SunSpec Modbus TCP (Sunspec M103 and M160), native or through the VSN300 wifi logger card.

### Features

- Installation through Config Flow UI.
- Separate sensor per register
- Configurable Unit ID
- Configurable polling interval
- All modbus registers are read in 1 read cycle for data consistency between sensors
- Supports reading inverter data and extra MPTT data

### Configuration
Go to the integrations page in your configuration and click on new integration -> SolarEdge Modbus

<img style="border: 5px solid #767676;border-radius: 10px;max-width: 350px;width: 100%;box-sizing: border-box;" src="https://github.com/alexdelprete/home-assistant-abb-sunspec-modbus/blob/master/demo.png?raw=true" alt="Demo">
