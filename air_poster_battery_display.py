# Use CircuitPython https://circuitpython.org/ to:
# read CO2 ppm and TVOC ppb from a sensor, 
# post them to the Cloud, and display them on a screen.
#
# Developed for a Adafruit ESP32-S3 Reverse TFT Feather
# https://www.adafruit.com/product/5691
# with an Adafruit SGP30 Air Quality Sensor Breakout
# https://www.adafruit.com/product/3709

import adafruit_requests
import time
import os
import ssl
import wifi
import socketpool
import microcontroller
import json
import board
import busio
import adafruit_sgp30
import re
import displayio
from adafruit_display_text import label
import terminalio
from adafruit_max1704x import MAX17048
from adafruit_lc709203f import LC709203F, PackSize

# Set display variables
BACKGROUND_COLOR = 0x000000  # BLACK
TEXT1_COLOR = 0x00FF00 # BRIGHT GREEN
TEXT2_COLOR = 0X0095a1 # WTF
TEXT3_COLOR = 0xFFFFFF # White
FONTSCALE = 3

# Make the display context
display = board.DISPLAY
splash = displayio.Group()
display.root_group = splash

# Initialize Battery Monitor
i2c = board.I2C()
while not i2c.try_lock():
    pass
i2c_address_list = i2c.scan()
i2c.unlock()

device = None

if 0x0b in i2c_address_list:
    lc709203 = LC709203F(board.I2C())
    # Update to match the mAh of your battery for more accurate readings.
    # Can be MAH100, MAH200, MAH400, MAH500, MAH1000, MAH2000, MAH3000.
    # Choose the closest match. Include "PackSize." before it, as shown.
    lc709203.pack_size = PackSize.MAH400
    device = lc709203
    print("Battery monitor: LC709203")

elif 0x36 in i2c_address_list:
    max17048 = MAX17048(board.I2C())
    device = max17048
    print("Battery monitor: MAX17048")

else:
    raise Exception("Battery monitor not found.")

# Create library object on our I2C port
if 0x58 in i2c_address_list:
    sgp30 = adafruit_sgp30.Adafruit_SGP30(board.I2C())
    sgp30.iaq_init()
    sensor_id = [hex(i) for i in sgp30.serial]
    short_id = sensor_id[2]
    print("SGP30 serial # ", sensor_id)

# Get WiFi and MAC address to use as a UID
wifi.radio.connect(os.getenv('CIRCUITPY_WIFI_SSID'), os.getenv('CIRCUITPY_WIFI_PASSWORD'))
hexy = [hex(i) for i in wifi.radio.mac_address]
uid = re.sub("0x", "", hexy[3]) + ":" + re.sub("0x", "", hexy[4]) + ":" + re.sub("0x", "", hexy[5])
url = os.getenv('cribl_url')

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

def get_time():
    time_url = "http://worldtimeapi.org/api/ip"
    results={}
    try:
        now = requests.get(time_url)
        print("get_time HTTP status: " + str(now.status_code))
        if now.status_code==200:
            nowdict = now.json()
            epoch = nowdict["unixtime"]
            datetime = nowdict["datetime"]
        else:
            epoch = -1000000
        now.close()
        results["epoch"]=epoch
        results["status_code"]=now.status_code
        results["datetime"]=datetime
        return(results)
    except:
        results["epoch"]=-1000000
        results["status_code"]="FAIL"
    return(results)

def draw_black_background():
    # Draw Black Background
    color_bitmap = displayio.Bitmap(display.width, display.height, 1)
    color_palette = displayio.Palette(1)
    color_palette[0] = BACKGROUND_COLOR
    bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
    splash.append(bg_sprite)    

def make_labels():
    # Make CO2 Label
    co2_text = "CO2: "
    co2_text_area = label.Label(terminalio.FONT, text=co2_text, color=TEXT1_COLOR, base_alignment=True)
    co2_text_width = co2_text_area.bounding_box[2] * FONTSCALE
    co2_text_height = co2_text_area.bounding_box[3] * FONTSCALE
    co2_text_group = displayio.Group(
        scale=FONTSCALE,
        x=10,
        y=co2_text_height
    )
    co2_text_group.append(co2_text_area)
    splash.append(co2_text_group)

    # Make smaller parts per million label
    ppm_text = "ppm"
    ppm_text_area=label.Label(terminalio.FONT, text=ppm_text, color=TEXT2_COLOR, base_alignment=True)
    ppm_text_width = ppm_text_area.bounding_box[2] * 2 # see scale below
    ppm_text_group = displayio.Group(
        scale=2,
        x=display.width - ppm_text_width,
        y=co2_text_height
    )    
    ppm_text_group.append(ppm_text_area)
    splash.append(ppm_text_group)

    # Make TVOC label
    tvoc_text= "TVOC: "
    tvoc_text_area = label.Label(terminalio.FONT, text=tvoc_text, color=TEXT1_COLOR, base_alignment=True)
    tvoc_text_width = tvoc_text_area.bounding_box[2] * FONTSCALE
    tvoc_text_height = tvoc_text_area.bounding_box[3] * FONTSCALE
    tvoc_text_group = displayio.Group(
        scale=FONTSCALE,
        x=10,
        y=co2_text_height + 10 + tvoc_text_height
    ) 
    tvoc_text_group.append(tvoc_text_area)
    splash.append(tvoc_text_group)   
    
    # Make smaller parts per billion label
    ppb_text = "ppb"
    ppb_text_area=label.Label(terminalio.FONT, text=ppb_text, color=TEXT2_COLOR, base_alignment=True)
    ppb_text_width = ppb_text_area.bounding_box[2] * 2 # see scale below
    ppb_text_group = displayio.Group(
        scale=2,
        x=display.width - ppb_text_width,
        y=co2_text_height + 10 + tvoc_text_height
    )
    ppb_text_group.append(ppb_text_area)
    splash.append(ppb_text_group)

    # Make cribl.io label
    cribl_api_text = "cribl.io"
    cribl_api_text_area = label.Label(terminalio.FONT, text=cribl_api_text, color=TEXT2_COLOR, base_alignment=True)
    cribl_api_text_width = cribl_api_text_area.bounding_box[2]
    cribl_api_text_height = cribl_api_text_area.bounding_box[3]
    cribl_api_text_group = displayio.Group(
        scale=1,
        x=display.width  - (cribl_api_text_width),
        y=display.height - int(cribl_api_text_height * 1.5)
    )
    cribl_api_text_group.append(cribl_api_text_area)
    splash.append(cribl_api_text_group)

    # create and share text base/bottom line alignments
    tvoc_base_alignment = co2_text_height + 10 + tvoc_text_height
    co2_base_alignment = co2_text_height
    label_width = tvoc_text_width 
    return(tvoc_base_alignment, co2_base_alignment, label_width)


