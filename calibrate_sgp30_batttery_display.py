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
BACKGROUND_COLOR = 0x000000  # Black
TEXT1_COLOR = 0x00FF00 # Bright green
TEXT2_COLOR = 0X0095a1 # Kind of a battleship grey 
TEXT3_COLOR = 0xFFFFFF # White
RED = 0xFF0000
FONTSCALE = 2

got_bootime_yet = 0
cribl_url = os.getenv('cribl_url')

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

# Initialize IAG algorithm 
if 0x58 in i2c_address_list:
    sgp30 = adafruit_sgp30.Adafruit_SGP30(board.I2C())
    sgp30.iaq_init()
    sensor_id = [hex(i) for i in sgp30.serial]
    short_id = sensor_id[2]
    print("SGP30 serial # ", sensor_id)


# Get wifi and innernet
print("Getting on WiFi..")
wifi.radio.connect(os.getenv('CIRCUITPY_WIFI_SSID'), os.getenv('CIRCUITPY_WIFI_PASSWORD'))

hexy = [hex(i) for i in wifi.radio.mac_address]
uid = re.sub("0x", "", hexy[3]) + ":" + re.sub("0x", "", hexy[4]) + ":" + re.sub("0x", "", hexy[5])
pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

battery_percent = device.cell_percent
print("Battery: " + str(battery_percent))

