class PM_PM5020:
    
    def open(self, rm):
        try:
            self.pm = rm.open_resource('USB0::0x1313::0x80BB::M00932473::INSTR')
        except:
            print("Failed to connect to Power Meter. Verify Address")
            exit()
    
    def get_units(self, channel: int) -> str:
        assert channel != 1 or channel != 2, "Unexpected channel"
        return self.pm.query(f"SENS{channel}:POW:UNIT?")
    
    def set_units(self, channel: int, unit: str):
        assert channel != 1 or channel != 2, "Unexpected channel"
        assert unit.upper() != "W" or unit.upper() != "dBm", "Unexpected unit"
        self.pm.write(f"SENS{channel}:POW:UNIT {unit}")
    
    def get_range(self, channel: int) -> float:
        assert channel != 1 or channel != 2, "Unexpected channel"
        return float(self.pm.query(f"SENS{channel}:POW:RANGE?"))
    
    def set_range(self, channel: int, range: float):
        assert channel != 1 or channel != 2, "Unexpected channel"
        self.pm.write(f"SENS{channel}:POW:RANGE {range}")
    
    def get_power(self, channel: int) -> float:
        assert channel != 1 or channel != 2, "Unexpected channel"
        self.pm.write("INIT{channel}:IMM")
        return float(self.pm.query(f"MEAS{channel}:POW?"))
    
    def configure_sense_power(self):
        self.pm.write("CONF:POW")

    def set_autorange(self, channel: int, auto: int):
        assert channel != 1 or channel != 2, "Unexpected channel"
        self.pm.write(f"SENS{channel}:POW:RANGE:AUTO {auto}")

    def get_autorange(self, channel: int) -> int:
        assert channel != 1 or channel != 2, "Unexpected channel"
        return int(self.pm.query(f"SENS{channel}:POW:RANGE:AUTO?"))
    
    def get_wavelength(self, channel: int) -> float:
        assert channel != 1 or channel != 2, "Unexpected channel"
        return float(self.pm.query(f"SENS{channel}:CORR:WAV?"))
    
    # wavelength in nm
    def set_wavelength(self, channel: int, wl: float):
        assert channel != 1 or channel != 2, "Unexpected channel"
        self.pm.write(f"SENS{channel}:CORR:WAV {wl}")

    def get_averaging(self, channel: int) -> float:
        return float(self.pm.query(f":SENS{channel}:AVER?"))
    
    def set_averaging(self, channel: int, aver_rate: float):
        self.pm.write(f":SENS{channel}:AVER {aver_rate}")

    def close(self):
        self.pm.close()