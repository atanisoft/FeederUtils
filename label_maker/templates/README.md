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
    "rows":4,
    "columns":4,
    "labelSize":153,
    "offsetX":143,
    "offsetY":133,
    "spacingX":200,
    "spacingY":100
}
```

TBD - are widths/offsets/spacing in mm or pixel?

## Available Label Configurations

### default.json

This contains the default configuration settings for generating a page of QR codes.

### neon_labels_0.5inch.json

This contains the configuration settings for [Neon Labels 1056](https://www.amazon.com/dp/B08M8SPFLC) 1/2 inch labels.

### avery_8195.json

This contains the configuration settings for [Avery 8195]() 2/3 x 1 3/4 inch labels.
