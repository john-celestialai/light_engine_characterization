import matplotlib.pyplot as plt
import numpy as np
import sqlalchemy as sa
from photonics_db import database_address
from sqlalchemy.orm import Session

from light_engine_characterization.tables import LightEngineMeasurement

engine = sa.create_engine(database_address + "/john_dev")

correction_ch3 = 1.38559
correction_ch7 = 1.64761

le_ids = [241312, 241313, 241314, 241328]
fig, ax = plt.subplots(2)
with Session(engine) as session:
    for le_id in le_ids:
        results = session.scalars(
            sa.select(LightEngineMeasurement)
            .where(LightEngineMeasurement.light_engine_id == int(str(le_id) + "2"))
            .where(LightEngineMeasurement.channel == 7)
            .where(LightEngineMeasurement.nominal_temp_c == 75)
        ).all()
        for result in results:
            result.light_engine_id = le_id
            result.power_dbm = np.array(result.power_dbm) + correction_ch7
            result.power_peak_dbm = result.power_peak_dbm + correction_ch7
            session.merge(result)
    session.commit()

plt.show()
