#
# SPDX-FileCopyrightText: 2022 Mike Dunston (atanisoft)
#
# SPDX-License-Identifier: MIT
#
# This script reads a KiCad 6.x PCB file and generates OpenPnP packages,
# parts and a board.xml file. This script should work with Python 3.8 or
# Python 3.9. KiCad 5.x PCB files may work but are not guaranteed.
#
# This script should be run with OpenPnP *NOT RUNNING*. A non-standalone
# version will be available for running within OpenPnP soon.
#
# For a trial run that does not modify OpenPnP be sure to add --read_only
# on the command line.
#
# By default all parts will be created without nozzle assignments, to
# assign one (or more) nozzles during part creation add --nozzle {name}
# on the command line.
#
# If you receive a warning about the board having an origin of 0,0 the parts
# placement offsets will very likely be inaccurate. To resolve this open your
# PCB in pcbnew and assign an origin to one corner of your PCB.
#
# NOTE: When opening the board.xml in OpenPnP it has been observed that some
# part assignments may not be honored. If you observe this it is likely the
# part name length being too long, you can add entries to parts.json to
# shorten package names or specify --use_value_for_part_id on the command
# line to shorten the part IDs even further.
#
# NOTE: If parts.json does not contain size data for a given part it will be
# defaulted to 0mm in OpenPnP.
#

import os
import sys
import pcbnew
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET
import json

# Internal lookup table for mapping KiCad footprint names to OpenPnP Packages.
#
# NOTE: This is updated by loading parts.json at startup.
footprint_to_package_mapping = {}

# Internal lookup table containing part heights based on the packages.
#
# NOTE: This is updated by loading parts.json at startup.
part_height_mapping = {}

# Internal lookup table containg package sizes.
#
# NOTE: This is updated by loading parts.json at startup.
package_size_mapping = {}

def create_board_xml(placements, board_origin_x, board_origin_y, x_size, y_size, pcb_board_file, board_xml_file):
    print('Creating {} with {} parts to be placed'.format(board_xml_file, len(placements)))

    # <openpnp-board version="1.1" name="{board name}">
    openpnp_board = ET.Element('openpnp-board', {
        'version' : "1.1",
        'name' : os.path.normpath(pcb_board_file).split(os.sep)[-1]
    })

    #<dimensions units="Millimeters" x="100.0" y="80.0" z="0.0" rotation="0.0"/>
    ET.SubElement(openpnp_board, 'dimensions', {
        'units': 'Millimeters',
        'x' : str(round(x_size, 10)),
        'y' : str(round(y_size, 10)),
        'z' : '0.0',
        'rotation' : '0.0'
    })
    # top level node for all parts to be placed
    openpnp_placements = ET.SubElement(openpnp_board, 'placements')
    # not used
    ET.SubElement(openpnp_board, 'solder-paste-pads')

    for placement in placements:
        node = ET.SubElement(openpnp_placements, 'placement', {
            'version' : '1.4',
            'id' : placement['id'],
            'side' : placement['side'],
            'part-id' : placement['part-id'],
            'type' : placement['type'],
            'enabled' : 'true'
        })
        placement_x = placement['x'] - board_origin_x
        placement_y = placement['y'] - board_origin_y
        ET.SubElement(node, 'location', {
            'units' : 'Millimeters',
            'x' : str(abs(round(placement_x, 10))),
            'y' : str(abs(round(placement_y, 10))),
            'z' : '0.0',
            'rotation' : str(placement['rotation'])
        })
    if sys.version_info >= (3, 9):
        ET.indent(openpnp_board)
    ET.ElementTree(openpnp_board).write(board_xml_file)

def update_parts_xml(parts, parts_xml_file, is_read_only):
    parts_xml = ET.parse(parts_xml_file)
    parts_root = parts_xml.getroot()
    # Process all unique packages and cross check against packages.xml
    new_parts_added = False
    for part in parts:
        # <part id="FIDUCIAL-HOME" name="Homing Fiducial - Do Not Delete" height-units="Millimeters" height="0.0" package-id="FIDUCIAL-1X2" speed="1.0" pick-retry-count="0"/>
        if len(parts_xml.findall(".//part[@id='{}']".format(part))) == 0:
            print('Part {} not found, creating'.format(part))
            new_parts_added = True
            ET.SubElement(parts_root, 'part', {
                'id' : part,
                'name' : part,
                'height-units' : 'Millimeters',
                'height' : part_height_mapping[parts[part]] if parts[part] in part_height_mapping else '0.0',
                'package-id' : parts[part],
                'speed' : '1.0',
                'pick-retry-count' : '0'
            })
    if is_read_only:
        print('Read-only mode is enabled, skipping updates to parts.xml')
    elif new_parts_added:
        if sys.version_info >= (3, 9):
            ET.indent(parts_root)
        parts_xml.write(parts_xml_file)
    else:
        print('All required parts have been found, no update to parts.xml required')

