# air-quality
![air-quality display](./images/air_monitor.jpg)
This IoT project uses [Circuitpython](https://circuitpython.org) to read Carbon Dioxide in parts per million (CO2 ppm) and Total Volatile Organic Compounds in parts per billion (TVOC ppb), send them to the Cloud over an HTTP POST and then show the readings on a display. 

The code was developed for and tested on an [Adafruit ESP32-S3 Reverse TFT Feather](https://www.adafruit.com/product/5691) with an [Adafruit SGP30 Air Quality Sensor Breakout](https://www.adafruit.com/product/3709). A calibration script is included to calibrate the sensor.

### Setup
Start with [installing Micropython](https://circuitpython.org/board/adafruit_feather_esp32s3_reverse_tft/) on the board. This will allow the board to act like a removable drive with a small filesystem. 

Download or clone this repository and copy its contents of the board.
```
cp -av air-quality/* /Volumes/CIRCUITPYTHON/
``` 
Micropython will automatically run the `code.py` file when it starts up. So, to calibrate the device, copy the calibration script to `code.py`.
```
cp calibrate_sgp30_batttery_display.py /Volumes/CIRCUITPY/
```

### Calibration
You've got to calibrate these SGP30s or else ~~they'll rust up on ya~~ you won't get accurate readings.
See page 12 from the [Adafruit Guide](https://cdn-learn.adafruit.com/downloads/pdf/adafruit-sgp30-gas-tvoc-eco2-mox-sensor.pdf) which quotes the manufacturer:
>If no stored baseline is available after initializing the baseline algorithm,
the sensor has to run for 12 hours until the baseline can be stored. This will
ensure an optimal behavior for the next time it starts up. Reading out the
baseline prior should be avoided unless a valid baseline is restored first.
Once the baseline is properly initialized or restored, the current baseline
value should be stored approximately once per hour. While the sensor is
off, baseline values are valid for a maximum of seven days.

TL;DR - if run the calibration script for 12 hours the first time you boot the device, or the first time you run the device after it's been powered off for 7 days or longer.

### Building Device and Case
STL files and parts list are included in the [case/README](./case/README.md) file.

