# Celestial AI DCA Module - 12/21/23

import sys
import pyvisa as visa  # PyVISA library

# ADDRESS = 'TCPIP0::localhost::hislip0,4880::INSTR'
# ADDRESS = 'TCPIP0::10.10.60.3::hislip0,4880::INSTR'  # used to work in July 2023. Check DCA Tools menu
ADDRESS_DCA = 'TCPIP0::10.10.60.3::hislip0,4880::INSTR'  # This worked 12/21/2023. No special setup required.

class DCAclass:

    def __init__(self):
        self.FlexDCAport = None

    def open(self):
        rm = visa.ResourceManager(r'C:\WINDOWS\system32\visa64.dll')
        print('\nVISA library version:  ', rm)
        FlexDCA = rm.open_resource(ADDRESS_DCA)
        FlexDCA.timeout = 3000  # 10s
        FlexDCA.write_termination = '\n'
        FlexDCA.read_termination = '\n'
        if False:
            print('\nVISA termination string (write) set to newline: ASCII ',
                  ord(FlexDCA.write_termination))
            print('VISA termination string (read) set to newline: ASCII ',
                  ord(FlexDCA.read_termination))
        print('DCA OPENED: FlexDCA ID string: ', FlexDCA.query('*IDN?'), flush=True)
        self.FlexDCAport = FlexDCA

    def selectChannel(self, channel):
        self.genericSetCommand(f':MEASure:OSCilloscope:APOWER:SOURCE CHAN{channel}')
        self.genericSetCommand(f':MEASure:OSCilloscope:OMA:SOURCE CHAN{channel}')
        
    def get_OMA_watts(self):
        oma1 = self.genericQuery(':MEASure:OSCilloscope:OMA?')
        return oma1

    def get_AVG_power_watts(self):
        self.genericSetCommand(':MEASure:OSCilloscope:APOWER:UNITS WATT')
        ap1 = self.genericQuery(':MEASure:OSCilloscope:APOWER?')
        return ap1

    def get_AVG_power_DBM(self):
        self.genericSetCommand(':MEASure:OSCilloscope:APOWER:UNITS DBM')
        ap1 = self.genericQuery(':MEASure:OSCilloscope:APOWER?')
        return ap1

    def genericQuery(self, queryMessage):
        # measurement = self.FlexDCAport.query(f':MEASure:OSCilloscope:{queryMessage}')
        measurement = self.FlexDCAport.query(f'{queryMessage}')
        print(f"Response to {queryMessage} :", float(measurement))
        return measurement

    def measureQuery(self, queryMessage):
        meas1 = self.genericQuery(f':MEASure:OSCilloscope:{queryMessage}')
        return meas1

    def genericSetCommand(self, setMessage):
        # measurement = self.FlexDCAport.query(f':MEASure:OSCilloscope:{queryMessage}')
        measurement = self.FlexDCAport.write(f'{setMessage}')
        print(f"Response to {setMessage} :", measurement)
        return measurement


if __name__ == "__main__":
    Scope = DCAclass()
    Scope.open()
    Scope.genericQuery(':MEASure:OSCilloscope:VBase?')
    Scope.measureQuery('VBase?')
    Scope.measureQuery('VTop?')
    Scope.genericQuery(':MEASure:OSCilloscope:Vtop?')
    Scope.genericSetCommand(':MEASure:OSCilloscope:APOWER:SOURCE CHAN1')
    Scope.selectChannel(1)
    Scope.genericSetCommand(':MEASure:OSCilloscope:APOWER:UNITS WATT')
    Scope.genericQuery(':MEASure:OSCilloscope:APOWER?')
    Scope.genericSetCommand(':MEASure:OSCilloscope:APOWER:UNITS DBM')
    Scope.genericQuery(':MEASure:OSCilloscope:APOWER?')
    oma = Scope.genericQuery(':MEASure:OSCilloscope:OMA?')
    print("OMA here: ", oma)
