# code.py # type: ignore
import time
import board
import digitalio
import pwmio
from fdvl_display import Display
from fdvl_rtc import RTC
from fdvl_buttons import Buttons
from fdvl_lightsensor import LightSensor
import usb_cdc
import json


#WATCHDOG
#from microcontroller import watchdog
#from watchdog import WatchDogMode
#watchdog.timeout=30 # Set a timeout of 30 seconds
#watchdog.mode = WatchDogMode.RESET

# Constants
CLOCK_MODE = "CLOCK_MODE"
TIMER_MODE = "TIMER_MODE"
STOPWATCH_MODE = "STOPWATCH_MODE"
STOPWATCH_COUNTING = "STOPWATCH_COUNTING"
STOPWATCH_PAUSED = "STOPWATCH_PAUSED"
REFRESH_INTERVAL = 1.0 / 60  # 60 Hz
SETTLE_PERIOD = 4.0  # Seconds to ignore button events after power-up
RTC_UPDATE_INTERVAL = 1.0  # Seconds between RTC reads
SETTINGS_FILE = "/settings.txt"

# Load settings from settings.txt
def load_settings():
    try:
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print("Failed to load settings.txt:", e)
        return {}
    
def save_settings():
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f)
            print("Settings saved.")
    except Exception as e:
        print("Failed to save settings:", e)

def apply_settings():
    # Update buzzer frequency
    global buzzer
    try:
        buzzer.deinit()
    except Exception:
        pass

    try:
        buzzer = pwmio.PWMOut(board.A3, frequency=settings["buzzer_frequency"], duty_cycle=0)
        print("Buzzer reinitialized with new frequency.")
    except Exception as e:
        print("Failed to reinitialize buzzer:", e)

    # Update light sensor thresholds
    try:
        light_sensor.update_thresholds(settings["light_sensor_bright_threshold"], settings["light_sensor_dark_threshold"])
        print("Updated light sensor thresholds.")
    except Exception as e:
        print("Failed to update light sensor:", e)

    # Update light sensor thresholds
    try:
        display.update_settings(settings)
        print("Updated display values.")
    except Exception as e:
        print("Failed to update display:", e)

        


# === Default Config ===
settings = load_settings()


BUZZER_CYCLE_TIME = settings.get("buzzer_beep_duration") + settings.get("buzzer_stop_duration") * 2 + settings.get("buzzer_beep_duration") + settings.get("buzzer_pause_duration")  # s per cycle
print(settings)

#SETUP SERIAL COMMUNICATION
data_serial = usb_cdc.data
data_serial.timeout = 0  # Non-blocking reads

def read_line():
    line = b""
    while True:
        if data_serial.in_waiting > 0:
            char = data_serial.read(1)
            if char == b"\n":
                return line.decode().strip()
            else:
                line += char

def handle_command(line):
    global settings
    try:
        data = json.loads(line)

        cmd = data.get("command")

        if cmd == "set_time":
            rtc.set_time({
                'tm_year': data['tm_year'],
                'tm_mon': data['tm_mon'],
                'tm_mday': data['tm_mday'],
                'tm_hour': data['tm_hour'],
                'tm_min': data['tm_min'],
                'tm_sec': data['tm_sec'],
                'tm_wday': data['tm_wday']
            })
            print("RTC time updated via serial command.")

        elif cmd == "get_settings":
            print("Get settings received")
            # Send current settings back to serial as JSON
            json_data = json.dumps({"settings": settings}) + "\n"
            data_serial.write(json_data.encode("utf-8"))

        else:
            # Assume full settings update
            settings = data
            save_settings()
            print("Settings updated:", settings)
            apply_settings()

    except Exception as e:
        print("JSON parse error:", e)


# Initialize button pins first to stabilize pull-ups
buttons = Buttons(board.GP15, board.GP14, board.GP13)  # BOTTOM, UP, DOWN

# Initialize other peripherals
rtc = RTC(board.GP11, board.GP10)  # SCL=GP11, SDA=GP10
display = Display(board.GP18, board.GP28)
light_sensor = LightSensor(board.GP27, settings.get("light_sensor_bright_threshold"), settings.get("light_sensor_dark_threshold"))  # Light sensor on GPIO27 (ADC1)
buzzer = pwmio.PWMOut(board.A3, frequency=settings.get("buzzer_frequency"), duty_cycle=0)  # Buzzer on GPIO29 (A3)

apply_settings()

# Initialize SWO (CLK_1HZ)
swo = digitalio.DigitalInOut(board.GP9)  # SWO on GPIO9
swo.direction = digitalio.Direction.INPUT
swo.pull = digitalio.Pull.UP

