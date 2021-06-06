## SOLAREDGE MODBUS TCP

Home assistant Custom Component for reading data from ABB inverter through SunSpec modbus TCP.
Implements Inverter registers from 

### Features

- Installation through Config Flow UI.
- Separate sensor per register
- Configurable Unit ID
- Configurable polling interval
- All modbus registers are read within 1 read cycle for data consistency between sensors.
- Supports reading inverter data and extra MPTT data

### Configuration
Go to the integrations page in your configuration and click on new integration -> SolarEdge Modbus

<img style="border: 5px solid #767676;border-radius: 10px;max-width: 350px;width: 100%;box-sizing: border-box;" src="https://github.com/alexdelprete/home-assistant-abb-sunspec-modbus/blob/master/demo.png?raw=true" alt="Demo">
