# wpt-devkit-v0.1 SCPI Command Set
Hardware tool and Arduino library for developing wireless power applications.

## Command reference
[SCPI command reference](./docs/SCPI.md)

## Arduino IDE
### Installation
Add `wpt-io-arduino.zip` in release.
- Sketch -> Include Library -> Add .ZIP Library

### Dependencies
**Manual ZIP install**
- [bschulz1701/PAC1720_Library](https://github.com/bschulz1701/PAC1720_Library)

**Arduino Library Manager**
- [WifWaf/MCP45HVX1](https://github.com/WifWaf/MCP45HVX1)

### Update
You need to manually uninstall to update. We plan to add this to Arduino Library Manager to automate this in the future.

## Examples
See [Examples](./firmware/wpt-io-arduino/examples) for example Arduino sketches