# Get initial time and set if invalid
rtc_time = rtc.get_time()
if rtc_time:
    if rtc_time['tm_year'] < 2025:
        print("Invalid RTC time detected, setting to 2025-05-29 13:21:00")
        rtc.set_time({
            'tm_year': 2025, 'tm_mon': 4, 'tm_mday': 30,
            'tm_hour': 6, 'tm_min': 55, 'tm_sec': 0,
            'tm_wday': 4  # 
        })
        time.sleep(0.1)  # Brief delay to ensure RTC settles
        rtc_time = rtc.get_time()
    print("Initialization complete. Initial time: {:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        rtc_time['tm_year'], rtc_time['tm_mon'] + 1, rtc_time['tm_mday'],
        rtc_time['tm_hour'], rtc_time['tm_min'], rtc_time['tm_sec']))
else:
    print("Initialization failed: Could not read RTC")

# State: Default to CLOCK_MODE after pin initialization
mode = CLOCK_MODE
sub_mode = None
last_swo = False
last_swo_change = 0
#last_midnight_check = 0
last_rtc_update = time.monotonic()
effect_active = False
effect_start = 0
buzzer_cycle = 0  # Track buzzer cycle (0 to settings.get("buzzer_max_cycles")-1)
buzzer_state = None  # Track buzzer state (Beep1, Stop1, Beep2, Stop2, Beep3, Pause)
buzzer_state_start = 0  # Track start time of current buzzer state
timer_seconds = 5  # Initial timer value
timer_last_update = 0
stopwatch_seconds = 0  # Stopwatch display value
stopwatch_background_seconds = 0  # Background counting
paused_time = 0  # Time when paused
stopwatch_last_update = 0
start_time = time.monotonic()
settle_confirmed = False
print("Entering mode: {}".format(mode))

# loop_count = 0
# last_time = time.monotonic()

