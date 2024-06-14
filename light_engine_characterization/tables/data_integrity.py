import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from light_engine_characterization.tables import (
    LightEngineMeasurement,
    database_address,
)

engine = create_engine(database_address)
temps = [25, 35, 45, 55, 65, 75]

# Get the number of unique Light Engines in the database
with Session(engine) as session:
    le_ids = sorted(
        [v for (v,) in session.query(LightEngineMeasurement.light_engine_id).distinct()]
    )
    for le_id in le_ids:
        for i in range(8):
            for temp in temps:
                result = session.scalar(
                    sa.select(sa.func.count())
                    .select_from(LightEngineMeasurement)
                    .where(LightEngineMeasurement.light_engine_id == le_id)
                    .where(LightEngineMeasurement.channel == i)
                    .where(LightEngineMeasurement.nominal_temp == temp)
                )
                print(le_id, i, result)
