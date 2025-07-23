# fdvl_rtc.py
import busio # type: ignore
import time

class RTC:
    MAX31343_I2C_ADDRESS = 0x68
    MAX31343_R_SECONDS = 0x06

    def __init__(self, scl_pin, sda_pin):
        self.i2c = busio.I2C(scl_pin, sda_pin)

    def bcd2bin(self, val):
        """Convert BCD to binary."""
        return (val & 0x0F) + ((val >> 4) * 10)

    def bin2bcd(self, val):
        """Convert binary to BCD."""
        return ((val // 10) << 4) | (val % 10)

    def get_time(self):
        """Read time and date from MAX31343, retry once if failed."""
        for _ in range(2):
            if self.i2c.try_lock():
                try:
                    write_buf = bytearray([self.MAX31343_R_SECONDS])
                    read_buf = bytearray(7)
                    self.i2c.writeto_then_readfrom(self.MAX31343_I2C_ADDRESS, write_buf, read_buf)
                    
                    seconds = self.bcd2bin(read_buf[0] & 0x7F)
                    minutes = self.bcd2bin(read_buf[1] & 0x7F)
                    hours = self.bcd2bin(read_buf[2] & 0x3F)
                    day = self.bcd2bin(read_buf[3] & 0x07) - 1
                    date = self.bcd2bin(read_buf[4] & 0x3F)
                    month = self.bcd2bin(read_buf[5] & 0x1F) - 1
                    century = (read_buf[5] & 0x80) >> 7
                    year = self.bcd2bin(read_buf[6])
                    base_year = 2000 if century else 1900
                    full_year = base_year + year
                    
                    return {
                        'tm_sec': seconds,
                        'tm_min': minutes,
                        'tm_hour': hours,
                        'tm_wday': day,
                        'tm_mday': date,
                        'tm_mon': month,
                        'tm_year': full_year,
                        'tm_yday': 0,
                        'tm_isdst': 0
                    }
                finally:
                    self.i2c.unlock()
            time.sleep(0.1)
        return None

    def set_time(self, time_dict):
        """Set RTC time in BCD format."""
        if self.i2c.try_lock():
            try:
                write_buf = bytearray(8)
                write_buf[0] = self.MAX31343_R_SECONDS
                write_buf[1] = self.bin2bcd(time_dict['tm_sec'])
                write_buf[2] = self.bin2bcd(time_dict['tm_min'])
                write_buf[3] = self.bin2bcd(time_dict['tm_hour'])
                write_buf[4] = self.bin2bcd(time_dict['tm_wday'] + 1)
                write_buf[5] = self.bin2bcd(time_dict['tm_mday'])
                write_buf[6] = self.bin2bcd(time_dict['tm_mon'] + 1)
                if time_dict['tm_year'] >= 2000:
                    write_buf[6] |= 0x80  # Set century bit
                    write_buf[7] = self.bin2bcd(time_dict['tm_year'] - 2000)
                else:
                    write_buf[7] = self.bin2bcd(time_dict['tm_year'] - 1900)
                self.i2c.writeto(self.MAX31343_I2C_ADDRESS, write_buf)
            finally:
                self.i2c.unlock()