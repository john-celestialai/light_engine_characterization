import matplotlib.pyplot as plt
import numpy as np
import sqlalchemy as sa
from photonics_db import database_address
from sqlalchemy.orm import Session

from light_engine_characterization.tables import LightEngineMeasurement

engine = sa.create_engine(database_address + "/john_dev")

correction_ch5 = 1.4391
correction_ch6 = 1.22897
correction_ch7 = 1.64761

corrections = [
    0,
    0,
    0,
    0,
    0,
    correction_ch5,
    correction_ch6,
    correction_ch7,
]

# fig, ax = plt.subplots(2)
with Session(engine) as session:
    for channel in range(5, 8, 1):
        for temperature in np.arange(25, 85, 10):
            results = session.scalars(
                sa.select(LightEngineMeasurement)
                .where(LightEngineMeasurement.light_engine_id == 123456)
                .where(LightEngineMeasurement.channel == channel)
                .where(LightEngineMeasurement.nominal_temp_c == temperature)
            ).all()
            print(channel, temperature, len(results))

            # Migrate to correct ID number and apply power correction
            # for result in results:
            #     result.light_engine_id = 241331
            #     result.power_dbm = np.array(result.power_dbm) + corrections[channel]
            #     result.power_peak_dbm = result.power_peak_dbm + corrections[channel]
            #     session.merge(result)
            # session.commit()

# plt.show()
