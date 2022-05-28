#
# SPDX-FileCopyrightText: 2022 Mike Dunston (atanisoft)
#
# SPDX-License-Identifier: MIT
#
# This script iterates over all feeders looking for ReferenceSlotAutoFeeder
# feeders, positions the camera over the feeder and searches for a QR code
# or bar code label. If a label is successfully decoded the script will
# search for a feeder that supplies is configured for that part or a feeder
# with the same code as it's name.
#
# ReferenceSlotAutoFeeder instances will be enabled if a compatible feeder
# has been identified for the decoded label. If no compatible feeder is
# found the ReferenceSlotAutoFeeder will be disabled.
#

# These values are used as an offset from the pick location to find the code
# label.
#
# NOTE: This uses the same units as the pick location, typically millimeters.
label_offset_from_pick_location_x = 0
label_offset_from_pick_location_y = 10

######## END OF USER MODIFYABLE SETTINGS ########

from org.openpnp.machine.reference.feeder import ReferenceSlotAutoFeeder
from org.openpnp.model import Location
from org.openpnp.util import VisionUtils, MovableUtils
import javax.swing.JOptionPane as optPanel

def show_error_dialog(message, abort = True):
    optPanel.showMessageDialog(None, message)
    if abort:
        raise message

def find_feeder_for_part(part_name, bank):
    for feeder in bank.getFeeders():
        if feeder.getPart().getName() == part_name or feeder.getName() == part_name:
            return feeder
    return None

# If the machine is not enabled VisionUtils will report an error
if not machine.isEnabled():
    show_error_dialog('This script requires the machine to be started!')

# Use the default camera (usually top mounted) for scanning codes
camera = machine.getDefaultHead().getDefaultCamera()

if not camera:
    show_error_dialog('Unable to locate default camera')

# Scan all registered feeders to find all ReferenceSlotAutoFeeder instances
for feeder in machine.getFeeders():
    if 'ReferenceSlotAutoFeeder' in str(feeder):
        try:
            # Determine the location of the code based on the pick location of the feeder
            pick_location = feeder.getPickLocation()
            label_location = pick_location.add(Location(pick_location.getUnits(),
                label_offset_from_pick_location_x, label_offset_from_pick_location_y,
                pick_location.getZ(), pick_location.getRotation()))

            # move to the code location
            MovableUtils.moveToLocationAtSafeZ(camera, label_location)

            # attempt to decode a QR or bar code
            code = VisionUtils.readQrCode(camera)
            if code and len(code) > 0:
                print('Detected part code as \'{}\', looking for matching feeder'.format(code))
                part = find_feeder_for_part(code, feeder.getBank())
                if part:
                    print('Found feeder \'{}\' with part \'{}\''.format(part.getName(), part.getPart()))
                    feeder.setFeeder(part)
                    feeder.setEnabled(True)
                else:
                    print('No part feeder found for code \'{}\', disabling feeder'.format(code))
                    feeder.setEnabled(False)
        except:
            print('Failed to read QR code for feeder \'{}\''.format(feeder.getName()))
            feeder.setEnabled(False)
            raise

# repaint the feeders tab since we have updated the feeders
gui.getFeedersTab().repaint()
