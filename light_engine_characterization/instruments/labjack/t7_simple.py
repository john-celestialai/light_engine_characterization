import sys

from labjack import ljm

handle1 = ljm.openS("T7", "USB", "ANY")

info = ljm.getHandleInfo(handle1)
print(
    "Opened a LabJack with Device type: %i, Connection type: %i,\n"
    "Serial number: %i, IP address: %s, Port: %i,\nMax bytes per MB: %i"
    % (info[0], info[1], info[2], ljm.numberToIP(info[3]), info[4], info[5])
)

deviceType = info[0]

if deviceType == ljm.constants.dtT4:
    print("\nThe LabJack T4 does not support triggered stream.")
    sys.exit()

try:
    ljm.eStreamStop(handle=handle1)
except Exception as e:
    print("Not a problem:", e)
    pass

# Read the voltage on AIN0
voltage = ljm.eReadName(handle1, "AIN0")

print("volts:", voltage)

# Streaming data below

# https://support.labjack.com/docs/estreamstart-ljm-user-s-guide
# stream1 = ljm.eStreamStart(handle=handle1, scansPerRead=4, numAddresses=1, aScanList=["AIN0"], scanRate=10)
stream1 = ljm.eStreamStart(
    handle=handle1, scansPerRead=4, numAddresses=1, aScanList=[0], scanRate=10
)
read1 = ljm.eStreamRead(handle=handle1)
ljm.eStreamStop(handle=handle1)
print("read1: ", read1)
