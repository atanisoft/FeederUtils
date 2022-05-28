# Feeder Reader

This project simplifies the import and feeder set up process between KiCad and Open PNP. It uses the top down camera on your Pick and Place machine to read small QR codes on each feeder. The feeders are then automatically mapped in Open PNP saving you hours of configuration.

![Open PNP Top down camera view of QR code](/docs/feeder-setup.png)

**WARNING:** THIS PROJECT IS STILL UNDER DEVELOPMENT

## KiCad Import

Feeder Reader imports your KiCad PCBnew file and exports out the board.xml, parts.xml, and job.xml files.

To use it run the following commands:

    python3 ./kicad-to-openpnp-standalone.py --board foo.kicad_pcb --board_xml foo.board.xml

Additional command line arguments are supported and can be viewed by running without arguments.

## Generate Sheets of Labels

In order to have the top down cameras recognize the feeders they need to scan a small QR code to know the position and contents of each feeder. Feeder Reader allows you to generate these QR codes and print them on sheets of labels. You can create or adjust a template .json file to match the sheets of labels you want to use. You can also offset where the label starts to print allowing you to print on a partially used sheet of labels. A label map file is also generated so you know the value of each QR code and it's X and Y position on sheet of labels.

![Sheet of QR codes](/docs/qr-page.png)

![Label map file listing contents of each sheet of labels](/docs/map-file.png)

To generate the labels you can use the following commands:

    python3 ./generate_labels.py
    
To offset the starting index of the QR codes on the sheet of paper by 2:

    python3 ./generate_labels.py 2
    
To use a different page template json file add the filename to the end of the command

    python3 ./generate_labels.py 2 neon_labels_0.5inch.json

## OpenPnP Scripts

The [openpnp](openpnp) directory contains scripts which should be added to your OpenPnP scripts directory. These scripts work in conjuction with the QR Codes and KiCad board import to automate the creation of feeders and automatic assignment of parts to the feeders.
