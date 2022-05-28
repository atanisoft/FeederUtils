
import sys
import os
import math 
from PIL import Image

import download_qr
import config

partList = [
    "FIDUCIAL-HOME",
    "Fiducial_1mm_Mask2mm-Fiducial",
    "SOT-23-2N7002K",
    "R_0805_2012Metric-10K",
    "C_0805_2012Metric_Pad1.15x1.40mm_HandSolder-0.1uf",
    "C_0805_2012Metric_Pad1.15x1.40mm_HandSolder-10uf",
    "LED_0805_2012Metric_Pad1.15x1.40mm_HandSolder-LED",
    "Fiducial_0.75mm_Mask1.5mm-Fiducial",
    "SOT-23-2N7002",
    "R_0805_2012Metric-2.2k",
    "R_0805_2012Metric-22"]

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
    
    # offset distance from top left corner
    offsetX = config.data['offsetX']
    offsetY = config.data['offsetY']

    # distance between top left corner of each label
    spacingY = config.data['spacingY']
    spacingX = config.data['spacingX']

    
    currentDirectory = get_current_directory()
    labelsDirectory = os.path.join(currentDirectory, "labels")

    exportFile =  os.path.join(currentDirectory, "print_labels_" + str(pageNumber) + ".png")
    img = Image.new('RGB', (pageWidth, pageHeight), color = 'white')

    labelMapPath =  os.path.join(currentDirectory, "label_map.txt")
    labelMap = open(labelMapPath, "a")
    labelMap.write("PAGE = " + str(pageNumber + 1) + "\n")
    labelMap.write("X , Y = PART ID\n")

    labelIndex = 0
    rowIndex = 0
    columnIndex = 0
    
    for label in labelList:
        if label != ' ':
            # Place QR code on sheet of paper
            imageSpacingX = offsetX + (rowIndex * labelSize) + (rowIndex * spacingX)
            imageSpacingY = offsetY + (columnIndex * labelSize) + (columnIndex * spacingY)
            new_image = Image.open(label)
            img.paste(new_image, (imageSpacingX, imageSpacingY))

            # Write QR code label to label map file
            filename = os.path.basename(label)
            partID = filename[:len(filename) - 4]
            # labelMap.write(str(rowIndex + 1) + "," + str(columnIndex + 1) + " = " + partID +"\n")
            labelMap.write(f'{(rowIndex + 1):02}' + "," + f'{(columnIndex + 1):02}' + " = " + partID +"\n")

        # Increment label position indexes to next position
        labelIndex += 1
        rowIndex += 1
        if rowIndex > columns - 1:
            rowIndex = 0
            columnIndex += 1

    img.save(exportFile)
    labelMap.write("\n")
    labelMap.close()


def generate(startIndex = 0, templateFile = "default.json"):

    config.load(templateFile)

    for part in partList:
        if not "FIDUCIAL" in part.upper():
            download_qr.download(part, config.data['labelSize'])

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

    # create PNG files for each page of labels
    for page in range(totalPages):
        create_page(page, labelsList[0:labelsPerSheet])
        del labelsList[0:labelsPerSheet]

    # delete old label images
    delete_labels()

def main():
    print("Generating QR Code Part ID Sheet")
    # print(sys.argv)

    startIndex = sys.argv[1] if len(sys.argv) > 1 else 0
    templateFile = sys.argv[2] if len(sys.argv) > 2 else "default.json"

    generate(startIndex, templateFile)

if __name__ == "__main__":
    main()