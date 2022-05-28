import os
import json

data = []

# Loads json file with the parameters for different brands printable of sticky labels
def load(fileName = 'default.json'):
    global data
    configPath = os.path.join("templates", fileName)
    # Opening JSON file
    with open(configPath) as json_file:
        data = json.load(json_file)
