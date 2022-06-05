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
# This offset should be orientated for 0deg rotated feeders, for other
# rotations enable the option below and the offsets will be adjusted
# accordingly.
#
# NOTE: This uses the same units as the pick location, typically millimeters.
label_offset_from_pick_location_x = 0
label_offset_from_pick_location_y = 10

# Enabling this option will translate the label offset based on feeder
# rotation:
#
# rotation  : adjustment
#   0       : none.
#  90       : negate and swap x and y.
# 180       : negate y.
# 270       : swap both x and y.
#
# examples:
# 
# feeder mounted at 0deg rotation (front side of machine):
# pick position  : x: 100, y: 0
# label position : x: 100, y: 0
#
# feeder mounted at 90deg rotation (right side of machine):
# pick position  : x: 100, y: 100
# label position : x: 90, y: 100 (calculated)
#
# feeder mounted at 180deg rotation (back side of machine):
# pick position  : x: 0, y: 100
# label position : x: 0, y: 90 (calculated)
#
# feeder mounted at 270deg rotation (left side of machine):
# pick position  : x: 0, y: 100
# label position : x: 10, y: 100 (calculated)
#
translate_offsets_based_on_orientation = True

# When this is set to True, if a part label is not detected or the detected
# part does not exist in OpenPnP the feeder will be disabled.
disable_feeders_without_parts = True

# When this option is set to True and a part label does not match an existing
# part, the script will prompt for which package to use for the part and then
# create it.
#
# NOTE: When no packages are defined this will be disabled automatically.
create_missing_parts = True

######## END OF USER MODIFYABLE SETTINGS ########

from org.openpnp.machine.reference.feeder import ReferenceSlotAutoFeeder
from org.openpnp.model import Configuration, Length, LengthUnit, Location, Part
from org.openpnp.util import VisionUtils, MovableUtils
import javax.swing.JOptionPane as optPanel

def show_error_dialog(message, abort = True):
    if abort:
        raise Exception(message)
    else:
        optPanel.showMessageDialog(None, message)

def get_user_confirmation(message, title):
    response = optPanel.showConfirmDialog(None, message, title,
                                          optPanel.YES_NO_OPTION)
    return response == optPanel.YES_OPTION

def find_feeder_in_bank_for_part(part, bank):
    print('Serching for part {}'.format(part))
    for feeder in bank.getFeeders():
        if (feeder.getPart() and feeder.getPart().getId() == part.getId()) or feeder.getName() == part.getName():
            return feeder
    return None

def get_package_from_user(part_name):
    packages = []
    for package in Configuration.get().getPackages():
        packages.append(package.getId())
    if len(packages):
        response = optPanel.showInputDialog(None,
                                            'Please select package to use for \'{}\':'.format(part_name),
                                            'Select package for part',
                                            optPanel.DEFAULT_OPTION,
                                            None,
                                            packages, packages[0])
        if response is not None:
            for package in Configuration.get().getPackages():
                if package.getId() == response:
                    return package
    return None

def find_part_for_label(camera, feeder_name, location):
    detected_part = None
    try:
        print('[{}] Moving camera to part label location: {}'.format(feeder_name, location))
        MovableUtils.moveToLocationAtSafeZ(camera, location)

        print('[{}] Attempting to read part label'.format(feeder_name))
        value = VisionUtils.readQrCode(camera)
        if value and len(value):
            print('[{}] Detected as \'{}\', looking for matching part'.format(feeder_name, value))
            for part in Configuration.get().getParts():
                if part.getName() == value or part.getId() == value:
                    detected_part = part
            if not detected_part:
                print('[{}] Unable to locate part with matching name/id'.format(feeder_name))
                if create_missing_parts and get_user_confirmation('Would you like to create part {}?'.format(value), 'Create new part?'):
                    package = get_package_from_user(value)
                    if package:
                        detected_part = Part(value)
                        detected_part.setName(value)
                        detected_part.setPackage(package)
                        detected_part.setHeight(Length(0.0, LengthUnit.Millimeters))
                        Configuration.get().addPart(detected_part)
                        gui.getPartsTab().repaint()
        else:
            print('[{}] No label detected'.format(feeder_name))
    except Exception as ex:
        print('[{}] Failed to read label, {}'.format(feeder_name, ex))

    return detected_part

