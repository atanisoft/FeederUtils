# Feeder Reader

This project simplifies the import and feeder set up process between [KiCad](www.kicad.org) and [OpenPnP](www.openpnp.org). It uses the top down camera on your Pick and Place machine to read small QR codes on each feeder. The feeders are then automatically mapped in [OpenPnP](www.openpnp.org) saving you hours of configuration.

![Open PNP Top down camera view of QR code](docs/feeder-setup.png)

> **WARNING**
> THIS PROJECT IS STILL UNDER ACTIVE DEVELOPMENT.
> USE AT OWN RISK!

## Repository layout

This repository is organized by the function of the utilities.
* [openpnp](openpnp) contains scripts which integrate and run from within [OpenPnP](www.openpnp.org).
* [kicad_tools](kicad_tools) contains standalone scripts which automate importing of [KiCad](www.kicad.org) PCBs into [OpenPnP](www.openpnp.org)
* [label_maker](label_maker) contains scripts related to generating QR code labels to attach onto feeders which can be used for part identification.ts.
