import os, sys, io
import unittest

from downloader import default_dest_dir_generator, GEEDownloader, URLDownloader, BatchDownloader

class DownloaderTest(unittest.TestCase):
    def setUp(self):
        # set config
        self.gee_service_account_key = r'C:\Users\XU\Downloads\cci-hrlc-ph2-benchmarking-f54c633a7075.json'
        # set dir
        self.base_resdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), r"maps")
        
    def test_gee_downloader(self):
        info = { # Africa Historical
            "region": "Africa",
            "year": 2015,
            "map_name": "DynamicWorld",
            "map_year": 2015,
            "type": "GEE",
            "url": "GOOGLE/DYNAMICWORLD/V1",
            "aoi": [[27, 16.3], [27, 3.5], [43.3, 3.5], [43.3, 16.3], [27, 16.3]],
            "gee_collection_extract_method": "MODE", 
            "scale": 10,
            'bands': ['label'],
        }
        dest_dir = default_dest_dir_generator(self.base_resdir, info)
        gd = GEEDownloader(self.gee_service_account_key)
        gd.download(info, dest_dir)
    
    def test_url_downloader(self):
        info = { # Amazon Extension
            "region": "Amazon_Extension",
            "year": 2019,
            "map_name": "GFC",
            "map_year": 2020,
            "type": "URL",
            "url": "https://ies-ows.jrc.ec.europa.eu/iforce/gfc2020/download.py?type=tile&lat=N0&lon=W70",
        } #PASS
        dest_dir = default_dest_dir_generator(self.base_resdir, info)
        ud = URLDownloader()
        ud.download(info, dest_dir)
    
    def test_batch_downloader(self): pass
    
    
if __name__ == '__main__':
    unittest.main()