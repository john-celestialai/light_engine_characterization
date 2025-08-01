from pymeasure.instruments.anritsu import AnritsuMS9740A
import time
import logging

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


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
        result = self.analysis_result
        print(result)
        smsr_delta_lambda = float(result[0])
        smsr_db = result[1]
        return smsr_delta_lambda, smsr_db

    def measure_linewidth(self, delta_db):
        """Measure the linewidth of the peak wavelength at peak_power_dbm - delta_db."""
        self.analysis_mode = f"ENV,{delta_db:0.1f}"
        result = self.analysis_result
        linewidth = result[1]
        return linewidth

    def wait_for_sweep(self, n=20, delay=0.5):
        """Wait for a sweep to stop.

        This is performed by checking bit 1 of the ESR2.
        """
        log.debug("Waiting for spectrum sweep")

        while self.esr2 != 3 and n > 0:
            log.debug(f"Wait for sweep [{n}]")
            # log.debug("ESR2: {}".format(esr2))
            time.sleep(delay)
            n -= 1

        if n <= 0:
            raise RuntimeWarning(f"Sweep Timeout Occurred ({int(delay * n)} s)")

    def single_sweep(self, **kwargs):
        """Perform a single sweep and wait for completion."""
        log.debug("Performing a Spectrum Sweep")
        self.clear()
        self.write("SSI")
        self.wait_for_sweep(**kwargs)


if __name__ == "__main__":
    osa = AnritsuMS9740B("TCPIP0::10.10.60.8::INSTR")

    print(osa.single_sweep())
    osa_peak = osa.measure_peak()
    peak_wavelength_nm = osa_peak[0]
    peak_power_dbm = osa_peak[1]
    log.debug(f"Peak wavelength: {peak_wavelength_nm}nm, {peak_power_dbm}dBm")

    # If the peak power is greater than -30dBm, also measure the SMSR and linewidth
    if peak_power_dbm > -30:
        smsr_linewidth_nm, smsr_db = osa.measure_smsr()
        linewidth_3db_nm = osa.measure_linewidth(3)
        linewidth_20db_nm = osa.measure_linewidth(20)
