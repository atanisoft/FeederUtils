# Templates

This directory contains templates used by the label making utility.

## Label configuration files

With multiple supportable labels on the market it is necessary to define the basic
layout of the label sheet for proper label generation. The json files in this directory
have the following structure:

```
{
    "pageWidth":2550,
    "pageHeight":3300,
    "marginX":143,
    "marginY":133,
    "rows":4,
    "columns":4,
    "labelSize":153,
    "labelBorder":0,
    "spacingX":200,
    "spacingY":100,
    "groupSize":2,
    "groupSpacing":0
}
```

- **pageWidth** = horizontal resolution of page
- **pageHeight** = vertical resolution of page
- **marginX** = distance from left side of page
- **marginY** = distance from top of the page
- **rows** = number of rows of labels on the page
- **columns** = number of columns of labels on the page
- **labelSize** = the height and width of each label
- **labelBorder** = currently unused
- **spacingX** = the horizontal distance between labels
- **spacingY** = the vertical distance between labels
- **groupSize** = for non square labels this allows you to print more than 1 QR code per label
- **groupSpacing** = defines the horizontal space between each group of QR codes

TBD - are widths/offsets/spacing in mm or pixels? - Currently Pixels


## Available Label Configurations

| Label Name      | Template Name |
| ----------- | ----------- |
| [Neon Labels 1056](https://www.amazon.com/dp/B08M8SPFLC) | neon_labels_0.5inch.json       |
| [Avery 8195]()   | avery_8195.json        |
