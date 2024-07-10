"""Remove database entries between the specified measurement ids"""

import sqlalchemy as sa
from photonics_db import database_address
from sqlalchemy.orm import Session

from light_engine_characterization.tables import LightEngineMeasurement

start_id = 167344
stop_id = 167844

engine = sa.create_engine(database_address + "/john_dev")

with Session(engine) as session:
    result = session.execute(
        sa.delete(LightEngineMeasurement).where(
            LightEngineMeasurement.measurement_id.between(start_id, stop_id)
        )
    )
    print(result.rowcount)
    session.commit()
