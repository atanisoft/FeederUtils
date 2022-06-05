#
# SPDX-FileCopyrightText: 2022 Mike Dunston (atanisoft)
#
# SPDX-License-Identifier: MIT
#
# This script will create multiple ReferenceSlotAutoFeeder instances based
# on provided parameters. In the case of 0816 feeders it will also create
# the necessary actuators (2mm, 4mm and post-pick) and the Gcode driver.
#
# The ReferenceSlotAutoFeeder instances will only be partially configured
# in that they will have a default offset (X, Y) and will require fine
# tuning to accurately configure the locations. The orientation will be set
# to zero and should be configured on the parts themselves rather than
# on the ReferenceSlotAutoFeeder instances.
#
# After this script has run you can attach a QR code or bar code to the
# feeders and use the scan-feeders-for-part-labels.py script to automatically
# assign Feeders/Parts to the ReferenceSlotAutoFeeder instances prior to
# running a job.
#

from org.openpnp.model import Configuration, Location
from org.openpnp.machine.reference import ReferenceActuator
from org.openpnp.machine.reference.driver import GcodeDriver
from org.openpnp.machine.reference.feeder import ReferenceAutoFeeder, ReferenceSlotAutoFeeder
from org.openpnp.spi import Actuator
from org.openpnp.model import LengthUnit

# Pick location to assign to the first feeder, additional feeders will be
# adjusted based on the feeder offsets defined below.
feeder_starting_pick_location_x = 0
feeder_starting_pick_location_y = 10

# Offset to apply to the pick location for the next feeder.
feeder_offset_x = 15
feeder_offset_y = 0

# Number of feeders to create.
feeder_count = 28

# When set to True all registered parts will have a feeder created in the
# default bank. This is not the same as a slotted feeder.
use_part_id_for_feeder = True

# Set this to True to use the AVR based 0816 Feeder Controller. When set to
# False the ESP32 controller is used.
use_avr_controller = True

# Set this to True to configure feeders as ReferenceSlotAutoFeeder. When set
# to False the feeders will be created as ReferenceAutoFeeder instead.
use_slotted_feeders = True

######## END OF USER MODIFYABLE SETTINGS ########

# Gcode commands for the Esp32FeederController.
#
# The Esp32FeederController uses a single actuator for advancing the parts,
# the distance to be moved should be configured on the controller itself.
esp32_feeder_advance = 'M610 N{IntegerValue}'
esp32_feeder_advance_actuator = 'FeederAdvance'
esp32_feeder_postpick = 'M611 N{IntegerValue}'
esp32_postpick_actuator = 'FeederPostPick'
esp32_gcode_driver = 'Esp32FeederController'

# Gcode commands for the AVR based Feeder Controller
#
# The AVR FeederController defaults to a 4mm advancement, if a 2mm advancement
# is needed, the assigned actuator should be changed to the 2mm version.
avr_feeder_advance_2mm = 'M600 N{IntegerValue} F2'
avr_actuator_2mm = 'FeederAdvance2MM'
avr_feeder_advance_4mm = 'M600 N{IntegerValue} F4'
avr_actuator_4mm = 'FeederAdvance4MM'
avr_feeder_postpick = 'M601 N{IntegerValue}'
avr_postpick_actuator = 'FeederPostPick'
avr_feeder_enable = 'M610 S1'
avr_feeder_disable = 'M610 S0'
avr_gcode_driver = 'FeederController'

def find_slotted_feeder(name):
    for feeder in machine.getFeeders():
        if feeder.getName().startswith('{} ('.format(name)):
            return feeder
    return None

def find_or_create_slotted_feeder(name, bank):
    feeder = find_slotted_feeder(name)
    if not feeder:
        print('Creating ReferenceSlotAutoFeeder \'{}\''.format(name))
        feeder = ReferenceSlotAutoFeeder()
        feeder.setName(name)
        feeder.setBank(bank)
        machine.addFeeder(feeder)
    else:
        print('Updating ReferenceSlotAutoFeeder \'{}\''.format(feeder.getName()))
    return feeder

