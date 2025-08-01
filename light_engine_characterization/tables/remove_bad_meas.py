import matplotlib.pyplot as plt
import numpy as np
import sqlalchemy as sa
from photonics_db import database_address
from sqlalchemy.orm import Session

from light_engine_characterization.tables import LightEngineMeasurement

engine = sa.create_engine(database_address + "/john_dev")

le_ids = [123456]
# fig, ax = plt.subplots(2)
with Session(engine) as session:
    for le_id in le_ids:
        result = session.execute(
            sa.delete(LightEngineMeasurement).where(
                LightEngineMeasurement.light_engine_id == le_id
            )
        )
        print(result.rowcount)
        session.commit()
