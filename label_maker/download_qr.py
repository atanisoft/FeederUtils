#
# SPDX-FileCopyrightText: 2022 CurlyTaleGamesLLC
#
# SPDX-License-Identifier: MIT
#

import requests
import os
from PIL import Image

def get_current_directory():
    script = os.path.realpath(__file__)
    dirname = os.path.dirname(script)
    return dirname

# Downloads a QR code image using the Google Charts API
def download(data, size, borderWidth):
    url = 'https://chart.googleapis.com/chart?cht=qr&chs=' + str(size) + 'x' + str(size) + '&chl=' + data
    
    currentDirectory = get_current_directory()
    labelsDirectory = os.path.join(currentDirectory, "labels")
    if not os.path.exists(labelsDirectory):
        os.makedirs(labelsDirectory)
    labelPath = os.path.join(labelsDirectory, data + ".png")
    
    img_data = requests.get(url).content
    with open(labelPath, 'wb') as handler:
        handler.write(img_data)
    add_border(labelPath)

def add_border(imagePath):
    im = Image.open(imagePath)

    crosshairLength = 5

    # add border to top and bottom
    for pixel in range(im.width):
        im.putpixel((pixel, 0),(127, 127, 127))
        im.putpixel((pixel, im.height - 1),(127, 127, 127))
    
    # add border to left and right
    for pixel in range(im.height):
        im.putpixel((0, pixel),(127, 127, 127))
        im.putpixel((im.width - 1, pixel),(127, 127, 127))
    
    # add left and right crosshairs
    yMiddle = int(im.height / 2)
    for pixel in range(crosshairLength):
        im.putpixel((pixel, yMiddle),(127, 127, 127))
        im.putpixel((im.width - 1 - pixel, yMiddle),(127, 127, 127))
    
    # add top and bottom crosshairs
    xMiddle = int(im.width / 2)
    for pixel in range(crosshairLength):
        im.putpixel((xMiddle, pixel),(127, 127, 127))
        im.putpixel((xMiddle, im.height - 1 - pixel),(127, 127, 127))
    
    # overwite the original image
    im.save(imagePath)



# this code is orphaned, it might be useful later though
def crop_qr_code_add_border(imagePath, borderWidth):
    im = Image.open(imagePath)
    px = im.load()

    left = 0
    right = 999
    top = 0
    bottom = 999

    scanY = int(im.height * 0.2)
    scanX = int(im.width * 0.2)

    # find first black pixel on the left side of the QR code
    for pixel in range(im.width):
        if px[pixel, scanY] != (255, 255, 255):
            left = pixel
            break
    
    # find first black pixel on the right side of the QR code
    for pixel in range(im.width):
        if px[im.width - pixel, scanY] != (255, 255, 255):
            right = pixel
            break
    
    # find first black pixel on the top side of the QR code
    for pixel in range(im.width):
        if px[scanX, pixel] != (255, 255, 255):
            top = pixel
            break
    
    # find first black pixel on the bottom side of the QR code
    for pixel in range(im.width):
        if px[scanX, pixel] != (255, 255, 255):
            bottom = pixel
            break
    
    # crop the white out of the QR code
    imageCropped = im.crop((left, top, right, bottom))
    imageCroppedWidth, imageCroppedHeight = imageCropped.size

    # create a new white image with the new border size
    newImageWidth = (right - left) + (borderWidth * 2)
    newImageHeight = (right - left) + (borderWidth * 2)
    img = Image.new('RGB', (newImageWidth, newImageHeight), color = 'white')

    # add the cropped QR code to the center
    offset = ((newImageWidth - imageCroppedWidth) // 2, (newImageHeight - imageCroppedHeight) // 2)
    img.paste(imageCropped, offset)

    # overwrite the original image
    img.save(imagePath)


# DownloadQRCode("data")