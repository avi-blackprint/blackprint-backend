from utils.dbUtils import RedshiftDatabase
from utils.responseUtils import Response
from psycopg2.extras import RealDictCursor
import time

class BrandController: 
    def __init__(self) :
        self.db = RedshiftDatabase()
    
    @staticmethod
    def get_brand_query(catchment, fid):
        if catchment == '500':
            query = f'''WITH split_values AS (
                        SELECT SPLIT_PART((SELECT ids_pois_500m FROM blackprint_db_prd.data_product.v_parcel_v3 WHERE fid = {fid}), ',', n)::INTEGER as value
                        FROM numbers
                        WHERE n <= f_count_elements((SELECT ids_pois_500m FROM blackprint_db_prd.data_product.v_parcel_v3 WHERE fid = {fid}), ',')
                        )
                        SELECT brand, geometry_wkt, main_category FROM blackprint_db_prd.presentation.dim_places_v2
                        WHERE id_place IN (SELECT value FROM split_values) AND brand IS NOT NULL;'''

        if catchment == '1000':
            query = f'''WITH split_values AS (
                        SELECT SPLIT_PART((SELECT ids_pois_1km FROM blackprint_db_prd.data_product.v_parcel_v3 WHERE fid = {fid}), ',', n)::INTEGER as value
                        FROM numbers
                        WHERE n <= f_count_elements((SELECT ids_pois_1km FROM blackprint_db_prd.data_product.v_parcel_v3 WHERE fid = {fid}), ',')
                        )
                        SELECT brand, geometry_wkt, main_category FROM blackprint_db_prd.presentation.dim_places_v2
                        WHERE id_place IN (SELECT value FROM split_values) AND brand IS NOT NULL;'''

        if catchment == '5':
            query = f'''WITH split_values AS (
                        SELECT SPLIT_PART((SELECT ids_pois_front FROM blackprint_db_prd.data_product.v_parcel_v3 WHERE fid = {fid}), ',', n)::INTEGER as value
                        FROM numbers
                        WHERE n <= f_count_elements((SELECT ids_pois_front FROM blackprint_db_prd.data_product.v_parcel_v3 WHERE fid = {fid}), ',')
                        )
                        SELECT brand, geometry_wkt, main_category FROM blackprint_db_prd.presentation.dim_places_v2
                        WHERE id_place IN (SELECT value FROM split_values) AND brand IS NOT NULL;'''
        return query

    def get_brands(self, radius, fid): 
        connection = None
        cursor = None
        try :
            connection = self.db.connect()
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            query = self.get_brand_query(radius, fid)
            cursor.execute(query)
            connection.commit()
            res = cursor.fetchall()
            print("res=====>", res)
            return Response.success(data={"response": res})
        except Exception as e :
            if connection:
                connection.rollback()
            return Response.internal_server_error(message=str(e))
        finally:
            if cursor:
                cursor.close()
            if connection:
                self.db.disconnect()

class TrafficController:
    def __init__(self) :
        self.db = RedshiftDatabase()

    @staticmethod
    def get_traffic_query(catchment, fid):
        query = None
        if catchment == '500':
            query = f'''SELECT a.fid,
                            b.*
                        FROM  (
                                SELECT i.fid, o AS h3_values_circle_500m
                                FROM blackprint_db_prd.integration.int_predio_radius_v2 i, i.h3_indexes_circle_500m o
                                WHERE i.fid = {fid}
                            ) a
                        INNER JOIN (
                                SELECT *
                                FROM blackprint_db_prd.presentation.dataset_mobility_data_v2
                        ) b on a.h3_values_circle_500m = b.h3_index;'''
        if catchment == '1000':
            query = f'''SELECT a.fid,
                            b.*
                        FROM  (
                                SELECT i.fid, o AS h3_values_circle_1km
                                FROM blackprint_db_prd.integration.int_predio_radius_v2 i, i.h3_indexes_circle_1km o
                                WHERE i.fid = {fid}
                            ) a
                        INNER JOIN (
                                SELECT *
                                FROM blackprint_db_prd.presentation.dataset_mobility_data_v2
                        ) b on a.h3_values_circle_1km = b.h3_index;'''
        if catchment == '5':
            query = f'''SELECT a.fid,
                            b.*
                        FROM  (
                                SELECT i.fid, o AS h3_values_circle_5m
                                FROM blackprint_db_prd.integration.int_predio_radius_v2 i, i.h3_indexes_buffer_dynamic o
                                WHERE i.fid = {fid}
                            ) a
                        INNER JOIN (
                                SELECT *
                                FROM blackprint_db_prd.presentation.dataset_mobility_data_v2
                        ) b on a.h3_values_circle_5m = b.h3_index;'''
        
        return query

    def get_mobility_data_within_buffer(self, fid, radius):
        query  = self.get_traffic_query(radius, fid)
        # Execute the query using your database connection
        connection = None
        cursor = None
        try:
            connection = self.db.connect()
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            print("query=====>", query)
            cursor.execute(query)
            result = cursor.fetchall()
            return Response.success(data={"response": result})
        except Exception as e:
            print(f"Error: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if connection:
                self.db.disconnect()