from pymeasure.instruments import Instrument
from pymeasure.instruments.generic_types import SCPIMixin
from pymeasure.instruments.validators import strict_discrete_set


class TECSource5240(SCPIMixin, Instrument):
    """Control the Arroyo TEC Source 5240 controller."""

    def __init__(self, adapter, name="TEC Source 5240", **kwargs):
        kwargs.setdefault("baud_rate", 38400)
        kwargs.setdefault("read_termination", "\n")
        kwargs.setdefault("write_termination", "\n")
        super().__init__(adapter, name, **kwargs)

        self.temperature = Instrument.control(
            "TEC:T?",
            "TEC:T %g",
            """The temperature of the TEC.
            
            Setting this property sets the temperature set point, getting this property 
            returns the actual temperature.
            """,
            get_process=lambda v: float(v),
        )

        self.output_enabled = Instrument.control(
            "TEC:OUT?",
            "TEC:OUT %d",
            """Whether the instrument output is enabled (boolean).""",
            validator=strict_discrete_set,
            map_values=True,
            values={True: 1, False: 0},
        )