# Main loop
while True:
    #loop_count += 1
    current_time = time.monotonic()

    # Check for new settings via serial
    if data_serial.in_waiting > 0:
        command = read_line()
        handle_command(command)

    # if current_time - last_time >= 1.0:
    #     print("Loop frequency:", loop_count, "Hz")
    #     loop_count = 0
    #     last_time = current_time
    
    # Confirm CLOCK_MODE after settle period (once)
    if not settle_confirmed and current_time - start_time > SETTLE_PERIOD:
        print("Confirmed: Remained in CLOCK_MODE after settle period")
        settle_confirmed = True

    # Update RTC time periodically
    if mode == CLOCK_MODE and current_time - last_rtc_update >= RTC_UPDATE_INTERVAL:
        new_time = rtc.get_time()
        if new_time:
            rtc_time = new_time
        last_rtc_update = current_time

    # Read buttons, ignore events during settle period
    button_event = None
    if current_time - start_time > SETTLE_PERIOD:
        button_event = buttons.get_event()

    # Process button events
    if button_event:
        if mode == CLOCK_MODE:
            if button_event == "DOWN_SHORT":
                mode = TIMER_MODE
                timer_seconds = 5
                timer_last_update = current_time
                print("Entering mode: {}".format(mode))
            elif button_event == "UP_SHORT":
                mode = STOPWATCH_MODE
                sub_mode = STOPWATCH_COUNTING
                stopwatch_seconds = 0
                stopwatch_background_seconds = 0
                paused_time = 0
                stopwatch_last_update = current_time
                print("Entering mode: {} ({})".format(mode, sub_mode))
            elif button_event == "BOTTOM_SHORT":
                effect_active = True
                effect_start = current_time
                buzzer_cycle = 0
                buzzer_state = "Beep1"
                buzzer_state_start = current_time
                buzzer.duty_cycle = 32768  # Start first beep
                print("CLOCK_MODE: Starting snake rainbow effect with buzzer")
        elif mode == TIMER_MODE:
            if button_event == "BOTTOM_SHORT":
                mode = CLOCK_MODE
                print("Entering mode: {}".format(mode))
            elif button_event == "DOWN_SHORT":
                timer_seconds += 5
                print("TIMER_MODE: Added 5 seconds, new time: {} seconds".format(timer_seconds))
            elif button_event == "UP_SHORT":
                timer_seconds += 60
                print("TIMER_MODE: Added 1 minute, new time: {} seconds".format(timer_seconds))
        elif mode == STOPWATCH_MODE:
            if button_event == "BOTTOM_SHORT":
                mode = CLOCK_MODE
                print("Entering mode: {}".format(mode))
            elif button_event == "UP_SHORT":
                if sub_mode == STOPWATCH_COUNTING:
                    stopwatch_seconds = 0
                    stopwatch_background_seconds = 0
                    stopwatch_last_update = current_time
                    print("STOPWATCH_MODE: Reset to 00:00, mode: {}".format(sub_mode))
                elif sub_mode == STOPWATCH_PAUSED:
                    sub_mode = STOPWATCH_COUNTING
                    stopwatch_seconds = stopwatch_background_seconds
                    paused_time = 0
                    print("STOPWATCH_MODE: Resumed from background time, mode: {}".format(sub_mode))
            elif button_event == "DOWN_SHORT":
                if sub_mode == STOPWATCH_COUNTING:
                    sub_mode = STOPWATCH_PAUSED
                    paused_time = stopwatch_seconds
                    print("STOPWATCH_MODE: Paused at {:02d}:{:02d}, mode: {}".format(
                        paused_time // 60, paused_time % 60, sub_mode))
                elif sub_mode == STOPWATCH_PAUSED:
                    sub_mode = STOPWATCH_COUNTING
                    stopwatch_seconds = paused_time
                    print("STOPWATCH_MODE: Resumed from paused time, mode: {}".format(sub_mode))
    
    # Handle buzzer pattern during rainbow effect
    if effect_active:
        elapsed = current_time - buzzer_state_start
        cycle_elapsed = current_time - effect_start - (buzzer_cycle * BUZZER_CYCLE_TIME)
        
        if buzzer_cycle < settings.get("buzzer_max_cycles"):
            if buzzer_state == "Beep1" and elapsed >= settings.get("buzzer_beep_duration"):
                buzzer.duty_cycle = 0
                buzzer_state = "Stop1"
                buzzer_state_start = current_time
            elif buzzer_state == "Stop1" and elapsed >= settings.get("buzzer_stop_duration"):
                buzzer.duty_cycle = 32768
                buzzer_state = "Beep2"
                buzzer_state_start = current_time
            elif buzzer_state == "Beep2" and elapsed >= settings.get("buzzer_beep_duration"):
                buzzer.duty_cycle = 0
                buzzer_state = "Stop2"
                buzzer_state_start = current_time
            elif buzzer_state == "Stop2" and elapsed >= settings.get("buzzer_stop_duration"):
                buzzer.duty_cycle = 32768
                buzzer_state = "Beep3"
                buzzer_state_start = current_time
            elif buzzer_state == "Beep3" and elapsed >= settings.get("buzzer_beep_duration"):
                buzzer.duty_cycle = 0
                buzzer_state = "Pause"
                buzzer_state_start = current_time
            elif buzzer_state == "Pause" and elapsed >= settings.get("buzzer_pause_duration"):
                buzzer_cycle += 1
                if buzzer_cycle < settings.get("buzzer_max_cycles"):
                    buzzer.duty_cycle = 32768
                    buzzer_state = "Beep1"
                    buzzer_state_start = current_time
        
        # End effect after 5 seconds
        if current_time - effect_start >= 5:
            effect_active = False
            buzzer.duty_cycle = 0  # Ensure buzzer is off
            print("CLOCK_MODE: Snake rainbow effect ended")
    
    # # Check for midnight (once per minute)
    # if current_time - last_midnight_check >= 60:
    #     if rtc_time and rtc_time['tm_hour'] == 0 and rtc_time['tm_min'] == 0:
    #         new_time = rtc.get_time()
    #         if new_time:
    #             rtc_time = new_time
    #             print("Midnight sync: {:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
    #                 rtc_time['tm_year'], rtc_time['tm_mon'] + 1, rtc_time['tm_mday'],
    #                 rtc_time['tm_hour'], rtc_time['tm_min'], rtc_time['tm_sec']))
    #     last_midnight_check = current_time
    
    # Synchronize timer and stopwatch with SWO
    swo_state = swo.value
    if swo_state and not last_swo and current_time - last_swo_change > 0.1:
        if mode == TIMER_MODE:
            timer_seconds -= 1
            timer_last_update = current_time
            if timer_seconds == 0:
                print("TIMER_MODE: Timer reached zero")
            elif timer_seconds == -1:
                print("TIMER_MODE: Timer entered negative time")
        elif mode == STOPWATCH_MODE:
            stopwatch_background_seconds += 1
            if sub_mode == STOPWATCH_COUNTING:
                stopwatch_seconds += 1
            stopwatch_last_update = current_time
    
    # Update SWO state
    if swo_state != last_swo:
        last_swo = swo_state
        last_swo_change = current_time

    brightness = light_sensor.get_brightness()
    # Update display
    if mode == CLOCK_MODE:
        if effect_active:
            display.show_time_with_effect(rtc_time, swo_state, current_time - effect_start)
        else:
            display.show_time(rtc_time, swo_state, brightness)
    elif mode == TIMER_MODE:
        if buttons.is_bottom_held():
            display.show_time(rtc_time, swo_state, brightness)
            print("TIMER_MODE: Showing clock time during BOTTOM_BTN hold")
        else:
            display.show_timer(timer_seconds, swo_state, brightness)
    elif mode == STOPWATCH_MODE:
        if buttons.is_bottom_held():
            display.show_time(rtc_time, swo_state, brightness)
            print("STOPWATCH_MODE: Showing clock time during BOTTOM_BTN hold")
        else:
            display_seconds = paused_time if sub_mode == STOPWATCH_PAUSED else stopwatch_seconds
            display.show_stopwatch(display_seconds, swo_state, brightness)

    #watchdog.feed()
    time.sleep(REFRESH_INTERVAL)