def find_feeder_in_bank(name, bank):
    for feeder in bank.getFeeders():
        if feeder.getName() == name:
            return feeder
    return None

def find_actuator_by_name(name):
    for act in machine.getActuators():
        if act.getName() == name:
            return act
    return None

def find_or_create_0816_actuator(name, driver):
    act = find_actuator_by_name(name)
    if not act:
        print('Creating Actuator \'{}\''.format(name))
        act = ReferenceActuator()
        act.setValueType(Actuator.ActuatorValueType.Double)
        act.setName(name)
        act.setDriver(driver)
        machine.addActuator(act)
    return act

def find_or_create_0816_gcode_driver(driver_name):
    target_driver = None
    for driver in machine.getDrivers():
        if driver.getName() == driver_name:
            target_driver = driver
    if not target_driver:
        print('Creating GCode driver \'{}\''.format(driver_name))
        target_driver = GcodeDriver()
        target_driver.setName(driver_name)
        machine.addDriver(target_driver)
    return target_driver

def create_auto_feeders(count, start_x, start_y, offset_x, offset_y, feed_actuator, postpick_actuator):
    # Create N feeders ReferenceSlotAutoFeeder
    for id in range(0, count):
        feeder = ReferenceAutoFeeder('Feeder-{}'.format(id))
        feeder.setLocation(Location(LengthUnit.Millimeters, start_x + (offset_x * id), start_y + (offset_y * id), 0, 0))
        feeder.setActuatorName(feed_actuator)
        feeder.setActuatorValue(id)
        feeder.setPostPickActuatorName(postpick_actuator)
        feeder.setPostPickActuatorValue(id)
        machine.addFeeder(feeder)

def create_slotted_feeders(count, start_x, start_y, offset_x, offset_y, feed_actuator, postpick_actuator):
    # Get (or create) the default bank for the feeders.
    bank = ReferenceSlotAutoFeeder.getBanks()[0]
    # Create N feeders ReferenceSlotAutoFeeder
    for id in range(0, count):
        slot = find_or_create_slotted_feeder('SLOT-{}'.format(id), bank)
        slot.setLocation(Location(LengthUnit.Millimeters, start_x + (offset_x * id), start_y + (offset_y * id), 0, 0))
        slot.setActuatorName(feed_actuator)
        slot.setActuatorValue(id)
        slot.setPostPickActuatorName(postpick_actuator)
        slot.setPostPickActuatorValue(id)

def configure_0816_feeder_gcode(driver_name, advance_gcode_2mm, feed_actuator_2mm, advance_gcode_4mm, feed_actuator_4mm, postpick_gcode, postpick_actuator, enable_gcode = None, disable_gcode = None):
    driver = find_or_create_0816_gcode_driver(driver_name)
    if advance_gcode_2mm != None and len(advance_gcode_2mm) > 0:
        act = find_or_create_0816_actuator(feed_actuator_2mm, driver)
        print('{}: Setting Gcode for Actuator \'{}\''.format(driver_name, feed_actuator_2mm))
        driver.setCommand(act, GcodeDriver.CommandType.ACTUATE_DOUBLE_COMMAND, advance_gcode_2mm)
    if advance_gcode_4mm != None and len(advance_gcode_4mm) > 0:
        act = find_or_create_0816_actuator(feed_actuator_4mm, driver)
        print('{}: Setting Gcode for Actuator \'{}\''.format(driver_name, feed_actuator_4mm))
        driver.setCommand(act, GcodeDriver.CommandType.ACTUATE_DOUBLE_COMMAND, advance_gcode_4mm)
    postpick_act = find_or_create_0816_actuator(postpick_actuator, driver)
    print('{}: Setting Gcode for Actuator \'{}\''.format(driver_name, postpick_actuator))
    driver.setCommand(postpick_act, GcodeDriver.CommandType.ACTUATE_DOUBLE_COMMAND, postpick_gcode)
    print('{}: Setting Gcode COMMAND_CONFIRM_REGEX'.format(driver_name))
    driver.setCommand(None, GcodeDriver.CommandType.COMMAND_CONFIRM_REGEX, '^ok.*')
    print('{}: Setting Gcode COMMAND_ERROR_REGEX'.format(driver_name))
    driver.setCommand(None, GcodeDriver.CommandType.COMMAND_ERROR_REGEX, '^error.*')
    if enable_gcode:
        print('{}: Setting Gcode ENABLE_COMMAND'.format(driver_name))
        driver.setCommand(None, GcodeDriver.CommandType.ENABLE_COMMAND, enable_gcode)
    if disable_gcode:
        print('{}: Setting Gcode DISABLE_COMMAND'.format(driver_name))
        driver.setCommand(None, GcodeDriver.CommandType.DISABLE_COMMAND, disable_gcode)

