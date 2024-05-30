class TSL_Quantifi_1001_2_FC:

    def open(self, rm):
        try:
            self.tsl = rm.open_resource('TCPIP::10.10.60.153::INSTR')
        except:
            print("Failed to connect to Quantifi Laser. Verify Address")
            exit()
    
    def set_output_on(self, laserslot, channel):
        self.tsl.write(":OUTP"+str(laserslot)+":CHAN"+str(channel)+":STATE ON")
    
    def set_output_off(self, laserslot, channel):
        self.tsl.write(":OUTP"+str(laserslot)+":CHAN"+str(channel)+":STATE OFF")
    
    def set_wavelength(self, laserslot, channel, wavelength):
        self.tsl.write(":SOUR"+str(laserslot)+":CHAN"+str(channel)+":WAV "+ str(wavelength)+" NM")
        while(self.tsl.query("*OPC?").strip() != '1'):
            pass

    def set_power(self, laserslot, channel, power):
        self.tsl.write(":SOUR"+str(laserslot)+":CHAN"+str(channel)+":POWER "+ str(power))
        
    def close(self):
        self.tsl.close()
