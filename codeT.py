# code.py # type: ignore
import time
import board
import neopixel
#from fdvl_display_test import Display

loop_count = 0
#last_time = time.monotonic()

#display = Display(board.GP18, board.GP28)
pixels = neopixel.NeoPixel(board.GP18, 28, brightness=1)  # 1 = number of LEDs

while True:
    loop_count += 1
    if loop_count %2 == 0:
        pixels.fill((0, 1, 0))  # Set all to green
    else:
        pixels.fill((0, 0, 0))  # Set all to green
    # current_time = time.monotonic()

    # if current_time - last_time >= 1.0:
    #     #print("Loop frequency:", loop_count, "Hz")
    #     loop_count = 0
    #     last_time = current_time
