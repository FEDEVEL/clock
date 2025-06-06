# fdvl_buttons.py
import time
import digitalio # type: ignore

class Buttons:
    DEBOUNCE_TIME = 0.02  # 20ms
    SHORT_PRESS_TIME = 0.5  # Max time for short press
    LONG_PRESS_TIME = 1.0  # Min time for long press
    INIT_STABILIZE_TIME = 3.0  # 3s to stabilize pull-ups
    CONFIRM_COUNT = 3  # Number of readings to confirm state
    CONFIRM_INTERVAL = 0.01  # 10ms between readings
    DIAG_LOG_TIME = 0.0  # Disable diagnostic logs

    def __init__(self, bottom_pin, up_pin, down_pin):
        self.bottom = digitalio.DigitalInOut(bottom_pin)
        self.bottom.direction = digitalio.Direction.INPUT
        self.bottom.pull = digitalio.Pull.UP
        self.up = digitalio.DigitalInOut(up_pin)
        self.up.direction = digitalio.Direction.INPUT
        self.up.pull = digitalio.Pull.UP
        self.down = digitalio.DigitalInOut(down_pin)
        self.down.direction = digitalio.Direction.INPUT
        self.down.pull = digitalio.Pull.UP
        
        # Wait for pull-ups to stabilize
        time.sleep(self.INIT_STABILIZE_TIME)
        
        self.start_time = time.monotonic()
        # Validate initial states, retry if low
        self.last_state = {
            "bottom": False,#self.validate_initial_state(self.bottom, "BOTTOM"),
            "up": False,#self.validate_initial_state(self.up, "UP"),
            "down": False#self.validate_initial_state(self.down, "DOWN")
        }
        self.last_change = {"bottom": self.start_time, "up": self.start_time, "down": self.start_time}
        self.event = None
        self.bottom_press_start = 0
        self.was_pressed = {"bottom": False, "up": False, "down": False}
        print("Initial button states - BOTTOM: {}, UP: {}, DOWN: {}".format(
            self.last_state["bottom"], self.last_state["up"], self.last_state["down"]))
        self.is_bottom_holding = False

    # def validate_initial_state(self, pin, name):
    #     """Validate initial pin state, retry if low."""
    #     for _ in range(5):  # Try up to 5 times
    #         if self.confirm_state(pin, True):  # Expect high (not pressed)
    #             return True
    #         print("Warning: {} button initially low, retrying...".format(name))
    #         time.sleep(0.1)
    #     print("Error: {} button stuck low after retries".format(name))
    #     return False  # Default to not pressed to avoid false events

    def confirm_state(self, pin, expected_state):
        """Confirm pin state with multiple readings."""
        for _ in range(self.CONFIRM_COUNT):
            if pin.value != expected_state:
                return False
            time.sleep(self.CONFIRM_INTERVAL)
        return True

    def is_bottom_held(self):
        """Check if BOTTOM_BTN is held for >= 1s."""
        current_time = time.monotonic()
        current_state = not self.bottom.value  # Active low
        if current_state and self.last_state["bottom"] and not self.is_bottom_holding:
            self.bottom_press_start = current_time
            self.is_bottom_holding = True
        elif not current_state:
            self.bottom_press_start = 0
            self.is_bottom_holding = False
        return current_state and (current_time - self.bottom_press_start >= self.LONG_PRESS_TIME)

    def get_event(self):
        """Check for button events (short press)."""
        current_time = time.monotonic()
        event = None

        # Check BOTTOM_BTN
        current_state = not self.bottom.value  # Active low
        if current_state != self.last_state["bottom"]:
            if self.confirm_state(self.bottom, not current_state):
                if current_time - self.last_change["bottom"] > self.DEBOUNCE_TIME:
                    self.last_state["bottom"] = current_state
                    # if current_time - self.start_time < self.DIAG_LOG_TIME:
                    #     print("BOTTOM_BTN state changed to: {}".format("pressed" if current_state else "released"))
                    if current_state:
                        self.was_pressed["bottom"] = True
                        self.last_change["bottom"] = current_time
                    elif self.was_pressed["bottom"]:  # Released after being pressed
                        press_duration = current_time - self.last_change["bottom"]
                        if press_duration < self.SHORT_PRESS_TIME:
                            event = "BOTTOM_SHORT"
                        self.was_pressed["bottom"] = False
        
        # Check UP_BTN
        current_state = not self.up.value
        if current_state != self.last_state["up"]:
            if self.confirm_state(self.up, not current_state):
                if current_time - self.last_change["up"] > self.DEBOUNCE_TIME:
                    self.last_state["up"] = current_state
                    # if current_time - self.start_time < self.DIAG_LOG_TIME:
                    #     print("UP_BTN state changed to: {}".format("pressed" if current_state else "released"))
                    if current_state:
                        self.was_pressed["up"] = True
                        self.last_change["up"] = current_time
                    elif self.was_pressed["up"]:
                        press_duration = current_time - self.last_change["up"]
                        if press_duration < self.SHORT_PRESS_TIME:
                            event = "UP_SHORT"
                        self.was_pressed["up"] = False
        
        # Check DOWN_BTN
        current_state = not self.down.value
        if current_state != self.last_state["down"]:
            if self.confirm_state(self.down, not current_state):
                if current_time - self.last_change["down"] > self.DEBOUNCE_TIME:
                    self.last_state["down"] = current_state
                    # if current_time - self.start_time < self.DIAG_LOG_TIME:
                    #     print("DOWN_BTN state changed to: {}".format("pressed" if current_state else "released"))
                    if current_state:
                        self.was_pressed["down"] = True
                        self.last_change["down"] = current_time
                    elif self.was_pressed["down"]:
                        press_duration = current_time - self.last_change["down"]
                        if press_duration < self.SHORT_PRESS_TIME:
                            event = "DOWN_SHORT"
                        self.was_pressed["down"] = False
        
        self.event = event
        return event