get_time_dict = get_time()
epoch = get_time_dict["epoch"]
datetime = get_time_dict["datetime"]

tvoc_base, co2_base, label_width = make_labels()

# Make sensor_id label
sensor_id_text = "Sensor ID: " + short_id
sensor_id_text_area = label.Label(terminalio.FONT, text=sensor_id_text, color=TEXT2_COLOR)
sensor_id_text_width = sensor_id_text_area.bounding_box[2]
sensor_id_text_height = sensor_id_text_area.bounding_box[3]
sensor_id_text_group = displayio.Group(
    scale=1,
    x=0,
    y=display.height - int(sensor_id_text_height * 2)
)
sensor_id_text_group.append(sensor_id_text_area)
splash.append(sensor_id_text_group) 

co2_reading_text = "0000"
co2_reading_text_area = label.Label(terminalio.FONT, text=co2_reading_text, color=TEXT3_COLOR, base_alignment=True)
co2_reading_text_group = displayio.Group(
    scale=FONTSCALE,
    x=label_width,
    y=co2_base
)
co2_reading_text_group.append(co2_reading_text_area)
splash.append(co2_reading_text_group)

tvoc_reading_text = "0000"
tvoc_reading_text_area = label.Label(terminalio.FONT, text=tvoc_reading_text, color=TEXT3_COLOR, base_alignment=True)
tvoc_reading_text_group = displayio.Group(
    scale=FONTSCALE,
    x=label_width,
    y=tvoc_base
)
tvoc_reading_text_group.append(tvoc_reading_text_area)
splash.append(tvoc_reading_text_group)

battery_text = "100%"
battery_text_area = label.Label(terminalio.FONT, text=battery_text, color=TEXT3_COLOR)
battery_text_width = battery_text_area.bounding_box[2]
battery_text_height = battery_text_area.bounding_box[3]
battery_text_group = displayio.Group(
    scale=1,
    x=0,
    y=display.height - battery_text_height
)
battery_text_group.append(battery_text_area)
splash.append(battery_text_group)

cribl_api_text = "HTTP 418"
cribl_api_text_area = label.Label(terminalio.FONT, text=cribl_api_text, color=TEXT3_COLOR, base_alignment=True)
cribl_api_text_width = cribl_api_text_area.bounding_box[2]
cribl_api_text_height = cribl_api_text_area.bounding_box[3]
cribl_api_text_group = displayio.Group(
    scale=1,
    x=display.width - cribl_api_text_width,
    y=display.height - int(cribl_api_text_height/2)
)
cribl_api_text_group.append(cribl_api_text_area)
splash.append(cribl_api_text_group)


while True:
    time.sleep(1)
    # Uncomment the line below to have a cool blinking/flashing HTTP status
    #cribl_api_text_area.text="HTTP " 
    message_json = {}
    air_dict={}
    air_dict["CO2"] = sgp30.eCO2
    air_dict["TVOC"] = sgp30.TVOC
    air_dict["baseline_eCO2"] = sgp30.baseline_eCO2
    air_dict["baseline_TVOC"] = sgp30.baseline_TVOC
    air_dict["sensor_id"] = short_id    
    message_json["data"] = air_dict
    message_json["full_sensor_id"] = sensor_id    
    message_json["boot"] = epoch
    message_json["board_id"] = uid
    air_json = json.dumps(message_json)
    posty = requests.post(url, data=air_json)
    print(posty.status_code)
    posty.close()
    cribl_api_text_area.text="HTTP " + str(posty.status_code)    
    print("Baseline CO2: " + str(air_dict["baseline_eCO2"]))
    print("Baseline TVOC: " + str(air_dict["baseline_TVOC"]))
    print("CO2: " + str(air_dict["CO2"]))
    print("TVOC: " + str(air_dict["TVOC"]))
    co2_reading_text_area.text=str(air_dict["CO2"])
    tvoc_reading_text_area.text=str(air_dict["TVOC"])
    battery_text_area.text="Battery: " + str(int(device.cell_percent)) + "%"
