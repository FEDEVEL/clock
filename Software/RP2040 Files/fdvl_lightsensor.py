# fdvl_lightsensor.py
import analogio # type: ignore

class LightSensor:
    # Brightness thresholds
    BRIGHT_THRESHOLD = 30000
    DARK_THRESHOLD = 49000

    def __init__(self, adc_pin, light_sensor_bright_threshold, light_sensor_dark_threshold):
        self.adc = analogio.AnalogIn(adc_pin)
        self.BRIGHT_THRESHOLD = light_sensor_bright_threshold
        self.DARK_THRESHOLD = light_sensor_dark_threshold

    def update_thresholds(self, bright, dark):
        self.BRIGHT_THRESHOLD = bright
        self.DARK_THRESHOLD = dark

    def get_brightness(self):
        """Determine brightness mode based on light sensor."""
        value = self.adc.value
        if value < self.BRIGHT_THRESHOLD:
            return "BRIGHT"
        elif value > self.DARK_THRESHOLD:
            return "DARK"
        return "NORMAL"