def update_packages_xml(packages, packages_xml_file, usable_nozzles, is_read_only):
    packages_xml = ET.parse(packages_xml_file)
    packages_root = packages_xml.getroot()

    # Process all unique packages and cross check against packages.xml
    new_packages_added = False
    for package in packages:
        if len(packages_xml.findall(".//package[@id='{}']".format(package))) == 0:
            new_packages_added = True
            print('Package {} not found, creating'.format(package))
            # top level element:
            # <package version="1.1" id="FIDUCIAL_0.5x1mm" description="Fiducial 0.5mm 1mm mask" pick-vacuum-level="0.0" place-blow-off-level="0.0">
            package_elem = ET.SubElement(packages_root, 'package', {
                'version':'1.1',
                'id':package,
                'description':'',
                'pick-vacuum-level':'0.0',
                'place-blow-off-level':'0.0'
            })
            # nested element:
            # <footprint units="Millimeters" body-width="1.0" body-height="1.0">
            footprint_elem = ET.SubElement(package_elem, 'footprint', {
                'units':'Millimeters',
                'body-width': package_size_mapping[package]['w'] if package in package_size_mapping else '0.0',
                'body-height': package_size_mapping[package]['h'] if package in package_size_mapping else '0.0'
            })
            # nested element:
            # <compatible-nozzle-tip-ids class="java.util.ArrayList"></compatible-nozzle-tip-ids>
            nozzles = ET.SubElement(package_elem, 'compatible-nozzle-tip-ids', {'class' : 'java.util.ArrayList'})
            if usable_nozzles:
                for nozzle in usable_nozzles:
                    ET.SubElement(nozzles, 'string').text = nozzle
            for pad in packages[package]:
                values = packages[package][pad]
                # <pad name="1" x="0.0" y="0.0" width="0.5" height="0.5" rotation="0.0" roundness="100.0"/>
                if values['shape'] == 'CIRCLE':
                    if 'FIDUCIAL' in pad.upper():
                        ET.SubElement(footprint_elem, 'pad', {
                            'name':pad,
                            'x':'0.0',
                            'y':'0.0',
                            'width':str(values['w']),
                            'height':str(values['h']),
                            'rotation':'0.0',
                            'roundness':'100.0',
                        })
                    else:
                        ET.SubElement(footprint_elem, 'pad', {
                            'name':pad,
                            #'radius':str(values['radius']),
                            'x':str(values['x']),
                            'y':str(values['y']),
                            'width':str(values['w']),
                            'height':str(values['h']),
                            'rotation':'0.0',
                            'roundness':'100.0'
                        })
                elif values['shape'] == 'ROUNDRECT':
                    ET.SubElement(footprint_elem, 'pad', {
                        'name':pad,
                        'x':str(values['x']),
                        'y':str(values['y']),
                        'width':str(values['w']),
                        'height':str(values['h']),
                        'rotation':'0.0',
                        #'roundness':'0.0'
                    })
                else:
                    ET.SubElement(footprint_elem, 'pad', {
                        'name':pad,
                        'x':str(values['x']),
                        'y':str(values['y']),
                        'width':str(values['w']),
                        'height':str(values['h']),
                        'rotation':'0.0',
                        #'roundness':'0.0'
                    })
        #else:
        #    print('Package {} already exists'.format(package))

    if is_read_only:
        print('Read-only mode is enabled, skipping updates to packages.xml')
    elif new_packages_added:
        if sys.version_info >= (3, 9):
            ET.indent(packages_root)
        packages_xml.write(packages_xml_file)
    else:
        print('All required packages have been found, no update to packages.xml required')

