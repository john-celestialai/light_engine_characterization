class LE_POET:
    
    def open(self, rm):
        try:
            self.laser = rm.open_resource('TCPIP0::192.168.1.20::5000::SOCKET')
            self.laser.read_termination = '\n'
            self.laser.write_termination = '\n'
        except:
            print("Failed to connect to LE. Verify Address")
            exit()
    
    def idn(self):
        readframe = self.laser.query("*IDN?")
        return readframe
    
    def set_timeout(self,timeout):
        self.timeout = timeout
    
    ## Channel Selection
    
    def set_output_on(self,Channel):
        readframe = self.laser.query(f'OUTPut:LD ON,{Channel}')
        return readframe
    
    def set_output_off(self,Channel):
        readframe = self.laser.query(f'OUTPut:LD OFF,{Channel}')
        return readframe
    
    def get_optical_output_status(self,Channel):
        readframe = self.laser.query(f'OUTPut:LD? {Channel}') 
        return readframe

    ## TEC Control 
    
    def set_temperature(self,Temperature):
        readframe = self.laser.query(f"SET:TEC {Temperature}")
        return readframe
     
    def set_tec_output_on(self):
        readframe = self.laser.query(f"OUTPut:TEC ON")
        return readframe
    
    def set_tec_output_off(self):
        readframe = self.laser.query(f"OUTPut:TEC OFF")
        return readframe
    
    def get_tec_output_status(self):
        readframe = self.laser.query(f"OUTPut:TEC?")
        return readframe
    
    def get_temperature(self):
        readframe = self.laser.query(f"SET:TEC?")
        return readframe
    
    def measure_temperature(self):
        readframe = self.laser.query(f"MEASure:TEC?")
        return float(readframe)
    
    ## LE Biasing
    
    def set_laser_current(self,Channel,Bias_current):
        readframe = self.laser.query(f'SET:CURRent {Bias_current},{Channel}')
        return readframe
    
    def get_laser_current(self,Channel):
        readframe = self.laser.query(f'SET:CURRent? {Channel}')
        return readframe
    
    def measure_laser_current(self,Channel):
        readframe = self.laser.query(f'MEASure:CURRent? {Channel}')
        meas_current = float(readframe.split(",")[1])
        return meas_current
    
    def measure_laser_voltage(self,Channel):
        readframe = self.laser.query(f'MEASure:VOLTage? {Channel}')
        meas_voltage = float(readframe.split(",")[1])
        return meas_voltage
    
    def measure_mpd_current(self,Channel):
        readframe = self.laser.query(f'MEASure:MPD? {Channel}')
        mpd_current = float(readframe.split(",")[1])
        return mpd_current
    
    ## Fan Settings
    
    def set_fan_on(self,Channel):
        readframe = self.laser.query(f'OUTPut:FAN ON,{Channel}')
        return readframe
    
    def set_fan_off(self,Channel):
        readframe = self.laser.query(f'OUTPut:FAN OFF,{Channel}')
        return readframe

    def set_fan_voltage(self,Bias_voltage):
        readframe = self.laser.query(f'SET:FAN {Voltage}')
        return readframe
    
    def get_fan_voltage(self):
        readframe = self.laser.query(f'SET:FAN?')
        return readframe
        
    def get_fan_output_status(self,Channel):
        readframe = self.laser.query(f'OUTPut:FAN? {Channel}')
        return readframe

    def close(self):
        self.laser.close()