from datetime import datetime

from sqlalchemy import Date, Integer, Time
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class LightEngineMeasurement(Base):
    __tablename__ = "light_engine"

    light_engine_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[datetime.date] = mapped_column(Date)
    time: Mapped[datetime.time] = mapped_column(Time)
    bias_current_ma: Mapped[float]
    voltage_v: Mapped[float]
    tec_temp_c: Mapped[float]
    ambient_temp_c: Mapped[float]
    light_engine_temp_c: Mapped[float]
    mpd_ma: Mapped[float]
    wavelength_nm: Mapped[float]
    power_dbm: Mapped[float]
    power_uw: Mapped[float]
    wavelength_peak_nm: Mapped[float]
    power_peak_nm: Mapped[float]
    smsr_db: Mapped[float | None]
    smsr_linewidth_nm: Mapped[float | None]
    linewidth_3db_nm: Mapped[float | None]
    linewidth_20db_nm: Mapped[float | None]


if __name__ == "__main__":
    print(LightEngineMeasurement.__table__.columns.keys())
