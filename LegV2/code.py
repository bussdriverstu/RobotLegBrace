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

# Calibration mode (This is for using both the muscle sensor and accelerometer do provide optimal straightening timing)
calibratedThreshold = None

# Muscle Sensor Configuration
usingMuscleSensor = False
analogPinA0 = AnalogIn(board.A0) # Use on handicapped leg
analogPinA1 = AnalogIn(board.A1) # Use on strong leg

# Button for brightness control of on-board LED
boardButton = digitalio.DigitalInOut(board.BUTTON)
boardButton.switch_to_input(pull=digitalio.Pull.UP)
ledBrightness = 0.01

# Bend Button
button = digitalio.DigitalInOut(board.RX)
button.switch_to_input(pull=digitalio.Pull.DOWN)

# On Board Pixel
onBoardPixels = boardpixel.NeoPixel(board.NEOPIXEL, 1)

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

def DoCalibration(threshold):
    global calibratedThreshold
    if (calibratedThreshold == None or threshold == None):
        calibratedThreshold = threshold
        print(calibratedThreshold)
    onBoardPixels.fill((255, 255, 255))
    pixels.fill(0)

def PotentiometerToThreshold(value):
    return (-1 * ((value / 1023 * 6.0) - 2)) # Number multiplied is range, number subtracted determines higher bound, -1 is there to flip the slider motion to match the muscle sensor sensitivity operation. In this case, the range goes from -4 to 2.

def PotentiometerToRange(value):
    return (value / 1023 * 4) + 1 # Number multiplied is range, number added determines lower bound. In this case, slider returns values between 1 and 5.

def PotentiometerToColor(value):
    return value / 1023 * 255 # Scale the potentiometer values (0-1023) to the colorwheel values (0-255)

def ControlLightsBasedOnServoPosition(position): # Controls LEDs based on servo position
    if (usingMuscleSensor): # Some code to control led brightness and color for visual feedback
        ratio = position / 120
        ledBrightness = int(255 - (254 * ratio)) # Changes brightness of on-board LED based on muscle activity
        #print("Ratio: " + str(ratio))
        pixels.fill(0)
        colorBrightness = colorwheel((int(165 * ratio)) & 255) # Colors blue to red on color wheel
        ledCount = 4 # Number of LEDs is slider strip
        for i in range(ledCount): # Cycle through LEDs 
            threshold = (ledCount-i)/ledCount # Spits out evenly spaced thresholds based on number of LEDs to compare to the ratio. In this case, 4 LEDs spit out 1, 0.75, 0.5, and 0.25
            if (ratio < threshold): # If muscle activity is within a certain threshold...
                pixels[i] = colorBrightness # Assign color and brightness
    else:
        pixels.fill(colorwheel(PotentiometerToColor(potentiometer.value))) # Changes led colors on slider based on the position of the potentiometer.
        ledBrightness = 1
    if (position <= lastValue and position < 120): # Determines when leg is bending vs straightening and not at rest straightened.
        onBoardPixels.fill((ledBrightness, 0, 1)) # On-board led turns red when bending, brightness determined by how bent the knee is (if using muscle sensor)
    else:
        onBoardPixels.fill((0, 0, ledBrightness)) # When straight, on-board led turns green if using positional sensor or blue when using muscle sensor, brightness determined by how straight the knee is (if using muscle sensor)
    
def SendSignal(position):
    global lastValue
    ControlLightsBasedOnServoPosition(position) # Update LED colors and brightness
    if (position != lastValue): # Checks the last sent signal so duplicate signals aren't sent every loop. Not sure if it matters... ¯\_(ツ)_/¯
        servo.angle = position
        lastValue = position
        #print("Signal Sent")

def ChangeMode():
    global usingMuscleSensor
    if (usingMuscleSensor):
        usingMuscleSensor = False
    else:
        usingMuscleSensor = True
    time.sleep(.3) # Cheap debounce

def ChangeBrightness(): # This function is no longer called anywhere, but I may integrate it back in at a later date. # ChangeBrightness() # If the on-board button is pressed, it will change the brightness multiplier for on-board LED. Values are off, dim, medium, bright.
    global ledBrightness
    if (ledBrightness == 0.0): # This modifies the value of ledBrightness which is then used as a multiplier for brightness. 0 = off, .01 = 10%, .5 = 50%, 1 = 100%
        ledBrightness = 0.01
    elif (ledBrightness == 0.01):
        ledBrightness = 0.32
    elif (ledBrightness == 0.32):
        ledBrightness = 1.0
    else:
        ledBrightness = 0.0

