# WN-Smartmeter custom component

## About 

Yet another HomeAssistant component for Smartmeter (Digital Electric Meter Reader) using the Wiener Netze API.

## FAQs
not yet!

## Installation
### HACS
I recommend installing it through [HACS](https://github.com/hacs/integration)

 1. **Installing via HACS**
  - Go to HACS->Integrations
  - Add this repo into your HACS custom repositories
   - Search for wn-smartmeter and Download it
   - Restart your HomeAssistant
   - Go to Settings->Devices & Services
   - Shift reload your browser
   - Click Add Integration
   - Search for wn-smartmeter
   - Type your username, password and the meter reader
2. **Installing Manually**
 - copy the folder wn-smartmeter to <homeassistant\>/config/custom_components/
###
Have fun!
## Debug
for debugging purpose you can enable debug logs in HomeAssistant in the configuration.yaml
```
logger:
  default: warning
  logs:
    custom_components.wn_smartmeter: debug
```

## TODOS
- Add python tests
- Implement multiple meter readers

## License
MIT-License
## Copyright
This integration uses the API of https://www.wienernetze.at/smartmeter

All rights regarding the API are reserved by [Wiener Netze](https://www.wienernetze.at/impressum)

Special thanks to [DarwinsBuddy](https://github.com/DarwinsBuddy)
for his [fork](https://github.com/DarwinsBuddy/WienerNetzeSmartmeter/)

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/jrnas)