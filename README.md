# GIS5572-scripting-land-use

This is a script I wrote to solve a lab exercise.  It takes a DEM and a simplified railroad network for Lake County, MN, and uses them to create zones to aggregate land cover values form a NLCD file.  The output is an Excel workbook with for separate sheets:

* Land cover by elevation, with percentages down the columns (so you know what fraction of each elevation category is categorized as each land cover type
* Land cover by elevation, with percentages across the rows (so you know what fraction of each land cover type is distributed across each elevation category)
* Land cover by railorad distance, with percentages down the columns
* Land cover by railroad distance, with percentages across the rows
