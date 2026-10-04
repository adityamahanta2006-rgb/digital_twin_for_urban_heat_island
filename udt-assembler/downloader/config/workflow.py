# default preprocessors
default_preprocessing = [
    {
        "type": "import_grass" # HRLC import and reprojection
    },
    {
        "type": "tile_clip_merge" # Tile clipping/merging
    },
    {
        "type": "set_null" # Set null value
    },
    {
        "type": "reclassify" # Reclassification to hamonized legends (a.k.a. MOLCA)
    }
]