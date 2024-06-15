import time
import traceback

import paramiko
from paramiko import SSHClient
from paramiko_expect import SSHClientInteraction


class ZeusController:
    """Class for interfacing with the Zeus controller board over SSH.

    TODO: Convert this class to use the pymeasure Instrument base class.
    """

    client: SSHClient

    def __init__(self):
        pass

    def open_session(self, HOSTNAME_PYNQ="pynq not set"):  # example 'pynq4'
        HOSTNAME = HOSTNAME_PYNQ  # example 'pynq4'
        USERNAME = "xilinx"
        PASSWORD = "xilinx"
        sudo_prompt = ".*\#\s+"
        PROMPT = ".*\$\s+"

        # Use SSH client to login
        try:
            # Create a new SSH client object
            client = paramiko.SSHClient()
            self.client = client

            # Set SSH key parameters to auto accept unknown hosts
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            if True:
                client.connect(hostname=HOSTNAME, username=USERNAME, password=PASSWORD)
            if False:
                mySSHK = "/path/to/sshkey.pub"
                mySSHK = "/id_rsa_pynq9.pub"
                mySSHK = "id_rsa_pynq9.pub"
                mySSHK = r"C:\Users\cdavies\.ssh\id_rsa.pub"  # this worked consistently Jan 29
                client.connect(
                    hostname=HOSTNAME, username=USERNAME, key_filename=mySSHK
                )

            # Create a client interaction class which will interact with the host
            interact = SSHClientInteraction(client, timeout=6, display=False)
            self.interact = interact

            time.sleep(0.1)  # do not remove
            # print("\n\n\nsending login for sudo-------- \n")
            interact.send(f"sudo -i")
            time.sleep(0.1)  # do not remove

            interact.send("xilinx")
            interact.expect([PROMPT, sudo_prompt, "password for xilinx.*\:"])
            interact.send(r"source /usr/local/share/pynq-venv/bin/activate")
            interact.expect([PROMPT, sudo_prompt, "password for xilinx.*\:"])
            PYTHON_PROMPT = r"(>>> )"
            interact.send("python3")
            time.sleep(0.3)  # wait for python to come up
            interact.expect([PYTHON_PROMPT, "/[>]", PROMPT, sudo_prompt])
            interact.send(r"import time")
            interact.expect(PYTHON_PROMPT)

            interact.send("from artemis2 import *")
            interact.expect(PYTHON_PROMPT)
            interact.send("power.bypass_asic_check(True)")
            interact.expect(PYTHON_PROMPT)
            interact.send("power.init(TargetRate.Gbps56_0)")
            interact.expect(PYTHON_PROMPT)

            if False:
                print(interact.current_output_clean)

        except Exception:
            traceback.print_exc()
        self.interact = interact

    def write_only(self, command="pwd"):
        PYTHON_PROMPT = r"(>>> )"
        self.interact.send(rf"{command}")
        self.interact.expect(PYTHON_PROMPT)

    def write_read(self, command="pwd"):
        PYTHON_PROMPT = r"(>>> )"
        self.interact.send(rf"{command}")
        answer = self.interact.expect(PYTHON_PROMPT)
        return answer

    def get_light_engine_temperatures(self):
        self.write_read("temperature.print_all()")
        readframe = self.interact.current_output_clean
        Ambient_C = float(readframe.split(" ")[1].split("°C")[0])
        LE_C = float(readframe.split(" ")[4].split("°C")[0])
        return Ambient_C, LE_C

    def get_mpd_readout(self, Channel):
        query_string = "adc.LE_MPD_IMON_" + str(Channel) + ".print()"
        self.write_read(query_string)
        answer = self.interact.current_output_clean
        mpd_mA = float(answer.split(" ")[1].split("°C")[0])
        return mpd_mA

    def get_voltage_readout(self, channel):
        adc_lut = [
            "A_LDO_NCCMN",
            "A_LDO_ECCMN",
            "A_LDO_SCCMN",
            "A_LDO_WCCMN",
            "NE_PIC_APROBE_1",
            "NE_PIC_APROBE_2",
            "SW_PIC_APROBE_1",
            "SW_PIC_APROBE_2",
        ]
        query = f"adc.{adc_lut[channel]}.print()"
        self.write_read(query)
        answer = self.interact.current_output_clean
        voltage_v = float(answer.split(" ")[1].split("V")[0])
        return voltage_v

    def close(self):
        try:
            self.client.close()  # we dont want to close
        except Exception:
            print("trouble closing ssh client")


if __name__ == "__main__":
    import sys
    
    # HOSTNAME = "pynq4"  # example 'pynq4'
    # USERNAME = "xilinx"
    # PASSWORD = "xilinx"
    # sudo_prompt = ".*\#\s+"
    # PROMPT = ".*\$\s+"
    
    # client = paramiko.SSHClient()

    # # Set SSH key parameters to auto accept unknown hosts
    # client.load_system_host_keys()
    # client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # client.connect(hostname=HOSTNAME, username=USERNAME, password=PASSWORD)
    # interact = SSHClientInteraction(client, timeout=6, display=False)
    # interact.send(f"sudo -i")
    
    # client.close()
    # sys.exit()
    
    zeus = ZeusController()
    zeus.open_session("pynq1")
    zeus.write_read("fan.set_le_duty_cycle(90)")
    time.sleep(0.1)
    for j in range(8):
        
        # print(f"Channel {j}")
        zeus.write_read(f"light_engine.set_laser_ma(LEChannel.LE{j},0)")
        # time.sleep(0.1)
        # voltages = [zeus.get_voltage_readout(i) for i in range(8)]
        # print(voltages)
        # time.sleep(0.1)
        # zeus.write_read(f"light_engine.set_laser_ma(LEChannel.LE{j},200)")
        # time.sleep(0.1)
        # voltages = [zeus.get_voltage_readout(i) for i in range(8)]
        # print(voltages)
        # time.sleep(0.1)
        # zeus.write_read(f"light_engine.set_laser_ma(LEChannel.LE{j},0)")
    zeus.close()
