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

# Servo things
pwm = pwmio.PWMOut(board.A3, frequency=50)
servo = servo.Servo(pwm)
up = 1
down = 120
lastValue = 120

def potentiometer_to_threshold(value):
    return (-1 * ((value / 1023 * 6.0) - 2)) # number multiplied is range, number subtracted determines higher bound, -1 is there to flip the slider motion to match the muscle sensor sensitivity operation. In this case, the range goes from -4 to 2.

def potentiometer_to_range(value):
    return (value / 1023 * 4) + 1 # Number multiplied is range, number added determines lower bound. In this case, slider returns values between 1 and 5.

def potentiometer_to_color(value):
    return value / 1023 * 255 # Scale the potentiometer values (0-1023) to the colorwheel values (0-255)

def sendSignal(position):
    global lastValue
    if (usingMuscleSensor): # Some code to control led brightness and color for visual feedback
        ratio = position / 120
        ledBrightness = int(255 - (254 * ratio)) # Changes brightness of on-board LED based on muscle activity
        pixels.fill(colorwheel((int(165 * ratio)))) # Changes led colors on slider based on the muscle activity
    else:
        pixels.fill(colorwheel(potentiometer_to_color(potentiometer.value))) # Changes led colors on slider based on the position of the potentiometer.
        ledBrightness = 1
    if (position <= lastValue and position < 120): # Determines when leg is bending vs straightening and not at rest straightened.
        onboardpixels.fill((ledBrightness, 0, 1)) # On-board led turns red when bending, brightness determined by how bent the knee is (if using muscle sensor)
    else:
        onboardpixels.fill((0, 0, ledBrightness)) # When straight, on-board led turns green if using positional sensor or blue when using muscle sensor, brightness determined by how straight the knee is (if using muscle sensor)
    if (position != lastValue): # Checks the last sent signal so duplicate signals aren't sent every loop. Not sure if it matters... ¯\_(ツ)_/¯
        servo.angle = position
        lastValue = position
        print("Signal Sent")

def changeMode():
    global usingMuscleSensor
    if (usingMuscleSensor):
        usingMuscleSensor = False
    else:
        usingMuscleSensor = True
    time.sleep(.3) # Cheap debounce

def changeBrightness(): # This function is no longer called anywhere, but I may integrate it back in at a later date. # changeBrightness() # If the on-board button is pressed, it will change the brightness multiplier for on-board LED. Values are off, dim, medium, bright.
    global ledBrightness
    if (ledBrightness == 0.0): # This modifies the value of ledBrightness which is then used as a multiplier for brightness. 0 = off, .01 = 10%, .5 = 50%, 1 = 100%
        ledBrightness = 0.01
    elif (ledBrightness == 0.01):
        ledBrightness = 0.32
    elif (ledBrightness == 0.32):
        ledBrightness = 1.0
    else:
        ledBrightness = 0.0

def get_voltage(pin):
    return (pin.value / 65536) # Returns percentage of 16-bit max-value of muscle sensor.

servo.angle = down # start leg in straight position on boot

while True:
    try:        
        if not boardButton.value: # If on board button is pressed, changes mode from accelerometer controlled to muscle sensor controlled
                changeMode() 
        if (usingMuscleSensor):
            muscleReading = get_voltage(analogPinA0)
            rangeAdjustment = potentiometer_to_range(potentiometer.value)
            print("Actual Voltage %: "+str(muscleReading) + ", Range Multiplier: " + str(rangeAdjustment))
            if (muscleReading < .04): # Ignore small muscle activity like weak twitches
                muscleReading = 0
            mappedRangeValue = int(muscleReading * -120 * rangeAdjustment) + 120  # Maps range of muscle activity to range of servo and determines servo value to send. Servo Position = (Muscle Sensor 0-1 * Range as a negative because higher values mean straight while lower means bend * increases the range so servo is more sensitive to activity) + our starting point of the range so that 0 muscle activity means servo position is at 120, which is down.
            if (mappedRangeValue < 1): # When sensitivity slider is set higher than 0, it's easy to go beyond the max limit for the knee to be bent. This keeps it in bounds.
                mappedRangeValue = 1
            if (mappedRangeValue > 120): # Same here, but on the other extreme. If I did my math right it should never go higher than 120 anyway.
                mappedRangeValue = 120
            print("Adjusted Voltage %: "+str(muscleReading) + ", Signal to Send: " + str(mappedRangeValue))
            if (button.value): # Button acts as a safety switch, pressing it will tell the servo to keep the knee straight
                sendSignal(down) # This value will always be 120.
            else:
                sendSignal(mappedRangeValue) # this value will be somewhere between 120 and 1. 1 is knee completely bent, 120 is completely straight.
        else:
            threshold = potentiometer_to_threshold(potentiometer.value)
            print("Threshold: " + str(threshold))
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
        print("Likely a misread from a sensor. No biggie.")
    #time.sleep(.5) # I use this for debugging to read all my print statements. Remove it when using in production.
