import logging

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

import sys
import tempfile
from datetime import datetime

from pymeasure.display.Qt import QtWidgets
from pymeasure.display.windows import ManagedWindow
from pymeasure.experiment import Results

from .procedures import MolexLECharacterization


class MainWindow(ManagedWindow):

    def __init__(self):
        super().__init__(
            procedure_class=MolexLECharacterization,
            inputs=[
                "light_engine_id",
                "channel",
                "temp_start",
                "temp_stop",
                "temp_settling_time",
                "bias_start",
                "bias_stop",
                "bias_step",
                "coarse_enable",
                "coarse_stop",
                "coarse_stop",
                "coarse_step",
            ],
            displays=[
                "light_engine_id",
                "channel",
                "bias_current_ma",
                "voltage_v",
                "tec_temp_c",
                "wavelength_peak_nm",
                "power_peak_nm",
                "smsr_db",
                "smsr_linewidth_nm",
                "linewidth_3db_nm",
                "linewidth_20db_nm",
            ],
            x_axis="bias_current_ma",
            y_axis="wavelength_peak_nm",
        )
        self.setWindowTitle("Molex Light Engine Characterization")

        dt = datetime.now()
        self.filename = f"light_engine_{datetime.date(dt)}_{datetime.time(dt)}"
        self.directory = "~/measurement_data/light_engine/molex/"
        self.store_measurement = True
        self.file_input.extensions = ["csv", "txt", "data"]
        self.file_input.filename_fixed = True

    def queue(self, procedure=None):
        """Queue a measurement based on the parameters in the input-widget."""
        # Check if the filename and the directory inputs are available
        if not self.enable_file_input:
            raise NotImplementedError(
                "Queue method must be overwritten if the filename- and "
                "directory-inputs are disabled."
            )

        if procedure is None:
            procedure = self.make_procedure()

        if self.store_measurement:
            try:
                filename = f"{self.file_input.filename_base}.{self.file_input.filename_extension}"
            except KeyError as E:
                if not E.args[0].startswith(
                    "The following placeholder-keys are not valid:"
                ):
                    raise E from None
                log.error(f"Invalid filename provided: {E.args[0]}")
                return
        else:
            filename = tempfile.mktemp(prefix="TempFile_", suffix=".csv")

        results = Results(procedure, filename)

        experiment = self.new_experiment(results)
        self.manager.queue(experiment)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