def GetVoltage(pin):
    return (pin.value / 65536) # Returns percentage of 16-bit max-value of muscle sensor.

servo.angle = down # Start leg in straight position on boot

while True:
    try:
        accel_x, accel_y, accel_z = bno.acceleration # Gets position of thigh
        if not boardButton.value: # If on board button is pressed, changes mode from accelerometer controlled to muscle sensor controlled
                ChangeMode()
        if (usingMuscleSensor):
            muscleOneReading = GetVoltage(analogPinA0) # Muscle Sensor One
            muscleTwoReading = GetVoltage(analogPinA1) # Muscle Sensor Two
            rangeAdjustment = PotentiometerToRange(potentiometer.value)
            #print("Actual Voltage %: "+str(muscleOneReading) + ", Range Multiplier: " + str(rangeAdjustment))
            if (muscleOneReading < .04): # Ignore small muscle activity like weak twitches
                muscleOneReading = 0
            mappedRangeValue = int(muscleOneReading * -120 * rangeAdjustment) + 120  # Maps range of muscle activity to range of servo and determines servo value to send. Servo Position = (Muscle Sensor 0-1 * Range as a negative because higher values mean straight while lower means bend * increases the range so servo is more sensitive to activity) + our starting point of the range so that 0 muscle activity means servo position is at 120, which is down.
            if (mappedRangeValue < 1): # When sensitivity slider is set higher than 0, it's easy to go beyond the max limit for the knee to be bent. This keeps it in bounds.
                mappedRangeValue = 1
            if (mappedRangeValue > 120): # Same here, but on the other extreme. If I did my math right it should never go higher than 120 anyway.
                mappedRangeValue = 120
            #print("Adjusted Voltage %: "+str(muscleOneReading) + ", Signal to Send: " + str(mappedRangeValue))
            if (button.value): # Button acts as a safety switch, pressing it will tell the servo to keep the knee straight
                SendSignal(down) # This value will always be 120.
                print("Adjusted Voltage %: "+str(muscleOneReading) + ", Signal to Send: " + str(mappedRangeValue))
                print("X: %0.6f  Y THRESHOLD VALUE: %0.6f Z: %0.6f  m/s^2" % (accel_x, accel_y, accel_z)) # Will use these values you determine when to ignore muscle sensor activity and just straighten the leg
            else:
                if (calibratedThreshold is None or accel_y > calibratedThreshold): # If using the accelerometer in muscle mode, straighten leg past the calibrated threshold
                    SendSignal(mappedRangeValue) # this value will be somewhere between 120 and 1. 1 is knee completely bent, 120 is completely straight.
                else:
                    SendSignal(down)
                print("calibrated: "+str(calibratedThreshold))
                print(accel_y)
        else:
            threshold = PotentiometerToThreshold(potentiometer.value)
            print("Threshold: " + str(threshold))
            print("X: %0.6f  Y: %0.6f Z: %0.6f  m/s^2" % (accel_x, accel_y, accel_z))
            if (accel_z > -4 and accel_z < 4): # Checking to make sure the leg is upright in case user has fallen over
                if (accel_y > threshold or button.value): # Checks if the accelerometer reading is greater than the threshold set by the slider position or if the button is pressed, then bends the leg if either are true.
                    print("bend")
                    SendSignal(up)
                    onBoardPixels.fill((255 * ledBrightness, 0, 0)) # On board led turns red when bending, brightness determined by on-board button
                else: # Straightens the leg
                    print("straight")
                    if (lastValue is not down): # fire this once at the moment the button is released
                        if (threshold == 2): # If slider is all the way at 2 (i.e. full manual mode)...
                            DoCalibration(accel_y) # Take note the instance the leg straightens and assign muscle sensor straighten threshold for muscle activity mode
                        else:
                            DoCalibration(None) # If the slider is not at 2, assign None to calibration to ignore position sensor in muscle activity mode
                    SendSignal(down)
                    onBoardPixels.fill((0, 255 * ledBrightness, 0)) # On board led turns green when straight, brightness determined by on-board button
            else:
                print("you fell over, clumsy nerd")
    except Exception as e:
        print("An error has occured, likely a misread from a sensor and can be ignored. Error: "+str(e))
    #time.sleep(.2) # I use this for debugging to read all my print statements. Remove it when using in production.
