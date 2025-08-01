"""
Known Issues:
- Seems like csv files may not be getting written
- Buggy graph performance (e.g. bias current not displaying correctly)
- Zeus driver is absolute shit, error handling non-existent, completely crashes the program if there is a communication issue
- Sequencer cannot handle temperature sequencing for some reason (tested are queued as "finished")
"""

import logging

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())
log.setLevel(logging.INFO)

import sys
import tempfile
from datetime import datetime
from pathlib import Path

from pymeasure.display.Qt import QtWidgets
from pymeasure.display.windows import ManagedWindow
from pymeasure.experiment import Results

from light_engine_characterization.procedures import TFCArrayCharacterization


class MainWindow(ManagedWindow):

    def __init__(self):
        super().__init__(
            procedure_class=TFCArrayCharacterization,
            inputs=[
                "light_engine_id",
                "channel",
                "nominal_temp_c",
                "temp_settling_time",
                "bias_start",
                "bias_stop",
                "bias_step",
                "coarse_enable",
                "coarse_stop",
                "coarse_step",
            ],
            displays=[
                "light_engine_id",
                "channel",
                "nominal_temp_c",
                # "bias_current_ma",
                # "voltage_v",
                # "tec_temp_c",
                # "ambient_temp_c",
                # "light_engine_temp_c",
                # "wavelength_peak_nm",
                # "power_peak_dbm",
                # "smsr_db",
                # "smsr_linewidth_nm",
                # "linewidth_3db_nm",
                # "linewidth_20db_nm",
            ],
            x_axis="Bias Current (mA)",
            y_axis="wavelength_peak_nm",
            sequencer=True,
            sequencer_inputs=["nominal_temp_c", "channel"],
        )
        self.setWindowTitle("TFC Array Light Engine Characterization")

        self.filename = f"light_engine"
        self.directory = "~/measurement_data/light_engine/tfc/"
        self.store_measurement = True
        self.file_input.extensions = [".csv", ".txt", ".data"]
        self.file_input.filename_fixed = True

    def queue(self, procedure=None):
        """Queue a measurement based on the parameters in the input-widget."""
        log.debug("Queuing experiment.")
        # Check if the filename and the directory inputs are available
        if not self.enable_file_input:
            raise NotImplementedError(
                "Queue method must be overwritten if the filename- and "
                "directory-inputs are disabled."
            )

        if procedure is None:
            procedure = self.make_procedure()

        if not bool(procedure.light_engine_id):
            log.error("No light engine ID specified.")
            raise ValueError("No light engine ID specified.")

        # Initialize date and time metadata
        dt = datetime.now()
        procedure.measurement_date = dt.strftime(r"%Y%m%d")
        procedure.measurement_time = dt.strftime(r"%H%M%S")

        log.debug("Generating measurement filename.")
        if self.store_measurement:
            try:
                filename_attrs = [
                    self.file_input.filename_base,
                    procedure.light_engine_id,
                    procedure.measurement_date,
                    procedure.measurement_time,
                ]
                filename_attrs = [str(attr) for attr in filename_attrs]
                filename = (
                    Path(self.file_input.directory.replace("\n", ""))
                    / Path(procedure.light_engine_id)
                    / Path("_".join(filename_attrs)).with_suffix(
                        "." + self.file_input.filename_extension
                    )
                )
                filename = filename.expanduser()

                # Create the parent directory if it doesn't exist
                filename.parent.mkdir(parents=True, exist_ok=True)
            except KeyError as E:
                if not E.args[0].startswith(
                    "The following placeholder-keys are not valid:"
                ):
                    raise E from None
                log.error(f"Invalid filename provided: {E.args[0]}")
                return
        else:
            filename = tempfile.mktemp(prefix="TempFile_", suffix=".csv")
        log.debug(f"Filename: {filename}")

        log.debug("Initializing procedure.")
        results = Results(procedure, filename)

        log.debug("Generating and queuing new experiment.")
        experiment = self.new_experiment(results)
        self.manager.queue(experiment)
        log.debug("Queuing sequence completed.")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
