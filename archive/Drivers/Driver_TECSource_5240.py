class TECSource_5240:

    def open(self, rm, resource):
        try:
            self.tec = rm.open_resource(resource)
        except:
            print("Failed to connect to TEC. Verify Address")
            exit()
        self.tec.baud_rate = 38400
        self.tec.read_termination = '\n'
        self.tec.write_termination = '\n'

    def set_temperature(self, Temperature):
        self.tec.write(f'TEC:T {Temperature}')

    def get_temperature(self):
        Temperature = self.tec.query(f'TEC:T?')
        return float(Temperature)
        
    def set_output_on(self):
        self.tec.write(f'TEC:OUTput {1}')
    
    def set_output_off(self):
        self.tec.write(f'TEC:OUTput {0}')
    
    def IDN(self):
        print(self.tec.query('*IDN?'))

    def close(self):
        self.tec.close()