def identity_used_packages_and_parts(board, ignore_top, ignore_bottom, use_value_for_part_id, use_mixedcase):
    print('Board contains {} footprints'.format(len(board.GetFootprints())))
    packages = {}
    parts = {}
    placements = []
        
    # Process all footprints that are found on the board
    for footprint in board.GetFootprints():
        # if the footprint is an SMD footprint we should process it further.
        includeFootprint = False
        for pad in footprint.Pads():
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                includeFootprint = True
        if includeFootprint:
            if 'SMD' not in footprint.GetTypeName():
                print('WARNING: KiCad lists \'{}\' as not SMD but includes SMD pads!'.format(footprint.GetReference()))
            if ignore_top and footprint.GetLayer() == pcbnew.F_Cu:
                continue
            elif ignore_bottom and footprint.GetLayer() == pcbnew.B_Cu:
                continue
            fp_name = str(footprint.GetFPID().GetLibItemName())

            # check if we have a mapping for the footprint name
            if fp_name.upper() in footprint_to_package_mapping:
                fp_name = footprint_to_package_mapping[fp_name.upper()]

            #print('Footprint: {}'.format(fp_name))
            fp_value = str(footprint.GetValue())
            fp_ref = str(footprint.GetReference())

            fp_x_mm = pcbnew.Iu2Millimeter(footprint.GetPosition().x)
            fp_y_mm = pcbnew.Iu2Millimeter(footprint.GetPosition().y)
            # <placement version="1.4" id="U12" side="Top" part-id="74AHC1G08" type="Placement" enabled="true">
            #   <location units="Millimeters" x="193.98" y="-125.91" z="0.0" rotation="0.0"/>
            #   <error-handling>Alert</error-handling>
            # </placement>
            placement_type = 'Placement' if 'Fiducial' not in fp_value else 'Fiducial'
            placement_name = '{}_{}'.format(fp_name, fp_value) if 'Fiducial' not in fp_value else fp_name

            if use_value_for_part_id:
                placement_name = fp_value

            if not use_mixedcase:
                placement_name = placement_name.upper()
                fp_name = fp_name.upper()
            
            parts[placement_name] = fp_name

            placements.append({'id' : footprint.GetReference(),
                'side' : 'Top' if footprint.GetLayer() == pcbnew.F_Cu else 'Bottom',
                'part-id' : placement_name,
                'type' : placement_type,
                'x' : pcbnew.Iu2Millimeter(footprint.GetPosition().x),
                'y' : pcbnew.Iu2Millimeter(footprint.GetPosition().y),
                'rotation' : footprint.GetOrientationDegrees()
            })
            packages[fp_name] = {}
            for pad in footprint.Pads():
                # Calculate the X/Y offset from the footprint in the PCB, this needs to be adjusted
                # for the footprint position.
                fp_offs_x_mm = pcbnew.Iu2Millimeter(pad.GetPosition().x - footprint.GetPosition().x)
                fp_offs_y_mm = pcbnew.Iu2Millimeter(pad.GetPosition().y - footprint.GetPosition().y)

                # Calculate the footprint pad size
                fp_size_w_mm = pcbnew.Iu2Millimeter(pad.GetSizeX())
                fp_size_h_mm = pcbnew.Iu2Millimeter(pad.GetSizeY())

                # Determine the pad shape, the value from this method is PAD_SHAPE::{value}
                # where {value} is: CIRCLE, RECT, OVAL, TRAPEZOID, ROUNDRECT, CHAMFERED_RECT, CUSTOM
                pad_shape = pcbnew.PAD_SHAPE_T_asString(pad.GetShape()).split('::')[1]

                pad_name = str(pad.GetName())
                if 'FIDUCIAL' in fp_name.upper() and pad_name == '':
                    pad_name = '1'

                if pad.IsOnCopperLayer():
                    if pad_shape == 'ROUNDRECT':
                        radius = pcbnew.Iu2Millimeter(pad.GetRoundRectCornerRadius());
                        packages[fp_name][pad_name] = {
                            'w':fp_size_w_mm,
                            'h':fp_size_h_mm,
                            'x':fp_offs_x_mm,
                            'y':fp_offs_y_mm,
                            'shape':pad_shape,
                            'radius':radius
                        }
    #    Need to figure out how to translate this to OpenPnP
    #               elif pad_shape == 'CHAMFERED_RECT':
    #                   radius = pcbnew.Iu2Millimeter(pad.GetChamferRectRatio());
    #                   packages[fp_name][pad_name] = {
    #                       'w':fp_size_w_mm,
    #                       'h':fp_size_h_mm,
    #                       'x':fp_offs_x_mm,
    #                       'y':fp_offs_y_mm,
    #                       'shape':pad_shape,
    #                       'radius':radius
    #                   }
                    elif pad_shape == 'CIRCLE':
                        radius = pcbnew.Iu2Millimeter(pad.GetBoundingRadius());
                        packages[fp_name][pad_name] = {
                            'w':fp_size_w_mm,
                            'h':fp_size_h_mm,
                            'x':fp_offs_x_mm,
                            'y':fp_offs_y_mm,
                            'shape':pad_shape,
                            'radius':radius
                        }
                    else:
                        # Generic pad
                        packages[fp_name][pad_name] = {
                            'w':fp_size_w_mm,
                            'h':fp_size_h_mm,
                            'x':fp_offs_x_mm,
                            'y':fp_offs_y_mm,
                            'shape':pad_shape
                        }
    print('Found {} unique SMD packages used by {} unique parts'.format(len(packages), len(parts)))
    return packages, parts, placements

