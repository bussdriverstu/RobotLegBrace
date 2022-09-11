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
    if (position != lastValue): # Checks the last sent signal so duplicate signals aren't sent every loop. Not sure if it matters... ¯\_(ツ)_/¯
        servo.angle = position
        lastValue = position
        print("Signal Sent")

servo.angle = down # start leg in straight position on boot

while True:
    pixels.fill(colorwheel(potentiometer_to_color(potentiometer.value))) # Changes led colors on slider based on the position of the potentiometer.
    threshold = potentiometer_to_threshold(potentiometer.value)
    print(str(threshold))
    try:
        accel_x, accel_y, accel_z = bno.acceleration
        print("X: %0.6f  Y: %0.6f Z: %0.6f  m/s^2" % (accel_x, accel_y, accel_z))
        if (accel_z > -4 and accel_z < 4): # Checking to make sure the leg is upright in case use has fallen over
            if (accel_y > threshold or button.value): # Checks if the accelerometer reading is greater than the threshold set by the slider position or if the button is pressed, then bends the leg if either are true.
                print("bend")
                sendSignal(up)
                onboardpixels.fill((10, 0, 0)) # On board led turns red when bending
            else: # Straightens the leg
                print("straight")
                sendSignal(down)
                onboardpixels.fill((0, 10, 0)) # On board led turns green when straight
        else:
            print("you fell over, clumsy nerd")
    except:
        print("Likely a misread from the sensor. No biggie.")
    time.sleep(.05)