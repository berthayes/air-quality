# air-quality

This IoT project uses [Circuitpython](https://circuitpython.org) to read Carbon Dioxide in parts per million (CO2 ppm) and Total Volatile Organic Compounds in parts per billion (TVOC ppb), send them to the Cloud over an HTTP POST and show the readings on a display. 

The code was developed for and tested on an [Adafruit ESP32-S3 Reverse TFT Feather](https://www.adafruit.com/product/5691) with an [Adafruit SGP30 Air Quality Sensor Breakout](https://www.adafruit.com/product/3709). A calibration script is included to calibrate the sensor.

### Setup
Start with [installing Micropython](https://circuitpython.org/board/adafruit_feather_esp32s3_reverse_tft/) on the board. 

### Calibration
You've got to calibrate these SGP30s or else ~~they'll rust up on ya~~ you won't get accurate readings.
