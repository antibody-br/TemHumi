

🔧 Arduino Wiring:

Typical Nokia 5110 LCD Connections:


```bash
LCD Pin     Arduino Uno
→ RST    →    Pin 6 
→ CE     →    Pin 7 
→ DC     →    Pin 5 → DIN    →    Pin 4 (MOSI - SPI data)
→ CLK    →    Pin 3 (SCK - SPI clock)
VCC    →    3.3V (NOT 5V for Nokia 5110!)
→ LIGHT  →    Pin 8 (or 3.3V for always on)
GND    →    GND
```

```bash

### #define RST_PIN   6
### #define CE_PIN    7
### #define DC_PIN    5
### #define DIN_PIN   4
### #define CLK_PIN   3
### #define LIGHT_PIN 8

``` 
