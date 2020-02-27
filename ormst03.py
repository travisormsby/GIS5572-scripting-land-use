import sys
import arcpy
import pandas as pd

def reclass (raster, raster_type, reclass_map):
    arcpy.ddd.Reclassify(raster, 
                         "Value", 
                         reclass_map, 
                         f'{raster_type}_reclass', 
                         "NODATA")    

def rr_buffer (railroad):
    arcpy.analysis.Buffer(railroad,
                          "railroad_Buffer",
                          "6 Miles",
                          "FULL",
                          "FLAT",
                          "ALL",
                          None,
                          "PLANAR")
    
def pixel_count (zones, zone_field, out_table):
    arcpy.env.mask = 'dem_reclass'
    arcpy.sa.ZonalHistogram(zones, zone_field, "lu_reclass", out_table, None)
    
def table_to_df(table):
    arr = arcpy.da.TableToNumPyArray(table, '*')
    df = pd.DataFrame.from_records(arr)
    return df

def main(workspace, dem, lu, railroad, out_file):
    # set environmental variables
    arcpy.env.workspace = workspace
    arcpy.env.mask = None 
    arcpy.env.overwriteOutput = True

    # reclass the dem and land use rasters by the pre-defined reclass map
    reclass(dem, 'dem', "-9999 -1 1;0 NODATA;1 1000 1;1001 1400 2;1401 1800 3;1801 2200 4")
    reclass(lu, 'lu', "0 10 NODATA;11 12 1;21 23 2;31 33 3;41 43 4;51 51 5;61 61 6;71 71 7;81 85 8;91 92 9")

    # we want to know which areas are within the 6 mile buffer of railroads
    rr_buffer(railroad)

    # count the number of pixels in each elevation and railroad distance zone
    # and write the output to two geodatabase tables
    pixel_count('dem_reclass', 'Value', 'lu_by_elev')
    pixel_count('railroad_buffer', 'OBJECTID', 'lu_by_rrdist')

    # read the land use pixel count by elevation into a pandas datafram
    # and reformat it
    elev_df = table_to_df('lu_by_elev')
    elev_df = elev_df.rename(columns={'LABEL': 'Land Use',
                                      'Value_1': '1000ft and less pixel count', 
                                      'Value_2': '1001 to 1400ft pixel count', 
                                      'Value_3': '1401 to 1800ft pixel count', 
                                      'Value_4': '1801 to 2200ft pixel count'})
    
    lu_dict = {1:'Water', 
               2:'Developed', 
               3:'Barren', 
               4:'Forested Upland', 
               5: 'Shrubland',
               6: 'Non-natural Woody',
               7: 'Herbaceous Upland',
               8: 'Herbaceous Planted / Cultivated',
               9: 'Wetlands'}
    
    elev_df['Land Use'] = elev_df['Land Use'].astype('int32').map(lu_dict)
    
    # calculate the column totals
    elev_df = elev_df.pivot_table(index='Land Use',
               values=elev_df.columns[2:],
               margins=True,
               margins_name='TOTALS',
               aggfunc=sum)

    # calculate the row totals
    elev_df['TOTALS'] = elev_df.sum(axis=1)
    
    # complete the same steps for the land use by railroad distance table
    rrdist_df = table_to_df('lu_by_rrdist')
    rrdist_df = rrdist_df.rename(columns={'LABEL': 'Land Use',
                                          'OBJEC_1': 'Close to RR Pixel Count'})
    
    rrdist_df['Land Use'] = rrdist_df['Land Use'].astype('int32').map(lu_dict)
    
    rrdist_df = rrdist_df.pivot_table(index='Land Use',
                values=rrdist_df.columns[2:],
                margins=True,
                margins_name='TOTALS',
                aggfunc=sum)    
    
    # join the railroad distance table to elevation table, so that
    # the pixel count for areas far from railroads can be calculated
    # from the difference to the total number of pixels
    pixel_count_df = rrdist_df.join(elev_df, on='Land Use')
    pixel_count_df['Far from RR Pixel Count'] = pixel_count_df['TOTALS'] - pixel_count_df['Close to RR Pixel Count']
    
    
    # calculate percentages by row and by column   
    by_rows_df = pixel_count_df.loc[:].div(pixel_count_df.loc[:,'TOTALS'], axis=0)
    by_rows_df = by_rows_df.rename(columns={k:k+' row %' for k in by_rows_df.columns})
    
    by_columns_df = pixel_count_df.loc[:].div(pixel_count_df.loc['TOTALS', :], axis=1)
    by_columns_df = by_columns_df.rename(columns={k:k+' column %' for k in by_columns_df.columns})

    # join the percentage calculation dataframes to the pixel count dataframe
    df = pixel_count_df.join(by_rows_df, on='Land Use')
    df = df.join(by_columns_df, on='Land Use')

    # write the output to seperate worksheets in a single Excel workbook
    with pd.ExcelWriter(out_file) as writer:
        sheets = ['elev_by_rows', 'elev_by_columns', 'rr_by_rows', 'rr_by_columns']
    
        df.iloc[:,[1, 8, 2, 9, 3, 10, 4, 11, 5, 12]].to_excel(writer, sheet_name=sheets[0])
        df.iloc[:,[1, 15, 2, 16, 3, 17, 4, 18, 5, 19]].to_excel(writer, sheet_name=sheets[1])
        df.iloc[:,[0, 7, 6, 13, 5, 12]].to_excel(writer, sheet_name=sheets[2])
        df.iloc[:,[0, 14, 6, 20, 5, 19]].to_excel(writer, sheet_name=sheets[3])

    # let the analyst know the scripts has finished    
    print(f'{out_file} completed')


# set up parameters for the function.  The function could be run in a loop
# iteratively over a list of sets of parameters.
workspace = r'C:\Users\orms0027\Documents\GIS5572\EX03\EX03.gdb'
dem = r"C:\Users\orms0027\Documents\GIS5572\EX03\ex03data\lkdem.tif"
lu = r"C:\Users\orms0027\Documents\GIS5572\EX03\ex03data\lklu.tif"
railroad = 'lkrr_SimplifyLine'
out_file = '27075.xlsx'
main(workspace, dem, lu, railroad, out_file)
