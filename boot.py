import board
import digitalio
import storage
import usb_cdc

# Set up the button pin
button = digitalio.DigitalInOut(board.GP15)
button.switch_to_input(pull=digitalio.Pull.UP)

# Enable serial always
usb_cdc.enable(console=True, data=True)

# If the button is pressed at boot, enable USB drive
if not button.value:  # Button pulled low (pressed)
    storage.enable_usb_drive()
else:
    storage.disable_usb_drive()