import os, unittest
import coordinates
import json

class CoordinatesTest(unittest.TestCase):
    
    def test_coordinate_range_to_bounding_box(self):
        ranges_map = {
            'Africa/Static': ("0N-18.5N", "18W-43.5E"),
            "Africa/Historical": ("4N-16N", "27E-43.5E"),
            "Siberia/Static": ("52N-79N", "65E-142E"),
            "Siberia/Historical": ("60N-74N", "65E-86E"),
        }
        
        for key, val in ranges_map.items():
            res = coordinates.coordinate_range_to_bounding_box(*val)
            print(f"For {key}, bounding box is {json.dumps(res)}")

    def test_get_bounding_box_from_geojson(self):
        geojson_path = r"/Users/qiong/Library/CloudStorage/OneDrive-PolitecnicodiMilano/CCI HRLC/Phase2/Processing_and_data_descriptions/CCI_regions/ESACCI-HRLC-Ph2-Amazonia_extended_area.geojson"
        get_bounding_box_from_geojson(geojson_path)
            
if __name__ == '__main__':
    unittest.main()