def get_script_directory():
    script = os.path.realpath(__file__)
    dirname = os.path.dirname(script)
    return dirname

parser = argparse.ArgumentParser()
parser.add_argument('--board', type=str, help='KiCad PCB to parse, foo.kicad_pcb', required=True)
parser.add_argument('--board_xml', type=str, help='OpenPnP board.xml to generate', required=True)
parser.add_argument('--packages', type=str, help='Location of packages.xml', default='{}/.openpnp2/packages.xml'.format(Path.home()))
parser.add_argument('--parts', type=str, help='Location of parts.xml', default='{}/.openpnp2/parts.xml'.format(Path.home()))
parser.add_argument('--use_mixedcase', help='Enabling this option will generate package names and part names using the values as-is from the PCB. When not enabled all names will be forced to upper case.', default=False, action='store_true')
parser.add_argument('--use_value_for_part_id', help='Enabling this option will use component Value from the KiCad PCB footprint as the OpenPnP part ID', default=False, action='store_true')
parser.add_argument('--nozzle', type=str, help='Default nozzle(s) to assign as compatible, can be specified more than once', action='append')
parser.add_argument('--ignore_top', help='Exclude pads on the F_Cu (top) layer', default=False, action='store_true')
parser.add_argument('--ignore_bottom', help='Exclude pads on the B_Cu (bottom) layer', default=False, action='store_true')
parser.add_argument('--read_only', help='Enable this option to disable updating any OpenPnP files, board.xml will still be generated.', default=False, action='store_true')
parser.add_argument('--parts_json', type=str, help='Location of parts.json', default='{}/parts.json'.format(get_script_directory()))
args = parser.parse_args()

# Check for and load parts.json into the lookup tables used by the package and
# parts verification code.
if os.path.exists(args.parts_json):
    with open(args.parts_json, 'r') as f:
        parts = json.load(f)
        for part in parts:
            if 'alias' in part:
                if isinstance(part['alias'], str):
                    footprint_to_package_mapping[part['alias'].upper()] = part['id']
                else:
                    for alias in part['alias']:
                        footprint_to_package_mapping[alias.upper()] = part['id']
            if 'z_mm' in part and part['z_mm']:
                part_height_mapping[part['id']] = str(part['z_mm'])
            if 'x_mm' in part and part['x_mm'] and 'y_mm' in part and part['y_mm']:
                package_size_mapping[part['id']] = {
                    'h' : str(part['x_mm']),
                    'w' : str(part['y_mm']),
                }

if not os.path.exists(args.board):
    raise '{} does not appear to be a valid file'.format(args.board)

print('Loading {}'.format(args.board))

board = pcbnew.LoadBoard(args.board)
board_edges = board.GetBoardEdgesBoundingBox()

# KiCad 6 moved the GetAuxOrigin method from the board to board design.
if pcbnew.GetBuildVersion().startswith('5'):
    board_origin = board.GetAuxOrigin()
else:
    board_origin = board.GetDesignSettings().GetAuxOrigin()

if board_origin.x == 0 and board_origin.y == 0:
    print('WARNING: board origin is not defined!')
    print('Without a board origin, part positions are very likely going to be inaccurate!')

board_width = pcbnew.Iu2Millimeter(board_edges.GetWidth())
board_height = pcbnew.Iu2Millimeter(board_edges.GetHeight())
board_origin_x = pcbnew.Iu2Millimeter(board_origin.x)
board_origin_y = pcbnew.Iu2Millimeter(board_origin.y)
print('Detected board is {}x{}mm (origin:{},{})'.format(board_width, board_height, board_origin_x, board_origin_y))

if args.use_mixedcase:
    print('Packages and parts may use mixed-case names')
else:
    print('Packages and parts will be forced to upper case')

packages, parts, placements = identity_used_packages_and_parts(board, args.ignore_top, args.ignore_bottom, args.use_value_for_part_id, args.use_mixedcase)
update_packages_xml(packages, args.packages, args.nozzle, args.read_only)
update_parts_xml(parts, args.parts, args.read_only)
create_board_xml(placements, board_origin_x, board_origin_y, board_width, board_height, args.board, args.board_xml)