def get_time():
    time_url = "http://worldtimeapi.org/api/ip"
    results={}
    try:
        now = requests.get(time_url)
        print("get_time HTTP status: " + str(now.status_code))
        if now.status_code==200:
            nowdict = now.json()
            epoch = nowdict["unixtime"]
        else:
            epoch = -1000000
        now.close()
        results["epoch"]=epoch
        results["status_code"]=now.status_code
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
    co2_text = "CO2 "
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
    ppm_text = "ppm: "
    ppm_text_area=label.Label(terminalio.FONT, text=ppm_text, color=TEXT1_COLOR, base_alignment=True)
    ppm_text_width = ppm_text_area.bounding_box[2] 
    ppm_text_group = displayio.Group(
        scale=1,
        x=co2_text_width,
        y=co2_text_height
    )    
    ppm_text_group.append(ppm_text_area)
    splash.append(ppm_text_group)
    
    # Make TVOC label
    tvoc_text= "TVOC "
    tvoc_text_area = label.Label(terminalio.FONT, text=tvoc_text, color=TEXT1_COLOR, base_alignment=True)
    tvoc_text_width = tvoc_text_area.bounding_box[2] * FONTSCALE
    tvoc_text_height = tvoc_text_area.bounding_box[3] * FONTSCALE
    tvoc_text_group = displayio.Group(
        scale=FONTSCALE,
        x=10,
        y=co2_text_height + tvoc_text_height
    ) 
    tvoc_text_group.append(tvoc_text_area)
    splash.append(tvoc_text_group)   
    
    # Make smaller parts per billion label
    ppb_text = "ppb: "
    ppb_text_area=label.Label(terminalio.FONT, text=ppb_text, color=TEXT1_COLOR, base_alignment=True, padding_left=5, padding_right=5)
    ppb_text_width = ppb_text_area.bounding_box[2] 
    ppb_text_group = displayio.Group(
        scale=1,
        x=tvoc_text_width,
        y=co2_text_height + tvoc_text_height
    )
    ppb_text_group.append(ppb_text_area)
    splash.append(ppb_text_group)
    
    tvoc_base_alignment = co2_text_height + tvoc_text_height
    co2_base_alignment = co2_text_height
    label_width = tvoc_text_width + ppb_text_width

    # Make CO2baseline Label
    co2_baseline_text = "CO2 baseline: "
    co2_baseline_text_area = label.Label(terminalio.FONT, text=co2_baseline_text, color=TEXT1_COLOR, base_alignment=True, padding_right=5)
    co2_baseline_text_width = co2_baseline_text_area.bounding_box[2] 
    co2_baseline_text_height = co2_baseline_text_area.bounding_box[3]
    co2_baseline_text_group = displayio.Group(
        scale=1,
        x=10,
        y=co2_text_height + tvoc_text_height + co2_baseline_text_height + 5
    )
    co2_baseline_base_alignment = co2_text_height + tvoc_text_height + co2_baseline_text_height + 5
    co2_baseline_text_group.append(co2_baseline_text_area)
    splash.append(co2_baseline_text_group)
    
    # Make TVOC_baseline Label
    tvoc_baseline_text = "TVOC baseline: "
    tvoc_baseline_text_area = label.Label(terminalio.FONT, text=tvoc_baseline_text, color=TEXT1_COLOR, base_alignment=True, padding_right=5)
    tvoc_baseline_text_width = tvoc_baseline_text_area.bounding_box[2] 
    tvoc_baseline_text_height = tvoc_baseline_text_area.bounding_box[3] 
    tvoc_baseline_text_group = displayio.Group(
        scale=1,
        x=10,
        y=co2_text_height + tvoc_text_height + co2_baseline_text_height + tvoc_baseline_text_height + 5
    )
    tvoc_baseline_base_alignment = co2_text_height + tvoc_text_height + co2_baseline_text_height + tvoc_baseline_text_height + 5
    tvoc_baseline_text_group.append(tvoc_baseline_text_area)
    splash.append(tvoc_baseline_text_group)

    # Make uptime Label
    uptime_text = "Uptime: "
    uptime_text_area = label.Label(terminalio.FONT, text=uptime_text, color=TEXT1_COLOR, base_alignment=True, padding_right=5)
    uptime_text_width = uptime_text_area.bounding_box[2] 
    uptime_text_height = uptime_text_area.bounding_box[3] 
    uptime_text_group = displayio.Group(
        scale=1,
        x=10,
        y=co2_text_height + tvoc_text_height + co2_baseline_text_height + tvoc_baseline_text_height + uptime_text_height + 5
    )
    uptime_base_alignment = co2_text_height + tvoc_text_height + co2_baseline_text_height + tvoc_baseline_text_height + uptime_text_height + 5
    uptime_text_group.append(uptime_text_area)
    splash.append(uptime_text_group)

    # Make HTTP status label for worldtimeapi.org
    api_label_text = "worldtimeapi.org"
    api_label_text_area = label.Label(terminalio.FONT, text=api_label_text, color=TEXT2_COLOR, base_alignment=True)
    api_label_text_width = api_label_text_area.bounding_box[2]
    api_label_text_height = api_label_text_area.bounding_box[3]
    api_label_text_group = displayio.Group(
        scale=1,
        x=display.width - api_label_text_width,
        y=api_label_text_height
    )
    api_label_text_group.append(api_label_text_area)
    splash.append(api_label_text_group)

    cribl_api_text = "cribl.io"
    cribl_api_text_area = label.Label(terminalio.FONT, text=cribl_api_text, color=TEXT2_COLOR, base_alignment=True)
    cribl_api_text_width = cribl_api_text_area.bounding_box[2]
    cribl_api_text_height = cribl_api_text_area.bounding_box[3]
    cribl_api_text_group = displayio.Group(
        scale=1,
        x=display.width - int(api_label_text_width/2) - int(cribl_api_text_width/2),
        y=int(cribl_api_text_height * 3.5)
    )
    cribl_api_text_group.append(cribl_api_text_area)
    splash.append(cribl_api_text_group)

    sensor_id_text = "Sensor ID"
    sensor_id_text_area = label.Label(terminalio.FONT, text=sensor_id_text, color=TEXT2_COLOR, base_alignment=True)
    sensor_id_text_width = sensor_id_text_area.bounding_box[2]
    sensor_id_text_height = sensor_id_text_area.bounding_box[3]
    sensor_id_text_group = displayio.Group(
        scale=1,
        x=display.width - int(api_label_text_width/2) - int(sensor_id_text_width/2),
        y=int(sensor_id_text_height * 6)
    )
    sensor_id_text_group.append(sensor_id_text_area)
    splash.append(sensor_id_text_group)    

    sensor = short_id
    sensor_area = label.Label(terminalio.FONT, text=sensor, color=TEXT3_COLOR, base_alignment=True)
    sensor_width = sensor_area.bounding_box[2]
    sensor_height = sensor_area.bounding_box[3]
    sensor_group = displayio.Group(
        scale=1,
        x=display.width - int(api_label_text_width/2) - int(cribl_api_text_width/2),
        #x=display.width - int(sensor_id_text_width/2) - int(sensor_width/2),
        y=int(sensor_id_text_height * 7)
    )
    sensor_group.append(sensor_area)
    splash.append(sensor_group)

    basealign = {}
    basealign["tvoc"]=tvoc_base_alignment
    basealign["co2"]=co2_base_alignment
    basealign["big_label_width"]=label_width
    basealign["small_label_width"]=tvoc_baseline_text_width + 5
    basealign["co2_baseline"]=co2_baseline_base_alignment
    basealign["tvoc_baseline"]=tvoc_baseline_base_alignment
    basealign["uptime"]=uptime_base_alignment
    basealign["api_label_width"]=api_label_text_width
    return(basealign)

