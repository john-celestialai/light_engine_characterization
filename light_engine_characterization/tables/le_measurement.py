from datetime import datetime
from dataclasses import replace
import numpy as np
import sqlalchemy as sa
from psycopg2.extensions import AsIs, register_adapter
from sqlalchemy import ARRAY, Date, Float, Integer, Time, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

database_address = "postgresql://testwrite:Happy_photons@10.10.30.10:5432/john_dev"


# We have to tell psycopg2 how to handle numpy datatypes
def addapt_numpy_float64(numpy_float64):
    return AsIs(numpy_float64)


def addapt_numpy_int64(numpy_int64):
    return AsIs(numpy_int64)


def addapt_numpy_float32(numpy_float32):
    return AsIs(numpy_float32)


def addapt_numpy_int32(numpy_int32):
    return AsIs(numpy_int32)


def addapt_numpy_array(numpy_array):
    return AsIs(numpy_array.tolist())


register_adapter(np.float64, addapt_numpy_float64)
register_adapter(np.int64, addapt_numpy_int64)
register_adapter(np.float32, addapt_numpy_float32)
register_adapter(np.int32, addapt_numpy_int32)
register_adapter(np.ndarray, addapt_numpy_array)


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
    sweep_type: Mapped[str | None]


class TFCMeasurement(Base):
    __tablename__ = "tfc"
    __table_args__ = {"schema": "lightengine"}

    measurement_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    light_engine_id: Mapped[str] = mapped_column(String)
    date: Mapped[datetime.date] = mapped_column(Date)
    time: Mapped[datetime.time] = mapped_column(Time)
    bias_current_ma: Mapped[float]
    voltage_v: Mapped[float]
    tec_pid: Mapped[list | None] = mapped_column(ARRAY(Float), nullable=True)
    nominal_temp_c: Mapped[float]
    tec_temp_c: Mapped[float]
    wavelength_nm: Mapped[np.ndarray] = mapped_column(ARRAY(Float))
    power_dbm: Mapped[np.ndarray] = mapped_column(ARRAY(Float))
    wavelength_peak_nm: Mapped[float]
    power_peak_dbm: Mapped[float]
    smsr_db: Mapped[float | None]
    smsr_linewidth_nm: Mapped[float | None]
    linewidth_3db_nm: Mapped[float | None]
    linewidth_20db_nm: Mapped[float | None]


if __name__ == "__main__":
    engine = sa.create_engine(database_address)
    TFCMeasurement.__table__.drop(engine)
    TFCMeasurement.__table__.create(engine)
