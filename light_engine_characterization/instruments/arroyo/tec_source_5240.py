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

    ########### Instrument Parameters ################################################
    temperature = Instrument.control(
        "TEC:T?",
        "TEC:T %g",
        """The temperature of the TEC.
        
        Setting this property sets the temperature set point, getting this property 
        returns the actual temperature.
        """,
        get_process=lambda v: float(v),
    )

    output_enabled = Instrument.control(
        "TEC:OUT?",
        "TEC:OUT %d",
        """Whether the instrument output is enabled (boolean).""",
        validator=strict_discrete_set,
        map_values=True,
        values={True: 1, False: 0},
    )
    
    pid_params = Instrument.measurement(
        "TEC:PID?",
        """PID coefficients used for control loop.""",
        get_process=lambda x: [float(v) for v in x]
    )
        
    def set_temperature(self, temperature):
        self.write(f'TEC:T {temperature}')

    def get_temperature(self):
        temperature = self.ask(f'TEC:T?')
        return float(temperature)
        
    def set_output_on(self):
        self.write(f'TEC:OUTput {1}')
    
    def set_output_off(self):
        self.write(f'TEC:OUTput {0}')
        
    def get_pid_params(self):
        return self.ask("TEC:PID?")


if __name__ == "__main__":
    tec = TECSource5240('ASRL4::INSTR')
    print(tec.pid_params)