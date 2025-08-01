import logging
import time
from datetime import datetime, timedelta

import numpy as np
import pymsteams
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
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from light_engine_characterization.instruments.anritsu import AnritsuMS9740B
from light_engine_characterization.instruments.arroyo import TECSource5240, LDDSource7144
from light_engine_characterization.tables import (
    TFCMeasurement,
    database_address,
)

teams_address = (
    "https://celestialai.webhook.office.com/webhookb2/"
    "8cb3d0ed-2d5f-4852-b21f-451dc3552a65@1f01dda0-08ff-4642-9764-7ebe444cecb7/"
    "IncomingWebhook/4027f23ded4644c29ccfe49cea069397/"
    "4f39bb7b-e2a8-4f49-9421-80a2e79d44e7"
)

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())
log.setLevel(logging.INFO)

data_columns = TFCMeasurement.__table__.columns.keys()
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
            res.write_termination = "\n"
            res.baud_rate = 38400
            resource_id = res.query("*IDN?")
            if "anritsu" in resource_id.lower():
                instruments["anritsu"] = resource
            elif "arroyo" in resource_id.lower():
                if "7144" in resource_id.lower():
                    instruments["arroyo_ldd"] = resource
                elif "5240" in resource_id.lower():
                    instruments["arroyo_tec"] = resource
            elif "keithley" in resource_id.lower():
                instruments["keithley"] = resource
        except Exception as e:
            continue

    return instruments


