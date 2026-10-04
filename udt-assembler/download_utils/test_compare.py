import os, unittest
import compare

class CompareTest(unittest.TestCase):
    
    def _row_handler(self, row):
        p1 = os.path.basename(os.path.normpath(row['CCI_location']))
        p2 = os.path.basename(os.path.normpath(row['Existing_data_location']))
        return f"{p1};{p2};{row['layer']}"
    
    def test_compare_csv(self):
        f1 = r'S:\InPolimi\ResearchProjects\CCI_HRLC\Phase1\CINECA_processing_and_data\Static_products_processing\Africa_v2\gpkg_africa_static_prod_exist.csv'
        f2 = r'C:\Users\XU\OneDrive - Politecnico di Milano\CCI HRLC\Phase2\MOLCAP\matcher\tmp\result\Static_products_processing\Africa_v2\gpkg_africa_static_prod_exist.csv'
    
        compare.csv(f1, f2, self._row_handler)
        
if __name__ == '__main__':
    unittest.main()