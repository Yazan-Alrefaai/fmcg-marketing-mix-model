# Data (not included)

The weekly dataset was provided privately for a case study and is not redistributed.

To reproduce the analysis, place the Excel file here as `model_variables.xlsx`, with two sheets:

- `Model variables`: 161 weekly rows (January 2022 to January 2025) and 90 columns: our brand's sales, price,
  promotion and distribution; the same measures for three competitors; weekly spend for eight media channels;
  and weather.
- `Variable dictionary`: a description of every column.

`src/01_load_and_clean.py` reads it and writes the cleaned table `clean.csv` used by every later step.
