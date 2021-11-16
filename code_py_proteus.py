
import spidev
import time
import os
import RPi.GPIO as GPIO
import urllib.request
import Ports
import pio

pio.uart = Ports.UART()  # Define serial port

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

myAPI = '4L53D7V8MX3KPQEI'
baseURL = 'https://api.thingspeak.com/update?api_key=%s' % myAPI

# Open SPI bus
spi = spidev.SpiDev()
spi.open(0, 0)

air = 5
lamp = 6
air1 = 12
lamp1 = 13
button_air = 16
button_air1 = 20
button_lamp = 19
button_lamp1 = 26
switch_mode = 21
buzz = 25
room = ""

# Define GPIO to LCD mapping
LCD_RS = 22
LCD_E = 23
LCD_D4 = 4
LCD_D5 = 17
LCD_D6 = 18
LCD_D7 = 27

# Define sensor channels
temp_channel = 0
lux_channel = 1
temp1_channel = 2
lux1_channel = 3
'''
define pin for lcd
'''
# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005
delay = 1

GPIO.setup(button_air, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(button_air1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(button_lamp, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(button_lamp1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(switch_mode, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(buzz, GPIO.OUT)
GPIO.setup(air, GPIO.OUT)
GPIO.setup(lamp, GPIO.OUT)
GPIO.setup(air1, GPIO.OUT)
GPIO.setup(lamp1, GPIO.OUT)
GPIO.setup(LCD_E, GPIO.OUT)  # E
GPIO.setup(LCD_RS, GPIO.OUT)  # RS
GPIO.setup(LCD_D4, GPIO.OUT)  # DB4
GPIO.setup(LCD_D5, GPIO.OUT)  # DB5
GPIO.setup(LCD_D6, GPIO.OUT)  # DB6
GPIO.setup(LCD_D7, GPIO.OUT)  # DB7

# Define some device constants
LCD_WIDTH = 20  # Maximum characters per line
LCD_CHR = True
LCD_CMD = False
LCD_LINE_1 = 0x80  # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0  # LCD RAM address for the 2nd line
LCD_LINE_3 = 0x94
LCD_LINE_4 = 0xD4

'''
Function Name :lcd_init()
Function Description : this function is used to initialized lcd by sending the different commands
'''


def lcd_init():
    # Initialise display
    lcd_byte(0x33, LCD_CMD)  # 110011 Initialise
    lcd_byte(0x32, LCD_CMD)  # 110010 Initialise
    lcd_byte(0x06, LCD_CMD)  # 000110 Cursor move direction
    lcd_byte(0x0C, LCD_CMD)  # 001100 Display On,Cursor Off, Blink Off
    lcd_byte(0x28, LCD_CMD)  # 101000 Data length, number of lines, font size
    lcd_byte(0x01, LCD_CMD)  # 000001 Clear display
    time.sleep(E_DELAY)


'''
Function Name :lcd_byte(bits ,mode)
Fuction Name :the main purpose of this function to convert the byte data into bit and send to lcd port
'''


def lcd_byte(bits, mode):
    # Send byte to data pins
    # bits = data
    # mode = True  for character
    #        False for command

    GPIO.output(LCD_RS, mode)  # RS

    # High bits
    GPIO.output(LCD_D4, False)
    GPIO.output(LCD_D5, False)
    GPIO.output(LCD_D6, False)
    GPIO.output(LCD_D7, False)
    if bits & 0x10 == 0x10:
        GPIO.output(LCD_D4, True)
    if bits & 0x20 == 0x20:
        GPIO.output(LCD_D5, True)
    if bits & 0x40 == 0x40:
        GPIO.output(LCD_D6, True)
    if bits & 0x80 == 0x80:
        GPIO.output(LCD_D7, True)

    # Toggle 'Enable' pin
    lcd_toggle_enable()

    # Low bits
    GPIO.output(LCD_D4, False)
    GPIO.output(LCD_D5, False)
    GPIO.output(LCD_D6, False)
    GPIO.output(LCD_D7, False)
    if bits & 0x01 == 0x01:
        GPIO.output(LCD_D4, True)
    if bits & 0x02 == 0x02:
        GPIO.output(LCD_D5, True)
    if bits & 0x04 == 0x04:
        GPIO.output(LCD_D6, True)
    if bits & 0x08 == 0x08:
        GPIO.output(LCD_D7, True)

    # Toggle 'Enable' pin
    lcd_toggle_enable()


def lcd_toggle_enable():
    # Toggle enable
    time.sleep(E_DELAY)
    GPIO.output(LCD_E, True)
    time.sleep(E_PULSE)
    GPIO.output(LCD_E, False)
    time.sleep(E_DELAY)


def lcd_string(message, line):
    # Send string to display

    message = message.ljust(LCD_WIDTH, " ")

    lcd_byte(line, LCD_CMD)

    for i in range(LCD_WIDTH):
        lcd_byte(ord(message[i]), LCD_CHR)

# Function to read SPI data from MCP3008 chip
# Channel must be an integer 0-7
def ReadChannel(channel):
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data


def ConvertTemp(data, places):
    temp = ((data * 500) / float(1023))
    temp = round(temp, places)
    return temp


def CovertLux(data, places):
    lux = int(data * 2.3753)
    lux = round(lux, places)
    return lux


def ShowLux(channel, line):
    lux_level = ReadChannel(channel)
    if channel == lux_channel:
        room = "ROOM 01"
    elif channel == lux1_channel:
        room = "ROOM 02"
    lux = CovertLux(lux_level, 1)
    lux_string = "LUX {}     {}".format(lux, room)
    lcd_string(lux_string, line)
    return lux


def ShowTemp(channel, line):
    temp_level = ReadChannel(channel)
    if channel == temp_channel:
        room = "ROOM 01"
    elif channel == temp1_channel:
        room = "ROOM 02"
    temp = ConvertTemp(temp_level, 1)
    temp_string = "TEMP {} C  {}".format(temp, room)
    lcd_string(temp_string, line)
    return temp


def room01():
    temp = ShowTemp(temp_channel, LCD_LINE_1)
    lux = ShowLux(lux_channel, LCD_LINE_3)

    if temp >= 40:
        GPIO.output(air, HIGH)
    else:
        GPIO.output(air, LOW)
    if lux <= 400:
        GPIO.output(lamp, HIGH)
    else:
        GPIO.output(lamp, LOW)
    return temp, lux


def room02():
    temp1 = ShowTemp(temp1_channel, LCD_LINE_2)
    lux1 = ShowLux(lux1_channel, LCD_LINE_4)

    if temp1 >= 40:
        GPIO.output(air1, HIGH)
    else:
        GPIO.output(air1, LOW)
    if lux1 <= 400:
        GPIO.output(lamp1, HIGH)
    else:
        GPIO.output(lamp1, LOW)
    return temp1, lux1
delay = 5
lcd_init()
lcd_string("welcome to my home", LCD_LINE_1)
time.sleep(2)
HIGH = 1
LOW = 0
pio.uart.setup(9600)
state_btn_air1 = LOW
state_btn_lamp = LOW
state_btn_lamp1 = LOW
state_btn_air = LOW

while 1:
    temp = ShowTemp(temp_channel, LCD_LINE_1)
    lux = ShowLux(lux_channel, LCD_LINE_3)
    temp1 = ShowTemp(temp1_channel, LCD_LINE_2)
    lux1 = ShowLux(lux1_channel, LCD_LINE_4)
    #send data to sever
    conn = urllib.request.urlopen(baseURL + '&field1=%s&field2=%s&field3=%s&field4=%s' % (temp, lux, temp1, lux1))
    conn.close()
    #mode 1 : Auto & 2 : Manual
    if GPIO.input(switch_mode)  == HIGH:
        print("Auto")
        room01()
        room02()
    else:
        print("Manual")
        # button air
        if GPIO.input(button_air) == LOW:
            state_btn_air =not  state_btn_air
            GPIO.output(air,state_btn_air)
            time.sleep(0.1)
        # button air
        if GPIO.input(button_air1) == LOW:
            state_btn_air1 =not  state_btn_air1
            GPIO.output(air1,state_btn_air1)
            time.sleep(0.1)
        # button lamp
        if GPIO.input(button_lamp) == LOW:
            state_btn_lamp =not  state_btn_lamp
            GPIO.output(lamp,state_btn_lamp)
            time.sleep(0.1)
        # button lamp1
        if GPIO.input(button_lamp1) == LOW:
            state_btn_lamp1 =not  state_btn_lamp1
            GPIO.output(lamp1,state_btn_lamp1)
            time.sleep(0.1)
    #detecte people
    Data = pio.uart.recv()
    time.sleep(2)
    if Data == "0":
        
        print("NO DETECED")
        GPIO.output(buzz,LOW)
    elif Data =="1":
        print("DETECED")
        GPIO.output(buzz,HIGH)

    time.sleep(0.2)
