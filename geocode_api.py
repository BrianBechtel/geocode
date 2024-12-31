# -*- coding:utf-8 -*-
# @Author: H
# @Date: 2024-07-08 10:56:04
# @Version: 1.1
# @License: H
# @Desc: FastAPI Implementation

import os
import geopandas as gpd
from shapely.geometry import Point
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI()

class GeoCoder:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(GeoCoder, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, cache=True):
        self.cache = cache
        self.geo_gdf = {}

        # Load GeoJSON data file
        self.DIR_BASE = os.path.dirname(os.path.abspath(__file__))
        self.base_gdf = gpd.read_file(os.path.join(self.DIR_BASE, 'geodata', 'china.json'))

    def get_point_df(self, gdf, point):
        if gdf is None:
            return None
        for _, row in gdf.iterrows():
            if row['geometry'].buffer(0).contains(point):
                return row
        return None

    def get_gdf(self, type, code):
        path = os.path.join(self.DIR_BASE, 'geodata', type, f'{code}.json')
        if not os.path.exists(path):
            return None
        if self.cache:
            if code in self.geo_gdf:
                return self.geo_gdf[code]
            else:
                gdf = gpd.read_file(path)
                self.geo_gdf[code] = gdf
                return gdf
        else:
            return gpd.read_file(path)

    def point_to_location(self, longitude, latitude):
        prov_name, prov_code, city_name, city_code, district_name, district_code = '', '', '', '', '', ''
        try:
            longitude, latitude = float(longitude), float(latitude)
        except ValueError:
            raise HTTPException(status_code=400, detail=f'Invalid latitude or longitude: {longitude}, {latitude}')

        point = Point(longitude, latitude)
        prov_df = self.get_point_df(self.base_gdf, point)
        if prov_df is not None:
            prov_code = str(prov_df['adcode'])
            prov_name = prov_df['name']

            city_gdf = self.get_gdf('province', prov_code)
            city_df = self.get_point_df(city_gdf, point)
            if city_df is not None:
                city_code = str(city_df['adcode'])
                city_name = city_df['name']

                if prov_name in {'北京市', '上海市', '天津市', '重庆市'}:
                    district_name = city_name
                    district_code = city_code
                    city_name = prov_name
                    city_code = prov_code
                else:
                    district_gdf = self.get_gdf('citys', city_code)
                    district_df = self.get_point_df(district_gdf, point)
                    district_name = district_df['name'] if district_df is not None else ''
                    district_code = district_df['adcode'] if district_df is not None else ''

        return {
            'prov_name': prov_name,
            'prov_code': prov_code,
            'city_name': city_name,
            'city_code': city_code,
            'district_name': district_name,
            'district_code': district_code
        }

# Initialize GeoCoder instance
g = GeoCoder()

class Coordinates(BaseModel):
    longitude: float
    latitude: float

@app.post("/geocode")
async def geocode_location(coords: Coordinates):
    result = g.point_to_location(coords.longitude, coords.latitude)
    return result

@app.get("/geocode")
async def geocode_location_get(longitude: float = Query(...), latitude: float = Query(...)):
    result = g.point_to_location(longitude, latitude)
    return result