if got_bootime_yet < 1:
    print("Getting Epoch...")
    time_api_results = get_time()
    epoch=time_api_results["epoch"]
    time_api_status_code = time_api_results["status_code"]
    print(epoch)

basealignments = make_labels()

time_api_text = "HTTP 418"
time_api_text_area = label.Label(terminalio.FONT, text=time_api_text, color=TEXT3_COLOR, base_alignment=True)
time_api_text_width = time_api_text_area.bounding_box[2]
time_api_text_height = time_api_text_area.bounding_box[3]
time_api_text_group = displayio.Group(
    scale=1,
    x=display.width - int(basealignments["api_label_width"]/2) - int(time_api_text_width/2),
    y=time_api_text_height * 2
)
time_api_text_group.append(time_api_text_area)
splash.append(time_api_text_group)

cribl_api_text = "HTTP 418"
cribl_api_text_area = label.Label(terminalio.FONT, text=cribl_api_text, color=TEXT3_COLOR, base_alignment=True)
cribl_api_text_width = cribl_api_text_area.bounding_box[2]
cribl_api_text_group = displayio.Group(
    scale=1,
    x=display.width - int(basealignments["api_label_width"]/2) - int(cribl_api_text_width/2),
    y=int(time_api_text_height * 4.5)
)
cribl_api_text_group.append(cribl_api_text_area)
splash.append(cribl_api_text_group)

co2_reading_text = "0000"
co2_reading_text_area = label.Label(terminalio.FONT, text=co2_reading_text, color=TEXT3_COLOR, base_alignment=True)
co2_reading_text_group = displayio.Group(
    scale=FONTSCALE,
    x=basealignments["big_label_width"],
    y=basealignments["co2"]
)
co2_reading_text_group.append(co2_reading_text_area)
splash.append(co2_reading_text_group)

tvoc_reading_text = "0000"
tvoc_reading_text_area = label.Label(terminalio.FONT, text=tvoc_reading_text, color=TEXT3_COLOR, base_alignment=True)
tvoc_reading_text_group = displayio.Group(
    scale=FONTSCALE,
    x=basealignments["big_label_width"],
    y=basealignments["tvoc"]
)
tvoc_reading_text_group.append(tvoc_reading_text_area)
splash.append(tvoc_reading_text_group)

co2_baseline_text = "0000"
co2_baseline_text_area = label.Label(terminalio.FONT, text=co2_baseline_text, color=TEXT3_COLOR, base_alignment=True)
co2_baseline_text_group = displayio.Group(
    scale=1,
    x=basealignments["small_label_width"],
    y=basealignments["co2_baseline"]
)
co2_baseline_text_group.append(co2_baseline_text_area)
splash.append(co2_baseline_text_group)

tvoc_baseline_text = "0000"
tvoc_baseline_text_area = label.Label(terminalio.FONT, text=tvoc_baseline_text, color=TEXT3_COLOR, base_alignment=True)
tvoc_baseline_text_group = displayio.Group(
    scale=1,
    x=basealignments["small_label_width"],
    y=basealignments["tvoc_baseline"]
)
tvoc_baseline_text_group.append(tvoc_baseline_text_area)
splash.append(tvoc_baseline_text_group)

