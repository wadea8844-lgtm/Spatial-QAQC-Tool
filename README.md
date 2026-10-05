# Spatial Data QA/QC Automation Tool

A custom **PyQGIS Processing Tool** developed to automate spatial data quality-control workflows in QGIS.

The tool reduces repetitive manual QA/QC work by automatically detecting coordinate-related issues, validating records against a user-defined project extent, identifying potential duplicate locations, correcting confirmed X/Y swaps, and generating structured QA/QC outputs.

---

## Features

The tool checks for:

- Missing coordinates
- Invalid coordinate values
- Exact and near-duplicate locations
- Coordinates outside a valid project extent
- X/Y coordinate swaps

It also allows the user to define:

- X field
- Y field
- Coordinate CRS
- Duplicate tolerance in meters
- Valid X/Y extent
- Fields to include in Excel and PDF reports

---

## X/Y Swap Detection

The tool automatically corrects X/Y values only when:

1. The original coordinate pair is outside the valid extent
2. The swapped coordinate pair falls inside the valid extent

Example:

```text
Original:
X = 24.425216
Y = 54.394130

Corrected:
X = 54.394130
Y = 24.425216
```

Corrected records are classified as:

`FIXED`

---

## Duplicate Detection

The tool supports both exact and near-duplicate detection.

The user defines a tolerance in meters, for example:

```text
Duplicate tolerance = 1.0 meter
```

Records within the selected distance are flagged as:

`WARNING`

The output also includes:

- Matching record ID
- Duplicate distance in meters

---

## QA/QC Output Fields

The validated output contains additional QA/QC fields:

| Field | Description |
|---|---|
| `QA_STATUS` | PASS, ERROR, WARNING, or FIXED |
| `QA_ISSUE` | Detected issue |
| `QA_ACTION` | Recommended action |
| `DUPLICATE_WITH` | Matching duplicate record |
| `DUP_DISTANCE_M` | Duplicate distance in meters |
| `ORIGINAL_X` | Original X value |
| `ORIGINAL_Y` | Original Y value |
| `CORRECTED_X` | Corrected/validated X value |
| `CORRECTED_Y` | Corrected/validated Y value |

---

## Outputs

The tool produces three main outputs:

### 1. Validated Dataset

A full QA/QC output containing all original records plus QA/QC fields.

### 2. Issues Excel

An Excel file containing only records with:

```text
QA_STATUS != PASS
```

### 3. Styled PDF Report

The PDF report includes:

- Total records
- Passed records
- Errors
- Warnings
- Auto-fixed records
- Issue summary
- Detailed issue table
- Original and corrected coordinates
- Duplicate distances

The report is exported in landscape format for better readability.

---

## Example Result

Example result from the training dataset:

```text
Total Records: 144
Passed: 120
Errors: 10
Warnings: 6
Auto Fixed: 8
```

Detected issues:

```text
Missing Coordinates: 6
Potential Duplicates: 6
X/Y Swapped: 8
Outside Valid Extent: 4
Invalid Coordinate Values: 0
```

---

## Technologies Used

- QGIS
- Python
- PyQGIS
- QGIS Processing Framework
- QgsDistanceArea
- Excel export through QGIS Processing
- HTML/CSS for PDF report generation

---

## Installation

Copy:

```text
spatial_qaqc_validator.py
```

to the QGIS Processing scripts folder.

Typical Windows path:

```text
C:\Users\<USERNAME>\AppData\Roaming\QGIS\QGIS3\profiles\default\processing\scripts
```

The tool will appear under:

```text
Processing Toolbox
└── Scripts
    └── QA/QC Tools
        └── Spatial QA/QC Validator
```

---

## How to Use

1. Open QGIS
2. Open Processing Toolbox
3. Run `Spatial QA/QC Validator`
4. Select the input table/layer
5. Select X and Y fields
6. Select optional report fields
7. Select Coordinate CRS
8. Set duplicate tolerance
9. Define valid extent
10. Choose output paths
11. Click Run

---

## Project Structure

```text
Spatial_QAQC_Tool/
│
├── spatial_qaqc_validator.py
├── README.md
├── sample_data/
├── outputs/
└── screenshots/
```

---

## Project Purpose

The purpose of this project is to demonstrate how spatial data QA/QC workflows can be automated using PyQGIS.

The tool converts repetitive manual validation steps into a reusable and structured workflow for:

- Data validation
- Spatial QA/QC
- Error detection
- Automated correction
- Duplicate detection
- Reporting
- GIS workflow automation

---

## Future Improvements

Possible future enhancements:

- Polygon and line geometry validation
- Topology checks
- CRS mismatch detection
- Batch processing
- Automated QA/QC maps
- Enterprise GIS database integration
- QGIS Plugin version with a custom GUI

---

## Author

Developed as a GIS automation and spatial data quality-control project using **QGIS and PyQGIS**.
