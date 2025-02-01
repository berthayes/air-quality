# The Hardware

## 3D Printed Case
For designing the case for this build, I took some existing designs from the folks at Adafruit and hacked away. The case is based on the [3D Printed Case for Adafruit Feather](https://learn.adafruit.com/3d-printed-case-for-adafruit-feather/cad) by Ruiz Brothers with modifications for the placement of the USB cable and overall length of the case. There is a mounting bracket for the feather and case which is also based on a design by Ruiz Brothers for an [air-quality monitoring project](https://learn.adafruit.com/aqi-case) that also uses this board.

## Parts List

The IoT *thing* itself is pretty straightforward and all of the parts used for this build can be purchased online from [Adafruit](https://adafruit.com). The IoT microcontroller is an ESP32-S3 with a nifty display and the sensor is an SGP30. They talk to each other using the I2C protocol; each one has a JST SH 4-pin connector so no soldering is required if using an Adafruit STEMMA cable (or Sparkfun Qwiic cable, etc.) 

If you're going to use the 3D printed case, you'll want to create a [battery on/off switch](https://learn.adafruit.com/on-slash-off-switches). This *will* require soldering but is pretty easy.



- Adafruit ESP32-S3 Reverse TFT Feather - 4MB Flash, 2MB PSRAM, STEMMA QT
    - https://www.adafruit.com/product/5691
    - ESP32-S3 with built-in 240x135 color TFT display and Qwiic/Stemma (I2C) connector
    - $24.95
- Adafruit SGP30 Air Quality Sensor Breakout - VOC and eCO2 - STEMMA QT / Qwiic
    - https://www.adafruit.com/product/3709
    - You'll want to calibrate this for best results (see sample code)
    - $17.50
- Lithium Ion Polymer Battery - 3.7v 500mAh
    - https://www.adafruit.com/product/1578
    - $7.95
- STEMMA QT / Qwiic JST SH 4-Pin Cable - 200mm Long
    - https://www.adafruit.com/product/4401
    - $1.25
- Black Nylon Machine Screw and Stand-off Set – M2.5 Thread
    - https://www.adafruit.com/product/3299
    - More than you'll need until you buy them again
    - $16.95
- Breadboard-friendly SPDT Slide Switch
    - https://www.adafruit.com/product/805
    - This should fit snugly in the 3d printed case.
    - $0.95

