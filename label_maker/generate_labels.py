#
# SPDX-FileCopyrightText: 2022 CurlyTaleGamesLLC
#
# SPDX-License-Identifier: MIT
#

import argparse
import sys
import os
import math
from pathlib import Path
from PIL import Image
import xml.etree.ElementTree as ET

import download_qr
import config

def get_current_directory():
    script = os.path.realpath(__file__)
    dirname = os.path.dirname(script)
    return dirname

def delete_pages():
    # Delete old label sheets and label map file
    currentDirectory = get_current_directory()
    mapFile = os.path.join(currentDirectory, "label_map.txt")
    if os.path.exists(mapFile):
        os.remove(mapFile)
    
    for page in os.listdir(currentDirectory):
        if os.path.isfile(page):
            if page.endswith('.png'):
                if page.startswith('print_labels'):
                    os.remove(page)

def delete_labels():
    labelsDirectory = os.path.join(get_current_directory(), "labels")
    # Delete the label image files after label sheet is created
    for label in os.listdir(labelsDirectory):
        f = os.path.join(labelsDirectory, label)
        if os.path.isfile(f):
            if f.endswith('.png'):
                os.remove(f)

def create_page(pageNumber, labelList, startIndex = 0):

    # resolution of the page
    pageWidth = config.data['pageWidth']
    pageHeight = config.data['pageHeight']

    # number of rows and column of labels per page
    rows = config.data['rows']
    columns = config.data['columns']

    # size of QR code
    labelSize = config.data['labelSize']
    
    # margin distance from top left corner
    marginX = config.data['marginX']
    marginY = config.data['marginY']

    # distance between top left corner of each label
    spacingY = config.data['spacingY']
    spacingX = config.data['spacingX']

    # optional parameter to group qr codes so multiple can be printed on a single label
    groupSize = config.data['groupSize']
    groupSpacing = config.data['groupSpacing']
    
    currentDirectory = get_current_directory()
    labelsDirectory = os.path.join(currentDirectory, "labels")

    if not os.path.exists(labelsDirectory):
        os.makedirs(labelsDirectory)

    exportFile =  os.path.join(currentDirectory, "print_labels_" + str(pageNumber + 1) + ".png")
    img = Image.new('RGB', (pageWidth, pageHeight), color = 'white')

    labelMapPath =  os.path.join(currentDirectory, "label_map.txt")
    labelMap = open(labelMapPath, "a")
    labelMap.write("PAGE = " + str(pageNumber + 1) + "\n")
    labelMap.write("X , Y = PART ID\n\n")

    labelIndex = 0
    rowIndex = 0
    columnIndex = 0
    groupIndex = 0
    
    for label in labelList:
        if label != ' ':
            groupIndex = rowIndex % groupSize
            groupNumber = math.floor(rowIndex / groupSize)
           
            # Place QR code on sheet of paper
            imageSpacingX = marginX + (rowIndex * labelSize) + (groupNumber * spacingX) + (groupIndex * groupSpacing)
            imageSpacingY = marginY + (columnIndex * labelSize) + (columnIndex * spacingY)
            new_image = Image.open(label)
            img.paste(new_image, (imageSpacingX, imageSpacingY))

            # Write QR code label to label map file
            filename = os.path.basename(label)
            partID = filename[:len(filename) - 4]
            labelMap.write(f'{(rowIndex + 1):02}' + "," + f'{(columnIndex + 1):02}' + " = " + partID +"\n")

        # Increment label position indexes to next position
        labelIndex += 1
        rowIndex += 1
        
        if rowIndex > columns - 1:
            rowIndex = 0
            columnIndex += 1
            labelMap.write("\n")

    img.save(exportFile)
    labelMap.write("\n")
    labelMap.close()


def generate(startIndex = 0, templateFile = "default.json", partList = []):

    config.load(templateFile)

    print('Generating QR Codes...')
    for part in partList:
        if not "FIDUCIAL" in part.upper():
            download_qr.download(part, config.data['labelSize'], config.data['labelBorder'])

    # delete old label pages
    delete_pages()
    
    # Create new label map file
    currentDirectory = get_current_directory()
    mapFile = os.path.join(currentDirectory, "label_map.txt")
    with open(mapFile, 'w') as f:
        f.write('')
    
    # create label pages
    labelsList = []
    labelsDirectory = os.path.join(currentDirectory, "labels")
    for label in os.listdir(labelsDirectory):
        f = os.path.join(labelsDirectory, label)
        # checking if it is a file
        if os.path.isfile(f):
            if f.endswith('.png'):
                labelsList.append(f)
    
    # add empty labels to offset the starting position of QR codes
    offsetLabels = [' '] * int(startIndex)
    labelsList = offsetLabels + labelsList

    labelsPerSheet = config.data["rows"] * config.data['columns']
    totalPages = math.ceil((len(labelsList)) / labelsPerSheet)

    print('Merging QR Codes into printable pages...')
    # create PNG files for each page of labels
    for page in range(totalPages):
        create_page(page, labelsList[0:labelsPerSheet])
        del labelsList[0:labelsPerSheet]

    # delete old label images
    delete_labels()

def parse_board_xml(xml_file):
    # read the XML file
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # get all the placement part-ids  
    xml_parts = []
    for part in root.iter('placement'):
        part_id = part.get('part-id')
        xml_parts.append(part_id)

    # filter out duplicate parts
    unique_parts = list(dict.fromkeys(xml_parts))

    return unique_parts

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', type=str, help='Label configuration file', default='default.json')
parser.add_argument('-i', '--index', type=int, help='Starting index on the label sheet', default=0)
parser.add_argument('-p', '--parts', type=str, help='board.xml file from KiCad Tools script, or text file with each part on a new line', default='')
parser.add_argument('-f', '--fetch', default=False, help='Text file with each part on a new line', action='store_true')
parser.add_argument('--parts_xml', type=str, help='Location of parts.xml', default='{}/.openpnp2/parts.xml'.format(Path.home()))
args = parser.parse_args()

if args.fetch:
    print('Reading parts list from OpenPnP: {}'.format(args.parts_xml))
    parts_xml = ET.parse(args.parts_xml)
    parts_root = parts_xml.getroot()
    partList = []
    for part in parts_root:
        part_id = part.attrib['id']
        if '/' in part_id or '\\' in part_id:
            new_part_id = part_id.replace('/','_').replace('\\','_')
            print('Warning: Part {} contains characters that will be problematic, new name: {}'.format(part_id, new_part_id))
            part_id = new_part_id
        partList.append(part_id)
else:
    print('Reading parts list from: {}'.format(args.parts))
    if args.parts.endswith('.xml'):
        print("Parsing XML file")
        partList = parse_board_xml(args.parts)
    else:
        print("Parsing TXT file")
        with open(args.parts, 'r') as file:
            partList = file.read().splitlines()

print('Generating labels for parts')

generate(args.index, args.config, partList)

print('QR Codes generated!')