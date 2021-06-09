## ABB Power-One PVI SunSpec

Home assistant Custom Component to integrate data from ABB Power-One PVI 3-phase Inverters with support for SunSpec Modbus TCP (SunSpec M1, M103 and M160) through the VSN300 wifi logger card.

### Features

- Installation through Config Flow UI
- Separate sensor per register
- Works with Unit ID 2 or 247 (slave address)
- Configurable polling interval
- All modbus registers are read in 1 cycle for data consistency between sensors
- Supports SunSpec models M1, M103, M160

### Configuration

Go to the integrations page in your configuration and click on new integration -> ABB Power-One PVI SunSpec

### Sensors Preview

<img style="border: 5px solid #767676;border-radius: 10px;max-width: 350px;width: 100%;box-sizing: border-box;" src="https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/blob/master/demo.png?raw=true" alt="Demo">
