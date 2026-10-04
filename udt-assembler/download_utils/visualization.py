import os
import rasterio
import numpy as np
import pandas as pd
from pathlib import Path
from rasterio.plot import show
from matplotlib import pyplot

def vis_raster_class_dist(rpath, code_labels, save_to):
    raster_name = Path(rpath).stem
    with rasterio.open(rpath) as src:
        data = src.read(1)
        uniq_counts = np.unique(data, return_counts=True, equal_nan=True)
        print(uniq_counts)
        df = pd.DataFrame(uniq_counts).T
        df = df.rename(columns={0: 'Class_Code', 1: 'Pixel_Count'})
        df['Class_Label'] = df['Class_Code'].apply(lambda x: code_labels.get(x, x))
        # add Class_Label
        # plot
        fig, (axi, axh) = pyplot.subplots(1,2, figsize=(14,7))
        show(src, ax=axi, title=f'MOLCA Map (name={raster_name})')
        #show_hist((src, 1), bins=20, ax=axh)
        df.plot.bar(x='Class_Label', y='Pixel_Count', legend=False,  ax=axh)
        # 在柱状图顶部标注数值
        axh.bar_label(axh.containers[0], fmt='%d', fontsize=12, label_type='edge')
        ipath = os.path.join(save_to, f'{raster_name}_class_distribution.png')
        pyplot.savefig(ipath)
        print('Distrubtion image is saved to ', ipath)