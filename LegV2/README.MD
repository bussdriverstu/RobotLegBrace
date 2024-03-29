# Robot Leg Brace v2
## Introduction/Warning

Hi. I’ve been handicapped for about 9 years now, I’ve tried to seek out treatments to be able to walk again. However, because of the type of injury and the specific motion I’ve regained, there aren’t many options out there, especially for someone on a fixed income. I took it upon myself to build my own solution. I am not an engineer nor am I a programmer. **I do not recommend anyone follow in my footsteps. THIS IS DANGEROUS.** You could blow yourself up or injure yourself doing what I did. That said, I can walk without my crutch or cane again, which is all I wanted to do. I figured I’d share my project in case anyone else, who is poor and disabled like I am, wants to try to build their own solution. 

## Injury and Ability

My injury is unique and so my solution may not apply to you. I have full motion of my left leg; I can also straighten my right leg out and (mostly) hold my weight with it. The issue I have is being able to bend it back in after pushing it out. I also have foot drop, but I can point my toes easily enough. Again, it’s the bringing my foot back that is the issue. This device will detect when I want to bend my leg and do it for me.

## The Device

The device uses a knee brace as a base. I’ve attached a large servo to the outer thigh portion of the brace and used an old cut-up AFO foot brace to add rigidity to the two sides. I had a friend use a 3D printer to create a pulley to attach to the servo. A chain threaded through a spring which is wrapped around the servo wheel and attaches to the shin portion of the brace via another spring (this is to absorb shock of occasional muscle spasms I can have when my leg moves or is tired). When the servo rotates, it pulls the shin up, bending the knee. 

To control the servo, a microcontroller reads input from various sensors and/or a user-held button and determines when to move, bending or straightening the leg. For example, in Gait/Accelerometer mode, the microcontroller reads data from an accelerometer to determine where my leg is positioned during the walking gait. When the user's thigh reaches a certain angle, it will tell the servo to move, bending my leg. As the user moves forward, the angle will change and the servo will reverse direction, straighten the leg again. See the "Operations" section for more details and controls.

![Gait Data](GaitDataExample.png)

## Operation

There are a few controls to operate the device. A slider, a hand-held button, and the microcontroller's on-board button. Each have different functions depending on what operating mode the device is in.

### Manual Mode

