## ABB Power-One PVI SunSpec

HA Custom Component to integrate data from ABB Power-One PVI 3-phase Inverters that support SunSpec Modbus TCP (SunSpec M1, M103 and M160) through the VSN300 wifi logger card.

### Features

- Installation/Configuration through Config Flow UI
- Separate sensor per register
- Configurable inverter Modbus Slave Address
- Configurable polling interval
- All live modbus registers are read in 1 cycle for data consistency between sensors
- Supports SunSpec models M1, M103, M160

### Configuration

Go to the integrations page in your configuration and click on new integration -> ABB Power-One PVI SunSpec

### Sensors Preview

<img style="border: 5px solid #767676;border-radius: 10px;max-width: 350px;width: 100%;box-sizing: border-box;" src="https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/blob/master/extrafiles/demo.png?raw=true" alt="Demo">
