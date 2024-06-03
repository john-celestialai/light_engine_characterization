from pymeasure.instruments.anritsu import AnritsuMS9740A


class AnritsuMS9740B(AnritsuMS9740A):
    """Anritsu MS9740B Optical Spectrum Analyzer."""

    def __init__(
        self, adapter, name="Anritsu MS9740B Optical Spectrum Analyzer", **kwargs
    ):
        """Constructor."""
        self.analysis_mode = None
        super().__init__(adapter, name, **kwargs)

    def measure_smsr(self):
        """Measure the side-mode suppression ratio of the OSA sweep."""
        self.analysis_mode = "SMSR"
        result = self.analysis_result.split(",")
        smsr_delta_lambda = float(result[0])
        smsr_db = float(result[1].replace("DBM", ""))
        return smsr_delta_lambda, smsr_db

    def measure_linewidth(self, delta_db):
        """Measure the linewidth of the peak wavelength at peak_power_dbm - delta_db."""
        self.analysis_mode = f"ENV,{delta_db:0.1f}"
        result = self.analysis_result.split(",")
        linewidth = float(result[1].replace("DBM", ""))
        return linewidth


class OSA_MS9740B:
    def open(self, rm):
        try:
            self.osa = rm.open_resource("TCPIP::10.10.60.150::INSTR")
        except:
            print("Failed to connect to OSA. Verify Address")
            exit()
        attn = self.osa.query("ATT?")
        if "ON" not in str(attn):
            self.osa.write("ATT ON")
        print("OSA Attenuation Status: ", self.osa.query("ATT?"))

    def set_timeout(self, timeout):
        self.timeout = timeout

    def set_wavelength(self, startW, stopW, pointsN):
        self.osa.write(f"*CLS")
        self.osa.write(f"STA {startW}; STO {stopW}; MPT {pointsN}")

    def set_resolution_VBW(self, res, vbw):
        self.osa.write(f"VBW {vbw}; RES {res}")

    def get_SMSR(self):
        self.osa.write("ANA SMSR")
        read_frame = self.osa.query("ANAR?")  # R - Result
        SMSR_delta_Lambda_nm = float(read_frame.split(",")[0])
        SMSR_dB = float(read_frame.split(",")[1].split("DBM")[0])
        return SMSR_delta_Lambda_nm, SMSR_dB

    def get_linewidth(self, delta_dB):
        self.osa.write(f"ANA ENV,{delta_dB}")
        read_frame = self.osa.query("ANAR?")  # R - Result
        delta_Lambda_nm = float(read_frame.split(",")[0])
        LineWidth = float(read_frame.split(",")[1].split("DBM")[0])
        return LineWidth

    def get_peak(self):
        self.osa.write("PKS PEAK")
        read_frame = self.osa.query("TMK?")
        peak_wavelength = float(read_frame.split(",")[0])
        peak_power = float(read_frame.split(",")[1].split("DBM")[0])
        return peak_wavelength, peak_power

    def sweep_single(self):
        self.osa.write("SSI; *WAI")

    def get_sweep_result(self):
        read_frame = self.osa.query("DMA?; *WAI")  # R is for result
        while float(self.osa.query("*OPC?")) != 1:
            time.sleep(0.5)
        traceList = read_frame.split()
        return traceList

    def write(self, command):
        print(f"writing: {command}", end="")
        self.osa.write(command)
        print(f"--- Write Complete.")

    def query(self, command):
        print(f"querying: {command}", end="")
        x = self.osa.query(command)
        print(f"-------reply to {command} was {x}")
        return x.strip()

    def get_3_peaks(self):
        self.osa.write("PKS PEAK")
        read_frame = self.osa.query("TMK?")
        peak_wavelength_1 = float(read_frame.split(",")[0])
        peak_power_1 = float(read_frame.split(",")[1].split("DBM")[0])
        self.osa.write("PKS NEXT")
        read_frame = self.osa.query("TMK?")
        peak_wavelength_2 = float(read_frame.split(",")[0])
        peak_power_2 = float(read_frame.split(",")[1].split("DBM")[0])
        self.osa.write("PKS NEXT")
        read_frame = self.osa.query("TMK?")
        peak_wavelength_3 = float(read_frame.split(",")[0])
        peak_power_3 = float(read_frame.split(",")[1].split("DBM")[0])
        return (
            peak_wavelength_1,
            peak_power_1,
            peak_wavelength_2,
            peak_power_2,
            peak_wavelength_3,
            peak_power_3,
        )

    def close(self):
        self.osa.close()
