"""Remove database entries between the specified measurement ids"""

import sqlalchemy as sa
from sqlalchemy.orm import Session

from light_engine_characterization.tables import TFCMeasurement, database_address

start_id = 1
stop_id = 694

engine = sa.create_engine(database_address)

with Session(engine) as session:
    result = session.execute(
        sa.delete(TFCMeasurement).where(
            TFCMeasurement.measurement_id.between(start_id, stop_id)
        )
    )
    print(result.rowcount)
    session.commit()