uptime_text = "0000"
uptime_text_area = label.Label(terminalio.FONT, text=uptime_text, color=TEXT3_COLOR, base_alignment=True)
uptime_text_group = displayio.Group(
    scale=1,
    x=basealignments["small_label_width"],
    y=basealignments["uptime"]
)
uptime_text_group.append(uptime_text_area)
splash.append(uptime_text_group)

calibration_text = "CALIBRATING"
calibration_text_area = label.Label(terminalio.FONT, text=calibration_text, color=TEXT3_COLOR, base_alignment=True, background_color=RED)
calibration_text_width = calibration_text_area.bounding_box[2] * FONTSCALE
calibration_text_height = calibration_text_area.bounding_box[3] * FONTSCALE
calibration_text_group = displayio.Group(
    scale=FONTSCALE,
    x=int(display.width/2) - int(calibration_text_width/2),
    y=display.height
)
calibration_text_group.append(calibration_text_area)
splash.append(calibration_text_group)

countdown_text = "300"
countdown_text_area = label.Label(terminalio.FONT, text=countdown_text, color=TEXT3_COLOR)
countdown_text_width = countdown_text_area.bounding_box[2]
countdown_text_height = countdown_text_area.bounding_box[3]
countdown_text_group = displayio.Group(
    scale=1,
    x=display.width - countdown_text_width,
    y=display.height - countdown_text_height
)
countdown_text_group.append(countdown_text_area)
splash.append(countdown_text_group)

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

while True:
    # Y'all know what time it is?
    if got_bootime_yet < 1:
        now = epoch
    else:
        time_api_results = get_time()
        now=time_api_results["epoch"]
        time_api_status_code = time_api_results["status_code"]
    if time_api_status_code == 200:
        uptime_minutes = ((now - epoch) / 60) 
    else: 
        uptime_minutes = 8675309

    # Create JSON object to POST to HTTP listener
    message_json = {}        
    air_dict={}
    air_dict["baseline_eCO2"] = sgp30.baseline_eCO2
    air_dict["baseline_TVOC"] = sgp30.baseline_TVOC
    air_dict["CO2"] = sgp30.eCO2
    air_dict["TVOC"] = sgp30.TVOC
    air_dict["sensor_id"] = short_id
    message_json["data"] = air_dict
    message_json["uptime"] = uptime_minutes
    message_json["full_sensor_id"] = sensor_id
    message_json["mode"]="calibration"
    message_json["board_id"] = uid
    air_json = json.dumps(message_json)   
    
    # Post data to Cribl
    posty = requests.post(cribl_url, data=air_json)
    print(posty.status_code)
    posty.close()

    # Send some stuff to the console
    print("Uptime: " + str(uptime_minutes) + " min")
    print("Baseline CO2: " + str(air_dict["baseline_eCO2"]))
    print("Baseline TVOC: " + str(air_dict["baseline_TVOC"]))
    print("CO2: " + str(air_dict["CO2"]))
    print("TVOC: " + str(air_dict["TVOC"]))

    # Update displayed values
    co2_reading_text_area.text=str(air_dict["CO2"])
    tvoc_reading_text_area.text=str(air_dict["TVOC"])
    co2_baseline_text_area.text=str(air_dict["baseline_eCO2"])
    tvoc_baseline_text_area.text=str(air_dict["baseline_TVOC"])
    uptime_text_area.text=str(int(message_json["uptime"])) + " min"
    time_api_text_area.text="HTTP " + str(time_api_status_code)
    cribl_api_text_area.text="HTTP " + str(posty.status_code)

    got_bootime_yet = 1
    countdown_timer = 300
    
    # Update displayed values every second even if we're not sending them to the cloud
    for run in range(300):
        co2_reading_text_area.text=str(sgp30.eCO2)
        tvoc_reading_text_area.text=str(sgp30.TVOC)
        battery_text_area.text=str(int(device.cell_percent)) + "%"
        countdown_timer -= 1
        countdown_text_area.text=str(countdown_timer)
        time.sleep(1)