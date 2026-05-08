# scpi-bind

SCPI instrument abstraction with property binding built around PyVISA.

## Features
 - Object-oriented SCPI instrument interfaces
 - Property binding for SCPI commands
 - Sub-system interfaces

## Installation

```bash
pip install scpi-bind
```

## Example

```python
from scpibind import Instrument, SCPIProperty

class PowerSupply(Instrument):
    voltage = SCPIProperty("VOLT?")
    current = SCPIProperty("CURR?")

psu = PowerSupply("TCPIP0::192.168.0.10::INSTR")
print(psu.identity)

# Set up multiple properties at the same time
psu.setup(voltage=5, current=0.1)
print(psu.voltage)

# Set up individual properties
psu.current = 0.05
print(psu.current)
```

## License

MIT