import logging
import time
from datetime import datetime

import numpy as np
import pyvisa as visa
from pymeasure.experiment import (
    BooleanParameter,
    FloatParameter,
    IntegerParameter,
    Measurable,
    Metadata,
    Parameter,
    Procedure,
)
from pymeasure.instruments.keithley import Keithley2400
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from light_engine_characterization.instruments.anritsu import AnritsuMS9740B
from light_engine_characterization.instruments.arroyo import TECSource5240
from light_engine_characterization.instruments.custom import ZeusController
from light_engine_characterization.tables import (
    LightEngineMeasurement,
    database_address,
)

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())
log.setLevel(logging.INFO)

data_columns = LightEngineMeasurement.__table__.columns.keys()
data_columns = list(
    map(lambda x: x.replace("bias_current_ma", "Bias Current (mA)"), data_columns)
)
data_columns = list(map(lambda x: x.replace("voltage_v", "Voltage (V)"), data_columns))


def detect_instruments():
    rm = visa.ResourceManager()
    resources = rm.list_resources()
    instruments = {}
    for resource in resources:
        try:
            res = rm.open_resource(resource)
            res.write_termination = '\n'
            resource_id = res.query("*IDN?")
            if "anritsu" in resource_id.lower():
                instruments["anritsu"] = resource
            elif "arroyo" in resource_id.lower():
                instruments["arroyo"] = resource
            elif "keithley" in resource_id.lower():
                instruments["keithley"] = resource
        except Exception as e:
            continue

    return instruments


