# -*- coding:utf-8 -*-
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, ValidationError
from shapely.geometry import Point
import geopandas as gpd
import os


# 定义请求数据模型
class Coordinates(BaseModel):
    longitude: float = Field(..., description="经度，范围 -180 到 180", ge=-180, le=180)
    latitude: float = Field(..., description="纬度，范围 -90 到 90", ge=-90, le=90)


class GeoCoder:
    def __init__(self, cache=True):
        self.cache = cache
        self.geo_gdf = {}
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
        if self.cache and code in self.geo_gdf:
            return self.geo_gdf[code]
        gdf = gpd.read_file(path)
        if self.cache:
            self.geo_gdf[code] = gdf
        return gdf

    def point_to_location(self, longitude, latitude):
        try:
            point = Point(longitude, latitude)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"无效的点: {str(e)}")

        prov_name, prov_code, city_name, city_code, district_name, district_code = '', '', '', '', '', ''
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
        else:
            raise HTTPException(status_code=404, detail="未找到该点的地理位置")

        return {
            'prov_name': prov_name,
            'prov_code': prov_code,
            'city_name': city_name,
            'city_code': city_code,
            'district_name': district_name,
            'district_code': district_code
        }


# 创建 FastAPI 应用
app = FastAPI()
geocoder = GeoCoder()


@app.post("/geocode", summary="根据经纬度获取地理位置信息")
async def geocode_post(coordinates: Coordinates):
    try:
        result = geocoder.point_to_location(coordinates.longitude, coordinates.latitude)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


@app.get("/geocode", summary="根据经纬度获取地理位置信息 (GET)")
async def geocode_get(
        longitude: float = Query(..., ge=-180, le=180, description="经度，范围 -180 到 180"),
        latitude: float = Query(..., ge=-90, le=90, description="纬度，范围 -90 到 90")
):
    try:
        result = geocoder.point_to_location(longitude, latitude)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")
