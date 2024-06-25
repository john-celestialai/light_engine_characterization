"""Drive for Agiltron MSWH 1xN Single mode optical switch series.

Control for the optical switch is implemented through the Labjack T7 digital I/O.
"""

import time

from labjack import ljm
from pymeasure.instruments import Instrument
from pymeasure.instruments.generic_types import SCPIMixin
from pymeasure.instruments.validators import strict_discrete_set


class OpticalSwitch:
    """Agiltron MEMS optical switch."""

    labjack_device = "T7"

    def __init__(self, *args) -> None:
        super().__init__(*args)
        self.handle = None

    def open(self) -> None:
        """Open a connection to the Labjack to control the optical switch."""
        self.handle = ljm.openS(self.labjack_device, "ANY", "ANY")

    def close(self) -> None:
        """Close the connection to the Labjack."""
        ljm.close(self.handle)
        self.handle = None

    def configure(self) -> None:
        """Configuration for Labjack and optical switch."""
        # Set DIO3 high to prevent switch reset
        ljm.eWriteName(self.handle, "DIO3", 1)

    def reset(self) -> None:
        """Reset the labjack and the optical switch."""
        # Reboot the labjack
        ljm.eWriteAddress(self.handle, 61998, ljm.constants.UINT32, 0x4C4A0000)
        time.sleep(0.5)

        # Pull DIO3 low for >4ms to reset optical switch
        ljm.eWriteName(self.handle, "DIO3", 0)
        time.sleep(0.01)
        ljm.eWriteName(self.handle, "DIO3", 1)

    def get_channel(self) -> int:
        """Get the current switch input channel.

        The switch channel is determined by querying the Labjack DAC[0:2]
        states.
        """

        names = [f"DIO{i}" for i in range(3)]
        states = ljm.eReadNames(self.handle, len(names), names)
        return sum([int(j * 2**i) for i, j in enumerate(states)])

    def set_channel(self, channel, check) -> None:
        """Select the switch input channel.

        The switch channel is selected by setting bits D[0:2] on the switch
        digital I/O, which are driven through the Labjack.

        channel: int, which input channel to select
        check: bool, check if the operation has completed
        """

        names = [f"DIO{i}" for i in range(3)]
        states = [int(i) for i in reversed(list(f"{channel:03b}"))]
        ljm.eWriteNames(self.handle, len(names), names, states)

        if check:
            done = False
            while not done:
                done = ljm.eReadName(self.handle, "DIO4")
                time.sleep(0.25)


if __name__ == "__main__":
    # Connect to the Labjack and iterate through all switch settings
    switch = OpticalSwitch()
    switch.open()
    switch.reset()
    print(switch.get_channel())
    for i in range(8):
        print(f"Switching channel to {i}")
        switch.set_channel(i)
        print()
        print("Reading current channel")
        print(switch.get_channel())
        print()
    switch.close()
