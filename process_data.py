import pandas as pd
import geopandas as gpd
import numpy as np

GLOBAL_CRS = 'EPSG:3435'

census_map = {
    'ASN2E001': 'total_pop',
    'ASQPE001': 'median_income',
    'ASVNE001': 'median_home_value',
    'ASVBE001': 'median_rent',  
}

def main():
    affordable_housing = pd.read_csv('data/Affordable_Rental_Housing_Developments_20250427.csv')
    cook_tracts = gpd.read_file('data/cook_county_tract_2023').to_crs(GLOBAL_CRS)
    chicago_border = gpd.read_file('data/City_Boundary_20250427.geojson').to_crs(GLOBAL_CRS)
    census_raw = pd.read_csv(
        'data/nhgis0060_csv/nhgis0060_ds267_20235_tract.csv',
        usecols=['GISJOIN'] + list(census_map.keys())
    )


    chi_tracts = gpd.clip(
        cook_tracts.sjoin(
            chicago_border, 
            predicate='intersects', 
            how='inner'
        ),
        chicago_border
    )

    census = census_raw.rename(
        columns=census_map
    ).replace(
        -666666666, 
        np.nan
    )

    chi_tracts_with_census_data = chi_tracts.merge(census, how='left', on='GISJOIN')

    af_gdf = gpd.GeoDataFrame(
        affordable_housing, 
        geometry=gpd.points_from_xy(
            affordable_housing.Longitude,
            affordable_housing.Latitude,
            crs='EPSG:4326'
        )
    ).to_crs(GLOBAL_CRS)

    tracts_units = af_gdf.sjoin(
        chi_tracts_with_census_data.loc[:, ['GISJOIN', 'geometry']]
    ).groupby(
        'GISJOIN'
    ).Units.sum().reset_index()

    final_gdf = chi_tracts_with_census_data.merge(tracts_units, on=['GISJOIN'], how='left')

    final_gdf['affordable_units'] = final_gdf.Units.fillna(0)

    final_gdf['affordable_units_per_1000'] = (final_gdf.affordable_units / final_gdf.total_pop) * 1000

    final_cols = [
        'GISJOIN', 
        'geometry',
        'total_pop', 
        'median_income', 
        'median_rent', 
        'median_home_value', 
        'affordable_units', 
        'affordable_units_per_1000'
    ]

    final_gdf.loc[:, final_cols].to_file('data/housing_by_tract.geojson')


if __name__ == '__main__':
    main()