class MolexLECharacterization(Procedure):
    """Procedure for characterizing Molex Light Engines over temperature and bias current."""

    # Measurement unique identifiers
    light_engine_id = Parameter("Light Engine ID")
    channel = IntegerParameter("Light Engine Channel", minimum=0, maximum=7, default=0)

    # Temperature sweep parameters
    temp_start = FloatParameter(
        "Temperature Start", units="°C", minimum=20, maximum=90, decimals=1, default=25
    )
    temp_stop = FloatParameter(
        "Temperature Stop", units="°C", minimum=20, maximum=90, decimals=1, default=75
    )
    temp_step = FloatParameter(
        "Temperature Step", units="°C", minimum=1, decimals=1, default=10
    )
    temp_settling_time = IntegerParameter(
        "Temperature Settling Time", units="s", default=30
    )

    # Current bias sweep settings
    bias_start = FloatParameter(
        "Bias Current Start", units="mA", minimum=0, decimals=1, default=0
    )
    bias_stop = FloatParameter("Bias Current Stop", units="mA", decimals=1, default=500)
    bias_step = FloatParameter("Bias Current Step", units="mA", decimals=1, default=1)
    coarse_enable = BooleanParameter("Enable Coarse Sweep?", default=False)
    coarse_stop = FloatParameter(
        "Coarse Bias Current Stop", group_by="coarse_enable", units="mA", default=200
    )
    coarse_step = FloatParameter(
        "Coarse Bias Current Step", group_by="coarse_enable", units="mA", default=20
    )

    # OSA configuration settings
    wavelength_start = 1565
    wavelength_stop = 1585
    wavelength_points = 2001
    wavelength_resolution = 0.03
    resolution_vbw = "1kHz"

    # Measurement metadata
    # TODO: Metadata does not seem to be fully supported yet
    # measurement_date = Metadata("Date", fget=lambda: datetime.now().strftime(r"%Y%m%d"))
    # measurement_time = Metadata("Time", fget=lambda: datetime.now().strftime(r"%H%M%S"))

    # Measurement data
    # bias_current_ma = FloatParameter("Bias Current (mA)")
    # voltage_v = FloatParameter("Voltage (V)")
    # tec_temp_c = Measurable("tec_temp_c")
    # ambient_temp_c = Measurable("ambient_temp_c")
    # light_engine_temp_c = Measurable("light_engine_temp_c")
    # mpd_current_ma = Measurable("mpd_current_ma")
    # wavelength_nm = Measurable("wavelength_nm")
    # power_dbm = Measurable("power_dbm")
    # power_uw = Measurable("power_uw")
    # wavelength_peak_nm = Measurable("wavelength_peak_nm")
    # power_peak_dbm = Measurable("power_peak_dbm")
    # smsr_db = Measurable("smsr_db")
    # smsr_linewidth_nm = Measurable("smsr_linewidth_nm")
    # linewidth_3db_nm = Measurable("linewidth_3db_nm")
    # linewidth_20db_nm = Measurable("linewidth_20db_nm")

    DATA_COLUMNS = data_columns

    def __init__(self, *args) -> None:
        super().__init__(*args)

        self.tec = None
        self.osa = None
        self.smu = None
        self.zeus = None
        self.engine = None
        self.session = None

        self.tec_pid = None

        # Evaluate metadata
        self.measurement_date = None
        self.measurement_time = None
        log.debug("Light engine characterization procedure initialized.")

    def startup(self):
        """Measurement startup procedure.

        Connect to all instruments and set any necessary configuration parameters.
        """
        log.debug("Beginning startup procedure.")

        instruments = detect_instruments()

        self.tec = TECSource5240(instruments["arroyo"])
        self.tec_pid = self.tec.pid_params
        log.debug("Connected to TEC.")

        # Configure the OSA parameters
        self.osa = AnritsuMS9740B(instruments["anritsu"])
        self.osa.wavelength_start = self.wavelength_start
        self.osa.wavelength_stop = self.wavelength_stop
        self.osa.sampling_points = self.wavelength_points
        self.osa.resolution = self.wavelength_resolution
        self.osa.resolution_vbw = self.resolution_vbw
        log.debug("Connected to OSA.")

        # Connect to SMU
        # self.smu = Keithley2400(instruments["keithley"])
        # log.debug("Connected to SMU.")

        # Connect to Zeus controller
        self.zeus = ZeusController()
        self.zeus.open_session("pynq1")
        self.zeus.write_read("fan.set_le_duty_cycle(90)")
        log.debug("Connected to Zeus controller.")

        # Attempt to connect to the database
        try:
            self.engine = create_engine(database_address)
            self.session = Session(self.engine)
            self.session.begin()
            log.debug("Connected to database.")

            # Create the table if it does not exist
            if not inspect(self.engine).has_table(
                LightEngineMeasurement.__tablename__,
                schema=LightEngineMeasurement.__table_args__["schema"],
            ):
                try:
                    LightEngineMeasurement.__table__.create(self.engine)
                except Exception as e:
                    log.error(e)
        except Exception as e:
            log.error(e)
            log.warning(
                "Could not connect to database, data will only be saved locally."
            )
            self.session = None

        log.info("Measurement startup complete.")

    def execute(self):
        """Execute the light engine characterization procedure."""

        for i, temperature in enumerate(self.temperature_steps):
            log.info(f"Starting bias sweep at {temperature}degC")
            self.tec.set_temperature(temperature)
            self.tec.set_output_on()
            # self.smu.enable_source = True

            log.debug(f"Waiting {self.temp_settling_time}s for TEC to settle.")
            self.wait_for_tec(temperature, self.temp_settling_time)
            if self.should_stop():
                log.info("User aborted the procedure.")
                break

            for j, bias_current in enumerate(self.bias_current_steps):
                start_date = self.measurement_date
                start_time = self.measurement_time

                # Set the light engine channel and bias current
                log.debug(f"Setting bias current to {bias_current}mA")
                query_string = f"light_engine.set_laser_ma(LEChannel.LE{self.channel},{bias_current})"
                self.zeus.write_read(query_string)

                # Read the temperatures, voltages, and currents
                tec_temp_c = self.tec.get_temperature()
                # cathode_voltage_v = self.read_voltage()
                cathode_voltage_v = self.zeus.get_voltage_readout(self.channel)
                ambient_temp_c, light_engine_temp_c = (
                    self.zeus.get_light_engine_temperatures()
                )
                mpd_current_ma = self.zeus.get_mpd_readout(self.channel)

                # Trigger a single OSA sweep and retrieve the result
                sweep_successful = False
                while not sweep_successful:
                    try:
                        self.osa.single_sweep()
                        sweep_successful = True
                    except RuntimeWarning:
                        log.warning("Sweep timed out, re-running sweep")

                wavelength_nm, power_dbm = self.osa.read_memory()
                wavelength_nm = np.array(wavelength_nm)
                power_dbm = np.array(power_dbm)
                power_uw = 10 ** (power_dbm / 10) * 1000

                # Get the spectral peak (wavelength, power)
                osa_peak = self.osa.measure_peak()
                peak_wavelength_nm = osa_peak[0]
                peak_power_dbm = osa_peak[1]
                log.debug(
                    f"Peak wavelength: {peak_wavelength_nm}nm, {peak_power_dbm}dBm"
                )

                # If the peak power is greater than -30dBm, also measure the SMSR and linewidth
                if peak_power_dbm > -30:
                    smsr_linewidth_nm, smsr_db = self.osa.measure_smsr()
                    linewidth_3db_nm = self.osa.measure_linewidth(3)
                    linewidth_20db_nm = self.osa.measure_linewidth(20)
                else:
                    smsr_linewidth_nm, smsr_db = np.nan, np.nan
                    linewidth_3db_nm = np.nan
                    linewidth_20db_nm = np.nan

                # Record the measurement
                # self.bias_current_ma = bias_current
                le_measurement = {
                    "light_engine_id": self.light_engine_id,
                    "channel": self.channel,
                    "date": start_date,
                    "time": start_time,
                    "Bias Current (mA)": bias_current,
                    "Voltage (V)": cathode_voltage_v,
                    "tec_pid": self.tec_pid,
                    "tec_temp_c": tec_temp_c,
                    "ambient_temp_c": ambient_temp_c,
                    "light_engine_temp_c": light_engine_temp_c,
                    "mpd_current_ma": mpd_current_ma,
                    "wavelength_nm": wavelength_nm.tolist(),
                    "power_dbm": power_dbm.tolist(),
                    "power_uw": power_uw.tolist(),
                    "wavelength_peak_nm": peak_wavelength_nm,
                    "power_peak_dbm": peak_power_dbm,
                    "smsr_db": smsr_db,
                    "smsr_linewidth_nm": smsr_linewidth_nm,
                    "linewidth_3db_nm": linewidth_3db_nm,
                    "linewidth_20db_nm": linewidth_20db_nm,
                }
                k = i * self.n_bias_steps + j
                self.emit("results", le_measurement)
                self.emit("progress", 100 * k / self.iterations)

                if self.session:
                    le_measurement["bias_current_ma"] = le_measurement.pop(
                        "Bias Current (mA)"
                    )
                    le_measurement["voltage_v"] = le_measurement.pop("Voltage (V)")
                    db_row = LightEngineMeasurement(**le_measurement)
                    self.session.add(db_row)
                    self.session.commit()

                if self.should_stop():
                    break

            if self.should_stop():
                log.info("User aborted the procedure.")
                break

    def shutdown(self):
        """Execute the shutdown procedure.

        Disable light engine and TEC and disconnect from all instruments.
        """
        # Disable light engine
        if self.zeus:
            query_string = f"light_engine.set_laser_ma(LEChannel.LE{self.channel},0)"
            self.zeus.write_read("fan.set_le_duty_cycle(90)")
            self.zeus.write_read(query_string)
            self.zeus.close()

        # Disable TEC
        if self.tec:
            self.tec.set_temperature(25)
            self.tec.set_output_off()
            # self.tec.close()

        # Disconnect from OSA and SMU
        # if self.osa:
        #     self.osa.close()
        # if self.smu:
        #     self.smu.close()

        # Disconnect from the database
        if self.session:
            self.session.close()

        # Parent shutdown procedure
        super().shutdown()
        log.info("Shutdown procedure complete.")

    def autodetect_instruments(self):
        """Detect all available instruments and their corresponding ports.

        Iterates over all connected VISA instruments and queries their instrument ID.
        Returns a dictionary containing the instrument ID and port number.
        Raises an error if not all required instruments are detected."""

    @property
    def temperature_steps(self) -> np.ndarray:
        """Array of temperature set points to step through."""
        return np.arange(
            self.temp_start, self.temp_stop + self.temp_step, self.temp_step
        )

    @property
    def n_temp_steps(self) -> int:
        """Number of temperature step points."""
        return self.temperature_steps.size

    @property
    def bias_current_steps(self) -> np.ndarray:
        """Array of current bias points to step through."""
        if not self.coarse_enable:
            bias_currents = np.arange(
                self.bias_start, self.bias_stop + self.bias_step, self.bias_step
            )
        else:
            coarse_steps = np.arange(
                self.bias_start, self.coarse_stop, self.coarse_step
            )
            fine_steps = np.arange(
                self.coarse_stop, self.bias_stop + self.bias_step, self.bias_step
            )
            bias_currents = np.append(coarse_steps, fine_steps)
        return bias_currents

    @property
    def n_bias_steps(self) -> int:
        """Number of current bias step points."""
        return self.bias_current_steps.size

    @property
    def iterations(self) -> int:
        return self.n_temp_steps * self.n_bias_steps

    def wait_for_tec(self, target_temp, t_settle, t_sleep=0.5, n=600, tol=0.1):
        """Wait for the TEC to reach the target temperature, then let it settle for the specified amount of time.
        
        Raises RuntimeError if the target temp is not reached in the specified time period (default 5min)."""
        success = False
        for _ in range(n):
            tec_temp = self.tec.get_temperature()
            if tec_temp > target_temp - tol:
                success = True
                break
            elif self.should_stop():
                break
            time.sleep(t_sleep)
            
        if success:
            log.info(f"Target temperature reached, settling for {t_settle}s")
            time.sleep(t_sleep)
        else:
            raise RuntimeError("Could not reach target TEC temperature.")
            

    def read_voltage(self):
        """Quickfix function to implement the SMU read voltage procedure."""
        # TODO: Integrate this into the SMU driver
        self.smu.write(f":SOUR:FUNC CURR")
        self.smu.write(f":SOUR:CURR:MODE FIXED")
        self.smu.write(r':SENS:FUNC "VOLT"')
        self.smu.write(f":SOUR:CURR:RANG MIN")
        self.smu.write(f":SOUR:CURR:LEV 0")
        self.smu.write(f":SENS:VOLT:PROT 10")
        self.smu.write(f":OUTP ON")
        voltage_v = self.smu.ask(f":READ?").replace("\n", "")
        self.smu.write(f":OUTP OFF")
        return voltage_v

