from binascii import unhexlify

class TSL_TLS200:
    
    @staticmethod
    def checkSum(command):
        chksum = 0
        chksum_4chars = ""
        for n in range(int(len(command) / 2)):
            chksum += int(command[n * 2: n * 2 + 2], 16)
            chksum_Hex = str(hex(chksum))[2:]
            padding = 6
        chksum_4chars = f"{chksum:#06x}"[2:]
        return chksum_4chars.upper()
    
    def open(self,rm):
        serial_port = 6
        try:
            self.tsl = rm.open_resource(f'ASRL{serial_port}::INSTR')
        except:
            print("Failed to connect to TSL. Verify Address")
            exit()        
        self.tsl.baud_rate = 115200

    def set_output_on(self):
        turnOnHexMessage = b'\xAA\x4C\x53\x4F\x4E\x00\x00\x01\x3C'
        turnOnHexMessage += b'\x0D'
        bytesWritten = self.tsl.write_raw(turnOnHexMessage)

    def set_output_off(self):
        turnOffHexMessage = b'\xAA\x4C\x53\x4F\x46\x00\x00\x01\x34'
        turnOffHexMessage += b'\x0D'
        bytesWritten = self.tsl.write_raw(turnOffHexMessage)

    def set_wavelength(self, wavelength_nm):
        wavelength_pm = int(wavelength_nm*1000)
        head = "AA"
        command1 = "474F"
        command2 = "574C"
        msgLength = "0002"
        wavelen_Hex = str(hex(wavelength_pm))[2:].upper()
        command = f"{command1}{command2}{msgLength}{wavelen_Hex}"
        chksum_4chars = self.checkSum(command)
        write_frame = f"{head}{command1}{command2}{msgLength}00{wavelen_Hex}{chksum_4chars}"
        messageSetWavelengthHex = unhexlify(write_frame)
        messageSetWavelengthHex += b'\x0D'
        bytesWritten = self.tsl.write_raw(messageSetWavelengthHex)

    def close(self):
        self.tsl.close()
    