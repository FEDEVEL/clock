# fdvl_display.py
import neopixel # type: ignore
import math

class Display:
    # Brightness settings
    BRIGHT_BRIGHTNESS = 0.1
    NORMAL_BRIGHTNESS = 0.05
    DARK_BRIGHTNESS = 0.02
    OFF_BRIGHTNESS = 0.01

    # LED Configuration
    NUM_LEDS_CHAIN1 = 28  # LED201-LED228
    NUM_LEDS_CHAIN2 = 3   # LED229-LED231
    PIXEL_ORDER = "GRB"
    DEFAULT_COLOR = (50, 100, 25)
    TIMER_POSITIVE_COLOR = (0, 0, 255)
    TIMER_NEGATIVE_COLOR = (255, 0, 0)
    STOPWATCH_COLOR = (255, 255, 0)
    NIGHT_COLOR = (255, 0, 0) #RGB NIGHT MODE COLOR
    NIGHT_COLOR_HOURS_START = 22 #HOUR OF NIGHT MODE START, INCLUDING
    NIGHT_COLOR_MINUTES_START = 0 #MINUTE OF NIGHT MODE START, INCLUDING
    NIGHT_COLOR_HOURS_END = 5 #HOUR OF NIGHT MODE END, INCLUDING
    NIGHT_COLOR_MINUTES_END = 0 #MINUTE OF NIGHT MODE START, INCLUDING
    OFF = (0, 0, 0)
    DOTS_ALWAYS_ON = True

    def update_settings(self, settings):
        # Update brightness levels
        self.BRIGHT_BRIGHTNESS = settings.get("bright_brightness", self.BRIGHT_BRIGHTNESS)
        self.NORMAL_BRIGHTNESS = settings.get("normal_brightness", self.NORMAL_BRIGHTNESS)
        self.DARK_BRIGHTNESS = settings.get("dark_brightness", self.DARK_BRIGHTNESS)
        self.OFF_BRIGHTNESS = settings.get("off_brightness", self.OFF_BRIGHTNESS)

        # Update colors
        self.DEFAULT_COLOR = tuple(settings.get("default_color", self.DEFAULT_COLOR))
        self.TIMER_POSITIVE_COLOR = tuple(settings.get("TIMER_POSITIVE_COLOR", self.TIMER_POSITIVE_COLOR))
        self.TIMER_NEGATIVE_COLOR = tuple(settings.get("TIMER_NEGATIVE_COLOR", self.TIMER_NEGATIVE_COLOR))
        self.STOPWATCH_COLOR = tuple(settings.get("STOPWATCH_COLOR", self.STOPWATCH_COLOR))
        self.NIGHT_COLOR = tuple(settings.get("night_color", self.NIGHT_COLOR))

        # Night mode time
        self.NIGHT_COLOR_HOURS_START = settings.get("night_color_hours_start", self.NIGHT_COLOR_HOURS_START)
        self.NIGHT_COLOR_MINUTES_START = settings.get("night_color_minutes_start", self.NIGHT_COLOR_MINUTES_START)
        self.NIGHT_COLOR_HOURS_END = settings.get("night_color_hours_end", self.NIGHT_COLOR_HOURS_END)
        self.NIGHT_COLOR_MINUTES_END = settings.get("night_color_minutes_end", self.NIGHT_COLOR_MINUTES_END)

        # Dots always on
        self.DOTS_ALWAYS_ON = settings.get("dots_always_on", self.DOTS_ALWAYS_ON)

    # Seven-segment patterns (a, b, c, d, e, f, g)
    DIGIT_PATTERNS = {
        0: [1, 1, 1, 1, 1, 1, 0],
        1: [0, 1, 1, 0, 0, 0, 0],
        2: [1, 1, 0, 1, 1, 0, 1],
        3: [1, 1, 1, 1, 0, 0, 1],
        4: [0, 1, 1, 0, 0, 1, 1],
        5: [1, 0, 1, 1, 0, 1, 1],
        6: [1, 0, 1, 1, 1, 1, 1],
        7: [1, 1, 1, 0, 0, 0, 0],
        8: [1, 1, 1, 1, 1, 1, 1],
        9: [1, 1, 1, 1, 0, 1, 1],
        '-': [0, 0, 0, 0, 0, 0, 1]  # Middle bar for negative sign
    }
    SEGMENT_OFFSETS = [3, 4, 6, 0, 1, 2, 5]  # a, b, c, d, e, f, g

    def __init__(self, pin1, pin2):
        self.pixels1 = neopixel.NeoPixel(pin1, self.NUM_LEDS_CHAIN1, pixel_order=self.PIXEL_ORDER, auto_write=False)
        self.pixels2 = neopixel.NeoPixel(pin2, self.NUM_LEDS_CHAIN2, pixel_order=self.PIXEL_ORDER, auto_write=False)
        self.brightness = self.NORMAL_BRIGHTNESS

    def set_brightness(self, mode):
        """Set display brightness based on mode."""
        if mode == "BRIGHT":
            self.brightness = self.BRIGHT_BRIGHTNESS
        elif mode == "NORMAL":
            self.brightness = self.NORMAL_BRIGHTNESS
        elif mode == "DARK":
            self.brightness = self.DARK_BRIGHTNESS
        elif mode == "OFF":
            self.brightness = self.OFF_BRIGHTNESS
        self.pixels1.brightness = self.brightness
        self.pixels2.brightness = self.brightness

    def display_digit(self, pixels, digit, start_idx, color):
        """Display a digit or symbol on a seven-segment display."""
        pattern = self.DIGIT_PATTERNS.get(digit, [0] * 7)
        for i, on in enumerate(pattern):
            led_idx = start_idx + self.SEGMENT_OFFSETS[i]
            pixels[led_idx] = color if on else self.OFF

    def hsv_to_rgb(self, h, s=1.0, v=1.0):
        """Convert HSV to RGB (0-255 range)."""
        if s == 0.0:
            return (int(v * 255), int(v * 255), int(v * 255))
        i = int(h * 6.0)
        f = (h * 6.0) - i
        p = v * (1.0 - s)
        q = v * (1.0 - s * f)
        t = v * (1.0 - s * (1.0 - f))
        i = i % 6
        if i == 0:
            return (int(v * 255), int(t * 255), int(p * 255))
        if i == 1:
            return (int(q * 255), int(v * 255), int(p * 255))
        if i == 2:
            return (int(p * 255), int(v * 255), int(t * 255))
        if i == 3:
            return (int(p * 255), int(q * 255), int(v * 255))
        if i == 4:
            return (int(t * 255), int(p * 255), int(v * 255))
        if i == 5:
            return (int(v * 255), int(p * 255), int(q * 255))
        return (0, 0, 0)

    def show_time(self, rtc_time, swo_state, brightness_mode):
        """Display HH:MM with double dot based on SWO."""
        if not rtc_time:
            return
        hours = rtc_time['tm_hour']
        minutes = rtc_time['tm_min']
        h_tens = hours // 10
        h_units = hours % 10
        m_tens = minutes // 10
        m_units = minutes % 10

        color = self.DEFAULT_COLOR
        if hours >= self.NIGHT_COLOR_HOURS_START and hours <= self.NIGHT_COLOR_HOURS_END and minutes >= self.NIGHT_COLOR_MINUTES_START and minutes <= self.NIGHT_COLOR_MINUTES_END:
            color = self.NIGHT_COLOR

        if self.DOTS_ALWAYS_ON:
            swo_state = 1

        self.set_brightness(brightness_mode)
        self.display_digit(self.pixels1, h_tens, 0, color)
        self.display_digit(self.pixels1, h_units, 7, color)
        self.display_digit(self.pixels1, m_tens, 14, color)
        self.display_digit(self.pixels1, m_units, 21, color)
        dot_color = color if swo_state else self.OFF
        self.pixels2[0] = dot_color  # LED229
        self.pixels2[1] = dot_color  # LED230
        self.pixels2[2] = self.OFF   # LED231
        self.pixels1.show()
        self.pixels2.show()

    def show_timer(self, seconds, swo_state, brightness_mode):
        """Display timer in MM:SS or HH:MM with appropriate colors."""
        abs_seconds = abs(seconds)
        is_negative = seconds < 0
        color = self.TIMER_NEGATIVE_COLOR if is_negative else self.TIMER_POSITIVE_COLOR

        if abs_seconds <= 3599:  # MM:SS (up to 59:59)
            minutes = abs_seconds // 60
            secs = abs_seconds % 60
            m_tens = minutes // 10
            m_units = minutes % 10
            s_tens = secs // 10
            s_units = secs % 10
            self.set_brightness(brightness_mode)
            if is_negative and minutes < 10:
                self.display_digit(self.pixels1, '-', 0, color)  # Negative sign
            else:
                self.display_digit(self.pixels1, m_tens, 0, color)
            self.display_digit(self.pixels1, m_units, 7, color)
            self.display_digit(self.pixels1, s_tens, 14, color)
            self.display_digit(self.pixels1, s_units, 21, color)
            self.pixels2[0] = color  # LED229 always on
            self.pixels2[1] = color  # LED230 always on
        else:  # HH:MM (after 59:59)
            hours = abs_seconds // 3600
            minutes = (abs_seconds % 3600) // 60
            h_tens = hours // 10
            h_units = hours % 10
            m_tens = minutes // 10
            m_units = minutes % 10
            self.set_brightness(brightness_mode)
            if is_negative and hours < 10:
                self.display_digit(self.pixels1, '-', 0, color)  # Negative sign
            else:
                self.display_digit(self.pixels1, h_tens, 0, color)
            self.display_digit(self.pixels1, h_units, 7, color)
            self.display_digit(self.pixels1, m_tens, 14, color)
            self.display_digit(self.pixels1, m_units, 21, color)
            dot_color = color if swo_state else self.OFF
            self.pixels2[0] = dot_color  # LED229 flashes with SWO
            self.pixels2[1] = dot_color  # LED230 flashes with SWO
        self.pixels2[2] = self.OFF  # LED231 always off
        self.pixels1.show()
        self.pixels2.show()

    def show_stopwatch(self, seconds, swo_state, brightness_mode):
        """Display stopwatch in MM:SS or HH:MM with YELLOW color."""
        if seconds < 0:
            seconds = 0  # Stopwatch doesn't go negative
        if seconds <= 3599:  # MM:SS (up to 59:59)
            minutes = seconds // 60
            secs = seconds % 60
            m_tens = minutes // 10
            m_units = minutes % 10
            s_tens = secs // 10
            s_units = secs % 10
            self.set_brightness(brightness_mode)
            self.display_digit(self.pixels1, m_tens, 0, self.STOPWATCH_COLOR)
            self.display_digit(self.pixels1, m_units, 7, self.STOPWATCH_COLOR)
            self.display_digit(self.pixels1, s_tens, 14, self.STOPWATCH_COLOR)
            self.display_digit(self.pixels1, s_units, 21, self.STOPWATCH_COLOR)
            self.pixels2[0] = self.STOPWATCH_COLOR  # LED229 always on
            self.pixels2[1] = self.STOPWATCH_COLOR  # LED230 always on
        else:  # HH:MM (after 59:59)
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            h_tens = hours // 10
            h_units = hours % 10
            m_tens = minutes // 10
            m_units = minutes % 10
            self.set_brightness(brightness_mode)
            self.display_digit(self.pixels1, h_tens, 0, self.STOPWATCH_COLOR)
            self.display_digit(self.pixels1, h_units, 7, self.STOPWATCH_COLOR)
            self.display_digit(self.pixels1, m_tens, 14, self.STOPWATCH_COLOR)
            self.display_digit(self.pixels1, m_units, 21, self.STOPWATCH_COLOR)
            dot_color = self.STOPWATCH_COLOR if swo_state else self.OFF
            self.pixels2[0] = dot_color  # LED229 flashes with SWO
            self.pixels2[1] = dot_color  # LED230 flashes with SWO
        self.pixels2[2] = self.OFF  # LED231 always off
        self.pixels1.show()
        self.pixels2.show()

    def show_time_with_effect(self, rtc_time, swo_state, effect_time):
        """Display HH:MM with snake rainbow effect."""
        if not rtc_time:
            return
        hours = rtc_time['tm_hour']
        minutes = rtc_time['tm_min']
        h_tens = hours // 10
        h_units = hours % 10
        m_tens = minutes // 10
        m_units = minutes % 10

        # Get active LEDs
        active_leds = []
        patterns = [
            self.DIGIT_PATTERNS.get(h_tens, [0] * 7),
            self.DIGIT_PATTERNS.get(h_units, [0] * 7),
            self.DIGIT_PATTERNS.get(m_tens, [0] * 7),
            self.DIGIT_PATTERNS.get(m_units, [0] * 7)
        ]
        # Display 1: LED201-LED207 (0-6)
        for i, on in enumerate(patterns[0]):
            if on:
                active_leds.append((1, self.SEGMENT_OFFSETS[i]))
        # Display 2: LED208-LED214 (7-13)
        for i, on in enumerate(patterns[1]):
            if on:
                active_leds.append((1, 7 + self.SEGMENT_OFFSETS[i]))
        # Display 3: LED215-LED221 (14-20)
        for i, on in enumerate(patterns[2]):
            if on:
                active_leds.append((1, 14 + self.SEGMENT_OFFSETS[i]))
        # Display 4: LED222-LED228 (21-27)
        for i, on in enumerate(patterns[3]):
            if on:
                active_leds.append((1, 21 + self.SEGMENT_OFFSETS[i]))
        # Double dot: LED229, LED230
        if swo_state:
            active_leds.append((2, 0))
            active_leds.append((2, 1))

        # Generate rainbow colors
        num_leds = len(active_leds)
        if num_leds == 0:
            return
        colors = []
        for i in range(num_leds):
            hue = (i / num_leds + effect_time) % 1.0
            colors.append(self.hsv_to_rgb(hue))

        # Order: D4 -> D3 -> LED230 -> LED229 -> D2 -> D1 -> LED231
        display_order = [3, 2, -2, -1, 1, 0, -3]  # -1=LED229, -2=LED230, -3=LED231
        segment_order = [6, 5, 4, 3, 2, 1, 0]  # c -> g -> b -> a -> f -> e -> d
        led_map = []
        for disp_idx in display_order:
            if disp_idx >= 0:  # Display
                start_idx = disp_idx * 7
                pattern = patterns[disp_idx]
                for seg_idx in segment_order:
                    if pattern[seg_idx]:
                        led_map.append((1, start_idx + self.SEGMENT_OFFSETS[seg_idx]))
            else:  # Dots
                if disp_idx == -1 and swo_state:
                    led_map.append((2, 0))  # LED229
                elif disp_idx == -2 and swo_state:
                    led_map.append((2, 1))  # LED230
                elif disp_idx == -3:
                    pass  # LED231 not used

        # Apply colors with shift
        shift = int(effect_time * num_leds) % num_leds
        for i, (chain, idx) in enumerate(led_map):
            color_idx = (i + shift) % num_leds
            if chain == 1:
                self.pixels1[idx] = colors[color_idx]
            else:
                self.pixels2[idx] = colors[color_idx]

        # Clear unused LEDs
        for i in range(self.NUM_LEDS_CHAIN1):
            if (1, i) not in led_map:
                self.pixels1[i] = self.OFF
        for i in range(self.NUM_LEDS_CHAIN2):
            if (2, i) not in led_map:
                self.pixels2[i] = self.OFF

        self.set_brightness("NORMAL")  # Effect uses normal brightness
        self.pixels1.show()
        self.pixels2.show()