class TFCCharacterization(Procedure):
    """Procedure for characterizing Molex Light Engines over temperature and bias current."""

    # Measurement unique identifiers
    light_engine_id = Parameter("Light Engine ID")

    # Temperature sweep parameters
    nominal_temp_c = FloatParameter(
        "Temperature", units="°C", minimum=20, maximum=90, decimals=1, default=25
    )
    temp_settling_time = IntegerParameter(
        "Temperature Settling Time", units="s", default=30
    )

    # Current bias sweep settings
    bias_start = FloatParameter(
        "Bias Current Start", units="mA", minimum=0, decimals=1, default=0
    )
    bias_stop = FloatParameter("Bias Current Stop", units="mA", decimals=1, default=400)
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
        self.ldd = None
        self.osa = None
        self.engine = None
        self.session = None

        self.tec_pid = None

        # Evaluate metadata
        self.measurement_date = None
        self.measurement_time = None
        log.debug("Light engine characterization procedure initialized.")

        self.measurement_successful = False

    def startup(self):
        """Measurement startup procedure.

        Connect to all instruments and set any necessary configuration parameters.
        """
        log.debug("Beginning startup procedure.")

        n_retry = 0
        while True:
            try:
                instruments = detect_instruments()

                self.tec = TECSource5240(instruments["arroyo_tec"])
                self.tec_pid = self.tec.pid_params
                log.debug("Connected to TEC.")

                self.ldd = LDDSource7144(instruments["arroyo_ldd"])
                log.debug("Connected to LDD.")

                # Configure the OSA parameters
                self.osa = AnritsuMS9740B(instruments["anritsu"])
                self.osa.wavelength_start = self.wavelength_start
                self.osa.wavelength_stop = self.wavelength_stop
                self.osa.sampling_points = self.wavelength_points
                self.osa.resolution = self.wavelength_resolution
                self.osa.resolution_vbw = self.resolution_vbw
                log.debug("Connected to OSA.")
                break
            except:
                # If we can't connect, wait 5sec and then retry
                if n_retry < 3:
                    log.warning("Failed to connect to instruments, waiting 5sec and retrying.")
                    n_retry += 1
                    time.sleep(5)
                    continue
                else:
                    raise RuntimeError("failed to connect to instruments")

        # Attempt to connect to the database
        try:
            self.engine = create_engine(database_address)
            self.session = Session(self.engine)
            self.session.begin()
            log.debug("Connected to database.")

            # Create the table if it does not exist
            if not inspect(self.engine).has_table(
                TFCMeasurement.__tablename__,
                schema=TFCMeasurement.__table_args__["schema"],
            ):
                try:
                    TFCMeasurement.__table__.create(self.engine)
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
        log.info(f"Starting bias sweep at {self.nominal_temp_c}degC")

        # Set the temperature and wait for it to settle
        self.tec.set_temperature(self.nominal_temp_c)
        self.tec.set_output_on()
        log.debug(f"Waiting {self.temp_settling_time}s for TEC to settle.")
        self.wait_for_tec(self.nominal_temp_c, self.temp_settling_time)
        if self.should_stop():
            log.info("User aborted the procedure.")
            return None
        
        # Set the LDD settings
        self.ldd.channel = 1
        self.ldd.current = 0
        self.ldd.output_enabled = True
        while not self.ldd.completed:
            time.sleep(0.1)

        # Perform the bias sweep
        for j, bias_current in enumerate(self.bias_current_steps):
            start_date = self.measurement_date
            start_time = self.measurement_time

            # Set the light engine channel and bias current
            log.debug(f"Setting bias current to {bias_current}mA")
            self.ldd.set_current(bias_current)
            while True:
                try:
                    current_ma = float(self.ldd.current)
                    break
                except:
                    continue

            while True:
                try:
                    voltage_v = float(self.ldd.voltage)
                    break
                except:
                    continue

            # Read the TEC temperature
            tec_temp_c = self.tec.get_temperature()

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

            # Get the spectral peak (wavelength, power)
            osa_peak = self.osa.measure_peak()
            peak_wavelength_nm = osa_peak[0]
            peak_power_dbm = osa_peak[1]
            log.debug(f"Peak wavelength: {peak_wavelength_nm}nm, {peak_power_dbm}dBm")

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
            le_measurement = {
                "light_engine_id": self.light_engine_id,
                "date": start_date,
                "time": start_time,
                "Bias Current (mA)": current_ma,
                "Voltage (V)": voltage_v,
                "tec_pid": self.tec_pid,
                "nominal_temp_c": self.nominal_temp_c,
                "tec_temp_c": tec_temp_c,
                "wavelength_nm": wavelength_nm.tolist(),
                "power_dbm": power_dbm.tolist(),
                "wavelength_peak_nm": peak_wavelength_nm,
                "power_peak_dbm": peak_power_dbm,
                "smsr_db": smsr_db,
                "smsr_linewidth_nm": smsr_linewidth_nm,
                "linewidth_3db_nm": linewidth_3db_nm,
                "linewidth_20db_nm": linewidth_20db_nm,
            }
            # k = i * self.n_bias_steps + j
            self.emit("results", le_measurement)
            self.emit("progress", 100 * j / self.iterations)

            if self.session:
                le_measurement["bias_current_ma"] = le_measurement.pop(
                    "Bias Current (mA)"
                )
                le_measurement["voltage_v"] = le_measurement.pop("Voltage (V)")
                db_row = TFCMeasurement(**le_measurement)
                self.session.add(db_row)
                self.session.commit()

            if self.should_stop():
                log.info("User aborted the procedure.")
                break

        if not self.should_stop():
            self.measurement_successful = True

    def shutdown(self):
        """Execute the shutdown procedure.

        Disable light engine and TEC and disconnect from all instruments.
        """
        # Disable LDD
        if self.ldd:
            self.ldd.channel = 1
            self.ldd.current = 0
            self.ldd.output_enabled = False

        # Disable TEC
        if self.tec:
            self.tec.set_temperature(25)
            self.tec.set_output_off()

        # Disconnect from the database
        if self.session:
            self.session.close()

        # Parent shutdown procedure
        super().shutdown()
        log.info("Shutdown procedure complete.")

        try:
            myTeamsMessage = pymsteams.connectorcard(teams_address)
            if self.measurement_successful:
                myTeamsMessage.text(
                    (
                        f"Measurement for light engine {self.light_engine_id} "
                        f"started at {self.measurement_time}, "
                        f"{self.measurement_date} completed successfully."
                    )
                )
            else:
                myTeamsMessage.text(
                    (
                        f"Measurement for light engine {self.light_engine_id} "
                        f"started at {self.measurement_time}, "
                        f"{self.measurement_date} failed."
                    )
                )
            myTeamsMessage.send()
        except:
            log.info("Failed to send teams message, skipping.")

    def autodetect_instruments(self):
        """Detect all available instruments and their corresponding ports.

        Iterates over all connected VISA instruments and queries their instrument ID.
        Returns a dictionary containing the instrument ID and port number.
        Raises an error if not all required instruments are detected."""
        pass

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
        # return self.n_temp_steps * self.n_bias_steps
        return self.n_bias_steps

    def wait_for_tec(self, target_temp, t_settle, t_sleep=0.5, n=600, tol=0.1):
        """Wait for the TEC to reach the target temperature, then let it settle for the specified amount of time.

        Raises RuntimeError if the target temp is not reached in the specified time period (default 5min).
        """
        success = False
        count = 0
        for _ in range(n):
            tec_temp = self.tec.get_temperature()
            if tec_temp > target_temp - tol and tec_temp < target_temp + tol:
                success = True
                count += 1
                if count >= 10:
                    break
            elif self.should_stop():
                break
            else:
                count = 0
            time.sleep(t_sleep)

        if success:
            log.info(f"Target temperature reached, settling for {t_settle}s")
            time.sleep(t_settle)
        else:
            raise RuntimeError("Could not reach target TEC temperature.")


if __name__ == "__main__":
    pass
