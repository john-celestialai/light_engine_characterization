from pymeasure.instruments import Instrument
from pymeasure.instruments.generic_types import SCPIMixin
from pymeasure.instruments.validators import strict_discrete_set
from time import sleep


class LDDSource7144(SCPIMixin, Instrument):
    """Control the Arroyo 4 Channel 7144 LDD controller."""

    def __init__(self, adapter, name="LDD Source 7144", **kwargs):
        kwargs.setdefault("baud_rate", 38400)
        kwargs.setdefault("read_termination", "\n")
        kwargs.setdefault("write_termination", "\n")
        kwargs.setdefault("timeout", 10000)
        super().__init__(adapter, name, **kwargs)

    ########### Instrument Parameters ################################################
    output_enabled = Instrument.control(
        "LAS:OUT?",
        "LAS:OUT %d",
        """Whether the instrument output is enabled (boolean).""",
        validator=strict_discrete_set,
        map_values=True,
        values={True: 1, False: 0},
    )

    completed = Instrument.control("*OPC?", "*OPC", """Operation complete bit in the event status register.""")

    channel = Instrument.control(
        "LAS:CHAN?", "LAS:CHAN %d", """Laser controller channel.""", validator=strict_discrete_set, values=[1, 2, 3, 4],
    )

    current = Instrument.control(
        "LAS:LDI?", "LAS:LDI %d", """Laser current [mA]."""
    )

    voltage = Instrument.control(
        "LAS:LDV?", "LAS:LDV %d", """Laser forward voltage [V]."""
    )

    tolerance = Instrument.control("LAS:TOL?", "LAS:TOL %f, 2", """Laser current tolerance criteria.""")

    def set_current(self, current):
        self.current = current
        sleep(0.1)
        while not self.completed:
            sleep(0.1)

        self.current
        sleep(0.1)
        # if abs(self.current - current) > 0.1:
        #     raise ValueError("LDD current did not settle within tolerance time")


if __name__ == "__main__":
    from time import sleep

    ldd = LDDSource7144('ASRL5::INSTR')
    ldd.tolerance = 0.1
    print(ldd.tolerance)
    ldd.current = 99
    ldd.output_enabled = True
    while not ldd.completed:
        sleep(0.1)

    for i in range(100, 110, 1):
        print(i)
        ldd.current = i

        sleep(0.1)
        while not ldd.completed:
            sleep(0.1)
        
        sleep(0.1)
        current = ldd.current
        if not current:
            current = ldd.current
        print(current)
        

    ldd.output_enabled = False
