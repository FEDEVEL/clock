# What is here
- Circuitpython (file adafruit-circuitpython-raspberry_pi_pico-en_US-9.2.7.uf2)
- Clock firmware source files (inside of RP2040 Files)
- Clock configuration website (RP2040 Files/clock_setup.html)

# To flash the firmware
## Flash this first - Circuitpython
Connect the board to USB and quickly press Reset button twice. The board will appear as RPI-RP2 storage. Copy adafruit-circuitpython-raspberry_pi_pico-en_US-9.2.7.uf2 file there. You need to do this only once.

## Updating the clock firmware
Before this, you need to have Circuitpython running on the clock board already (see the previous step). To update the clock software, folow these steps:
1. Hold USR1 button down and connect the board to USB
1. The board will be mounted as CIRCUITPY storage
1. Copy all the files from RP2040 Files directory to CIRCUITPY storage
