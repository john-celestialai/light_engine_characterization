from datetime import datetime

import numpy as np
import sqlalchemy as sa
from sqlalchemy import ARRAY, Date, Float, Integer, Time
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

database_address = "postgresql://testwrite:Happy_photons@10.10.30.10:5432/john_dev"


class Base(DeclarativeBase):
    pass


class LightEngineMeasurement(Base):
    __tablename__ = "molex"
    __table_args__ = {"schema": "lightengine"}

    measurement_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    light_engine_id: Mapped[int] = mapped_column(Integer)
    channel: Mapped[int] = mapped_column(Integer)
    date: Mapped[datetime.date] = mapped_column(Date)
    time: Mapped[datetime.time] = mapped_column(Time)
    bias_current_ma: Mapped[float]
    voltage_v: Mapped[float]
    tec_pid: Mapped[list | None] = mapped_column(ARRAY(Float), nullable=True)
    nominal_temp_c: Mapped[float]
    tec_temp_c: Mapped[float]
    ambient_temp_c: Mapped[float]
    light_engine_temp_c: Mapped[float]
    mpd_current_ma: Mapped[float]
    wavelength_nm: Mapped[np.ndarray] = mapped_column(ARRAY(Float))
    power_dbm: Mapped[np.ndarray] = mapped_column(ARRAY(Float))
    power_uw: Mapped[np.ndarray] = mapped_column(ARRAY(Float))
    wavelength_peak_nm: Mapped[float]
    power_peak_dbm: Mapped[float]
    smsr_db: Mapped[float | None]
    smsr_linewidth_nm: Mapped[float | None]
    linewidth_3db_nm: Mapped[float | None]
    linewidth_20db_nm: Mapped[float | None]


# if __name__ == "__main__":
#     engine = sa.create_engine(database_address)
#     LightEngineMeasurement.__table__.drop(engine)