if use_avr_controller:
    configure_0816_feeder_gcode(avr_gcode_driver,
        avr_feeder_advance_2mm, avr_actuator_2mm,
        avr_feeder_advance_4mm, avr_actuator_4mm,
        avr_feeder_postpick, avr_postpick_actuator,
        avr_feeder_enable, avr_feeder_disable)
    if use_slotted_feeders:
        create_slotted_feeders(feeder_count,
            feeder_starting_pick_location_x, feeder_starting_pick_location_y,
            feeder_offset_x, feeder_offset_y, avr_actuator_4mm,
            avr_postpick_actuator)
    else:
        create_auto_feeders(feeder_count,
            feeder_starting_pick_location_x, feeder_starting_pick_location_y,
            feeder_offset_x, feeder_offset_y, avr_actuator_4mm,
            avr_postpick_actuator)
else:
    configure_0816_feeder_gcode(esp32_gcode_driver,
        esp32_feeder_advance, esp32_feeder_advance_actuator,
        None, None, # ESP32 only uses one feeder actuator
        esp32_feeder_postpick, esp32_postpick_actuator,
        None, None) # ESP32 does not use a global enable
    if use_slotted_feeders:
        create_slotted_feeders(feeder_count,
            feeder_starting_pick_location_x, feeder_starting_pick_location_y,
            feeder_offset_x, feeder_offset_y, esp32_feeder_advance_actuator,
            esp32_postpick_actuator)
    else:
        create_auto_feeders(feeder_count,
            feeder_starting_pick_location_x, feeder_starting_pick_location_y,
            feeder_offset_x, feeder_offset_y, esp32_feeder_advance_actuator,
            esp32_postpick_actuator)

if use_slotted_feeders:
    bank = ReferenceSlotAutoFeeder.getBanks()[0]
    if use_part_id_for_feeder:
        for part in Configuration.get().getParts():
            if not find_feeder_in_bank(part.getId(), bank):
                print('Creating feeder for part \'{}\''.format(part.getId()))
                feeder = ReferenceSlotAutoFeeder.Feeder()
                feeder.setName(part.getId())
                feeder.setPart(part)
                part_x = part.getPackage().getFootprint().getBodyWidth() / 2.0 if part.getPackage().getFootprint().getBodyWidth() > 0.0 else 0.0
                part_y = part.getPackage().getFootprint().getBodyHeight() / 2.0 if part.getPackage().getFootprint().getBodyHeight() > 0.0 else 0.0
                part_z = part.getHeight().getValue()
                part_rotation = 0
                print('[{}] pick offset: x:{}, y:{}, z:{}'.format(part.getId(), part_x, part_y, part_z))
                part_size = Location(LengthUnit.Millimeters, part_x, part_y, part_z, part_rotation)
                feeder.setOffsets(feeder.getOffsets().add(part_size))
                bank.getFeeders().add(feeder)
    else:
        for id in range(0, feeder_count):
            name = 'Feeder-{}'.format(id)
            feeder = find_feeder_in_bank(name, bank)
            if not feeder:
                print('Creating feeder \'{}\''.format(name))
                feeder = ReferenceSlotAutoFeeder.Feeder()
                feeder.setName(name)
                feeder.setPart(Configuration.get().getPart('HOMING-FIDUCIAL'))
                bank.getFeeders().add(feeder)
    gui.getFeedersTab().repaint()