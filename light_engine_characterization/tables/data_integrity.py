import sys
from datetime import datetime

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
                    .where(LightEngineMeasurement.sweep_type == "normal")
                )

                # If channel=0 and n_points=1002, then it is most likely
                # that the first sweep is a normal sweep and the second
                # sweep is a full power sweep
                if i == 0 and n_points == 1002:
                    query = (
                        sa.select(LightEngineMeasurement)
                        .where(LightEngineMeasurement.light_engine_id == le_id)
                        .where(LightEngineMeasurement.channel == i)
                        .where(LightEngineMeasurement.nominal_temp_c == temp)
                    )
                    df = pd.read_sql(query, session.bind)
                    df_groups = df.groupby(["date", "time"])

                    # If we have two groups and each group has 501 datapoints,
                    # then the first group is the normal sweep and the second
                    # group is the full_power sweep
                    if len(df_groups) == 2 and all(
                        [d.shape[0] == 501 for _, d in df_groups]
                    ):
                        print("Found probable normal and full_power sweeps.")
                        key_0, key_1 = list(df_groups.groups.keys())
                        key_0_dt = datetime.combine(key_0[0], key_0[1])
                        key_1_dt = datetime.combine(key_1[0], key_1[1])
                        if key_0_dt < key_1_dt:
                            # Key 1 belongs to the later entry
                            meas_ids = df_groups.get_group(key_1)[
                                "measurement_id"
                            ].values
                        else:
                            # Key 0 belongs to the later entry
                            meas_ids = df_groups.get_group(key_0)[
                                "measurement_id"
                            ].values

                        updates = [
                            {"measurement_id": meas_id, "sweep_type": "full_power"}
                            for meas_id in meas_ids
                        ]
                        session.execute(sa.update(LightEngineMeasurement), updates)
                        session.commit()

                elif n_points < 501:
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

                    # First try to separate the measurements by day/time and
                    # delete any incomplete sweeps
                    for name, sub_df in df.groupby(["date", "time"]):
                        # Delete any incomplete sweeps
                        if sub_df.shape[0] < 501:
                            print(f"Incomplete sweep found for sub-table {name}")
                            sub_df.sort_values(by="measurement_id", inplace=True)
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
                        else:
                            sub_df.sort_values(by="measurement_id", inplace=True)
                            print(name)
                            print(sub_df)
