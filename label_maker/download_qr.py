#
# SPDX-FileCopyrightText: 2022 CurlyTaleGamesLLC
#
# SPDX-License-Identifier: MIT
#

import requests
import os

def get_current_directory():
    script = os.path.realpath(__file__)
    dirname = os.path.dirname(script)
    return dirname

# Downloads a QR code image using the Google Charts API
def download(data, size):
    url = 'https://chart.googleapis.com/chart?cht=qr&chs=' + str(size) + 'x' + str(size) + '&chl=' + data
    
    currentDirectory = get_current_directory()
    labelsDirectory = os.path.join(currentDirectory, "labels")
    if not os.path.exists(labelsDirectory):
        os.makedirs(labelsDirectory)
    labelPath = os.path.join(labelsDirectory, data + ".png")
    
    img_data = requests.get(url).content
    with open(labelPath, 'wb') as handler:
        handler.write(img_data)

# DownloadQRCode("data")