def get_label_location(feeder_name, pick_location):
    label_offset_x = label_offset_from_pick_location_x
    label_offset_y = label_offset_from_pick_location_y
    rotation = pick_location.getRotation()
    if translate_offsets_based_on_orientation:
        if rotation == 90:
            label_offset_x = label_offset_from_pick_location_y * -1
            label_offset_y = label_offset_from_pick_location_x * -1
        elif rotation == 180:
            label_offset_y = label_offset_from_pick_location_y * -1
        elif rotation == 270:
            label_offset_x = label_offset_from_pick_location_y
            label_offset_y = label_offset_from_pick_location_x
    label_location = pick_location.add(Location(pick_location.getUnits(),
                                       label_offset_x,
                                       label_offset_y,
                                       pick_location.getZ(),
                                       rotation))
    print('[{}] pick-location:{}, label-location:{}'.format(feeder_name, pick_location, label_location))
    return label_location

# If the machine is not enabled VisionUtils will report an error
if not machine.isEnabled():
    show_error_dialog('This script requires the machine to be started!')

# Use the default camera (usually top mounted) for scanning codes
camera = machine.getDefaultHead().getDefaultCamera()

if not camera:
    show_error_dialog('Unable to locate default camera')

# Sanity check for parts creation, if there are no packages defined disable the
# option
if create_missing_parts and not len(Configuration.get().getPackages()):
    print('Unable to find any packages to use for part creation, disabling')
    create_missing_parts = False

# Scan all registered feeders, if a code can be detected the assigned part will be updated
for feeder in machine.getFeeders():
    feeder_name = feeder.getName()
    label_location = get_label_location(feeder_name, feeder.getPickLocation())
    if 'ReferenceSlotAutoFeeder' in str(feeder) and feeder.getFeeder():
        label_location = label_location.subtract(feeder.getFeeder().getOffsets())
        print('[{}] is a slotted feeder, adjusted label location:{}'.format(feeder_name, label_location))

    # Try and detect a part via code label
    detected_part = find_part_for_label(camera, feeder_name, label_location)

    # If a part code was successfully detected and converted to a part check and
    # update the assigned feeder/part or optionally disable the feeder.
    if detected_part:
        if 'ReferenceSlotAutoFeeder' in str(feeder) or 'SlotSchultzFeeder' in str(feeder):
            part_feeder = find_feeder_in_bank_for_part(detected_part, feeder.getBank())
            if part_feeder:
                print('[{}] Setting part feeder to \'{}\''.format(feeder_name, part_feeder.getName()))
                feeder.setFeeder(part_feeder)
                feeder.setEnabled(True)
            elif create_missing_parts and get_user_confirmation('Would you like to create feeder for part {}?'.format(detected_part.getId()), 'Create new feeder?'):
                if 'ReferenceSlotAutoFeeder' in str(feeder):
                    part_feeder = ReferenceSlotAutoFeeder.Feeder()
                else:
                    part_feeder = SlotSchultzFeeder.Feeder()
                part_feeder.setName(detected_part.getId())
                part_feeder.setPart(detected_part)
                part_x = detected_part.getPackage().getFootprint().getBodyWidth() / 2.0 if detected_part.getPackage().getFootprint().getBodyWidth() > 0.0 else 0.0
                part_y = detected_part.getPackage().getFootprint().getBodyHeight() / 2.0 if detected_part.getPackage().getFootprint().getBodyHeight() > 0.0 else 0.0
                part_z = detected_part.getHeight().getValue()
                part_rotation = 0
                print('[{}] {} pick offset: x:{}, y:{}, z:{}'.format(feeder_name, detected_part.getId(), part_x, part_y, part_z))
                part_size = Location(LengthUnit.Millimeters, part_x, part_y, part_z, part_rotation)
                part_feeder.setOffsets(part_feeder.getOffsets().add(part_size))
                feeder.getBank().getFeeders().add(part_feeder)
                print('[{}] Setting part feeder to \'{}\''.format(feeder_name, part_feeder.getName()))
                feeder.setFeeder(part_feeder)
                feeder.setEnabled(True)
            elif disable_feeders_without_parts:
                print('[{}] Unable to find feeder for part, disabling feeder'.format(feeder_name))
                feeder.setEnabled(False)
        elif feeder.getPart().getId() != detected_part.getId():
            print('[{}] Updating part \'{}\''.format(feeder_name, detected_part.getName()))
            feeder.setPart(detected_part)
    else:
        print('[{}] No part code detected'.format(feeder_name))
        if disable_feeders_without_parts:
            print('[{}] Disabling feeder'.format(feeder_name))
            feeder.setEnabled(False)

# repaint the feeders tab since we have updated the feeders
gui.getFeedersTab().repaint()
