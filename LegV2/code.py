import time
import board
import neopixel as boardpixel
from rainbowio import colorwheel
from adafruit_seesaw.seesaw import Seesaw
from adafruit_seesaw.analoginput import AnalogInput
from adafruit_seesaw import neopixel
from adafruit_bno08x import BNO_REPORT_ACCELEROMETER
from adafruit_bno08x.i2c import BNO08X_I2C
import pwmio
from adafruit_motor import servo
import digitalio
from analogio import AnalogIn

# Muscle Sensor Configuration
usingMuscleSensor = False
analogPinA0 = AnalogIn(board.A0)

# Button for brightness control of on-board LED
boardButton = digitalio.DigitalInOut(board.BUTTON)
boardButton.switch_to_input(pull=digitalio.Pull.UP)
ledBrightness = 0.01

# Bend Button
button = digitalio.DigitalInOut(board.RX)
button.switch_to_input(pull=digitalio.Pull.DOWN)

# On Board Pixel
onboardpixels = boardpixel.NeoPixel(board.NEOPIXEL, 1)

# NeoSlider Setup
neoslider = Seesaw(board.STEMMA_I2C(), 0x30)
potentiometer = AnalogInput(neoslider, 18)
pixels = neopixel.NeoPixel(neoslider, 14, 4, pixel_order=neopixel.GRB)

# Positional Sensor
bno = BNO08X_I2C(board.STEMMA_I2C())
bno.enable_feature(BNO_REPORT_ACCELEROMETER)

#Servo things
pwm = pwmio.PWMOut(board.A3, frequency=50)
servo = servo.Servo(pwm)
up = 1
down = 120
lastValue = 120

def potentiometer_to_threshold(value):
    return (value / 1023 * 6.0) - 4 # number multiplied is range, number subtracted determines lower bound. In this case, the range goes from -4 to 2.

def potentiometer_to_color(value):
    return value / 1023 * 255 # Scale the potentiometer values (0-1023) to the colorwheel values (0-255)

def sendSignal(position):
    global lastValue
    if (position < lastValue):
        onboardpixels.fill((255 * ledBrightness, 0, 0)) # On board led turns red when bending, brightness determined by on-board button
    else:
        onboardpixels.fill((0, 0, 255 * ledBrightness)) # On board led turns green when straight, brightness determined by on-board button
    if (position != lastValue): # Checks the last sent signal so duplicate signals aren't sent every loop. Not sure if it matters... ¯\_(ツ)_/¯
        servo.angle = position
        lastValue = position
        print("Signal Sent")

def changeMode(): # Switch from accelerometer sensor to muscle sensor control
    global usingMuscleSensor
    if (usingMuscleSensor):
        usingMuscleSensor = False
    else:
        usingMuscleSensor = True

def changeBrightness(): # Because I use the on board button to switch modes, I no long integrated this control. I may add it later via a 'set brightness mode' with the slider or something.
    global ledBrightness
    if (ledBrightness == 0.0): # I guess python doesn't have case-switch. Anyway, this modifies the value of ledBrightness which is then used as a multiplier for brightness. 0 = off, .01 = 10%, .5 = 50%, 1 = 100%
        ledBrightness = 0.01
    elif (ledBrightness == 0.01):
        ledBrightness = 0.32
    elif (ledBrightness == 0.32):
        ledBrightness = 1.0
    else:
        ledBrightness = 0.0
        
def get_value(pin):
    return (pin.value / 65536) # converts 16 bit value to a percent (0-1) and returns that result

servo.angle = down # start leg in straight position on boot

while True:
    try:
        pixels.fill(colorwheel(potentiometer_to_color(potentiometer.value))) # Changes led colors on slider based on the position of the potentiometer.
        if not boardButton.value: # If on board button is pressed, changes mode from accelerometer controlled to muscle sensor controlled
                changeMode()
        if (usingMuscleSensor):
            muscleReading = get_value(analogPinA0) # Gets value of muscle sensor in range from 0-1
            mappedRange = int(muscleReading * -120) + 120 # Maps the muscle voltage range to the servo range of motion. 1 is fully up, 120 is fully down.
            print(str(muscleReading) + ", " + str(mappedRange))
            if (button.value):
                sendSignal(down)
            else:
                sendSignal(mappedRange) #sends position to servo based on work of muscle.
        else:
            threshold = potentiometer_to_threshold(potentiometer.value)
            print(str(threshold))
            accel_x, accel_y, accel_z = bno.acceleration
            print("X: %0.6f  Y: %0.6f Z: %0.6f  m/s^2" % (accel_x, accel_y, accel_z))
            if (accel_z > -4 and accel_z < 4): # Checking to make sure the leg is upright in case use has fallen over
                if (accel_y > threshold or button.value): # Checks if the accelerometer reading is greater than the threshold set by the slider position or if the button is pressed, then bends the leg if either are true.
                    print("bend")
                    sendSignal(up)
                    onboardpixels.fill((255 * ledBrightness, 0, 0)) # On board led turns red when bending, brightness determined by on-board button
                else: # Straightens the leg
                    print("straight")
                    sendSignal(down)
                    onboardpixels.fill((0, 255 * ledBrightness, 0)) # On board led turns green when straight, brightness determined by on-board button
            else:
                print("you fell over, clumsy nerd")
    except:
        print("Likely a misread from the sensor. No biggie.")
