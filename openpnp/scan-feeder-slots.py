from org.openpnp.machine.reference.feeder import ReferenceSlotAutoFeeder
from org.openpnp.util import VisionUtils

def find_feeder_in_bank_for_part(part_name, bank):
    for feeder in bank.getFeeders():
        if feeder.getPart() == part_name or getName() == part_name:
            return feeder
    return None

if not machine.isEnabled():
    raise 'This script requires the machine to be started!'

default_camera = machine.getDefaultHead().getDefaultCamera()
bank = ReferenceSlotAutoFeeder.getBanks()[0]
for feeder in machine.getFeeders():
    if 'ReferenceSlotAutoFeeder' in str(feeder):
        try:
            default_camera.moveTo(feeder.getPickLocation())
            code = VisionUtils.readQrCode(default_camera)
            if code and len(code) > 0:
                print('QR: {}'.format(code))
                banked_feeder = find_feeder_in_bank_for_part(code, bank)
                if banked_feeder:
                    print('Found feeder {} with part {}'.format(banked_feeder.getName(), banked_feeder.getPart()))
                    feeder.setFeeder(banked_feeder)
        except:
            print('Failed to read QR code for feeder {}'.format(feeder.getName()))
            pass