When the potentiometer slider is at the zero-position (which side that is depends on how you've mounted it) press the handheld button to bend the knee, release to straighten it. When your leg is straight, the on-board LED will be green.

### Gait/Accelerometer Mode

In gait detection mode, the potentiometer slider will set the angle-position threshold that tells the servo when in the walking gait to begin bending the leg and when to straighten it again. A handheld momentary push button is used to override the sensors and manually bend the leg brace. This is useful for steps or uneven ground. You can operate the device in full manual mode by moving the slider all the way to one side (which side depends on how you’ve mounted it, but it will be refered to as the zero-position). An on-board LED light provides visual feedback of what state the brace is in. Green means the leg should be straight, red means the knee should be bent. 

### Muscle Activity Mode

There is an on-board button that will toggle operation from using the brace's position to bend to the muscle sensor. When using the muscle sensor, the light will change from green to blue and the position of the device will not affect bending and straightening. Flexing of the muscle the sensor is positioned on will bend the knee relative to how hard to flex. The slider adjusts the sensitivity of the muscle sensor so that you can get a strong signal from weak muscles. The manual bending button has also been reversed so that when you press it the leg will straighten. This was done as a safety precaution in case interference causes the muscle sensor to report higher readings than the muscle is sending. At rest, the on-board LED will be blue instead of green.

### Hybrid Mode

This mode allows for muscle activity to control the knee only when the leg is positioned within a certain threshold. When enabled it will force the leg to straighten when the leg swings forward past the set threshold. To enable, set the device in Manaul Mode by moving slider all the way to the zero-position in Gait Mode (On-board LED should be green) and use the bend-button to walk. The program will record the position of your leg when you first let go of the button to straighten during each step. Then, switch to muscle activity mode (On-board LED will be blue) and it will straighten your leg at the same position you released the button during the previous step, regardless of the muscle activity registered. To disable this feature, go to Gait mode (press the on-board button so the on-board LED is green and move the slider to any position other than zero) then press and release the bend button again. A white flash will indicate when you have enabled and set, or disabled the setting successfully.

## Installation, Code and Libraries

The code is written in CircuitPython 7.3 and uses the following libraries in the lib folder:

- adafruit_bno08x
- adafruit_bus_device
- adafruit_motor
- adafruit_seesaw
- adafruit_pixelbuf.mpy
- neopixel.mpy

Instructions for installing CircuitPython on the microcontroller can be found here: https://learn.adafruit.com/welcome-to-circuitpython/installing-circuitpython 

After installing, you should be able to copy 'code.py' and the entire 'lib' folder from this repository into the root directory of the microcontroller and you'll be done. Again, I am not a programmer, but I commented what most of it does to the best of my ability. 

## Design/Wiring Diagram

![LegV2 Diagram](robotlegv2design.png)

## Materials List for building Robot Leg Brace Version 2

- Brace https://www.amazon.com/gp/product/B07BT59Q6X
- Battery https://www.amazon.com/24-VOLT-4-0-AMP-LITHIUM-KB-424-03/dp/B01KAL4IO2
- Battery Quick Connect Terminal Adapter https://www.amazon.com/gp/product/B09BKGX81V
- Small Buck Converter https://www.amazon.com/gp/product/B07MKQXNWG/
- Large Buck Converter https://www.amazon.com/dp/B08GCX2RJ1
- Servo https://www.ebay.com/itm/123414770402
- 10 Gauge Wire https://www.amazon.com/Copper-American-Gauge-Wire/dp/B0796JJHTQ/
- 22 Gauge Wire https://www.amazon.com/Gauge-Wire-Solid-Hookup-Wires/dp/B088KQFHV7/
- Adafruit QT Py RP2040 https://www.adafruit.com/product/4900
- Adafruit BNO085 9-DOF Orientation Sensor https://www.adafruit.com/product/4754
- STEMMA QT Cable https://www.adafruit.com/product/4399
- 1k Ohm Resistors https://www.amazon.com/MCIGICM-Values-Resistor-Assortment-Resistors/dp/B06WRQS97C/
- ANR Corp R24 Muscle Receiver https://www.anrcorp.com/product/r24-muscle-receiver/
- ANR Corp Wireless Muscle Sensor M40 https://www.anrcorp.com/product/m40-muscle-sense/

## Notes

The original design used a Raspberry Pi Zero, input/output controls, a screen, and muscle sensors. It was written in Python 3.7 using multiple libraries from adafruit, waveshare, and users on github. I will upload that version at some point as it was useful for gathering data in my walking gait and experimenting with different techniques for detecting when to bend the leg brace. For now, this is a simplified version targeted toward walking on even ground and can be built with minimal soldering and programming experience.

Once you have the device working, the next challenge will be to fit it on your leg without it moving around. A tight, secure fit is needed to ensure the brace moves your leg instead of moving *on* your leg. I attached the lower portion of the brace directly to my foot drop AFO but still have trouble with the thigh piece sliding around. You will have to experiment on your own to get it right. Good luck.

## Update 2023

Thanks to [ANR Corp](https://www.anrcorp.com/) sending me their muscle sensors and design help from their president, I was able to succesfully integrate muscle sensors into the latest design of the robotic leg. See the operation section for more information on how they operate. ~~I may experiement with more than one muscle sensor in the future.~~ I've started using two sensors, one on the good leg and one on the disabled one. This gives a better picture of my gait so that the brace can respond appropriately. How a short demo of the muscle sensor, watch this video: [https://youtu.be/r48ZZ4WN5bA](https://youtu.be/r48ZZ4WN5bA)
