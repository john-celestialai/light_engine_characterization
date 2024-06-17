import sys

import pandas as pd
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
                n_points = session.scalar(
                    sa.select(sa.func.count())
                    .select_from(LightEngineMeasurement)
                    .where(LightEngineMeasurement.light_engine_id == le_id)
                    .where(LightEngineMeasurement.channel == i)
                    .where(LightEngineMeasurement.nominal_temp_c == temp)
                )

                if n_points < 501:
                    print(
                        f"Insufficient datapoints for light_engine_id={le_id}, channel={i}, temp={temp} (expected {501}, found {n_points})"
                    )
                    # For now, we can just skip doing anything about
                    # insufficient number of points since these are most likely
                    # due to a measurement not being complete
                elif n_points > 501:
                    print(
                        f"Excess datapoints for light_engine_id={le_id}, channel={i}, temp={temp} (expected {501}, found {n_points})"
                    )
                    # In the event that we have too many datapoints, we need to
                    # separate the sweeps into complete and incomplete sweeps
                    query = (
                        sa.select(LightEngineMeasurement)
                        .where(LightEngineMeasurement.light_engine_id == le_id)
                        .where(LightEngineMeasurement.channel == i)
                        .where(LightEngineMeasurement.nominal_temp_c == temp)
                    )
                    df = pd.read_sql(query, session.bind)

                    # First try to separate the measurements by day
                    for name, sub_df in df.groupby(["date", "time"]):

                        # Delete any incomplete sweeps
                        if sub_df.shape[0] < 501:
                            print(f"Incomplete sweep found for sub-table {name}")
                            print(sub_df)
                            resp = input(
                                (
                                    f"""Delete entries {sub_df["measurement_id"].values[0]} """
                                    f"""through {sub_df["measurement_id"].values[-1]}? [y/N]: """
                                )
                            )
                            if resp.lower() == "y":
                                print("Deleting entries ... ", flush=True, end="")
                                stmt = sa.delete(LightEngineMeasurement).where(
                                    LightEngineMeasurement.measurement_id.in_(
                                        sub_df["measurement_id"].values
                                    )
                                )
                                session.execute(stmt)
                                session.commit()
                                print("Completed.")
                            else:
                                print("Skipping delete.")
