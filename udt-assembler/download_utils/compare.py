import pandas as pd

def csv(f1, f2, row_handler):
    # read files
    df1 = pd.read_csv(f1)
    df2 = pd.read_csv(f2)
    # preprocess the dfs
    df1['to_compare'] = df1.apply(row_handler, axis=1)
    df2['to_compare'] = df2.apply(row_handler, axis=1)
    # compare
    res = pd.merge(df1, df2, on='to_compare', how='left', indicator=True)
    #print(res['_merge'].unique())
    res = res[res['_merge'] == 'left_only']
    
    # report
    unmatched_layers = res['layer_x'].unique()
    print(f"Rows of unmatched: {res.shape[0]}\nUnmatched layers: {unmatched_layers}")
    for nl in unmatched_layers:
        print(f"""Unique Existing_data_location for Unmatched layer {nl}: {res[res['layer_x'] == nl]['Existing_data_location_x'].unique()}""")
    return res.shape[0] == 0