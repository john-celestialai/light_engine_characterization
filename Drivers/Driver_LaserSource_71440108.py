class LaserSource_71440108:

    def open(self, rm):
        try:
            self.ld = rm.open_resource('ASRL4::INSTR')
        except:
            print("Failed to connect to Laser Driver. Verify Address")
            exit()
        self.ld.baud_rate = 38400
        self.ld.read_termination = '\n'
        self.ld.write_termination = '\n'

    def set_laser_current(self, Channel, Bias_current):
        if Bias_current > 500:
            print("Light Engine Abs. Max. Bias Current: 500mA")
            exit()
        else:
            self.ld.write(f'LASer:CHAN {Channel}') 
            self.ld.write(f'LASer:LDI {Bias_current}')

    def get_laser_voltage(self, Channel):
        self.ld.write(f'LASer:CHAN {Channel}') 
        Voltage = self.ld.query(f'LASer:LDV?')
        return float(Voltage)
    
    def set_output_on(self, Channel):
        self.ld.write(f'LASer:CHAN {Channel}') 
        self.ld.write(f'LASer:OUTput {1}')
    
    def set_output_off(self, Channel):
        self.ld.write(f'LASer:CHAN {Channel}') 
        self.ld.write(f'LASer:OUTput {0}')
        
    def IDN(self):
        print(self.ld.query('*IDN?'))

    def close(self):
        self.ld.close()