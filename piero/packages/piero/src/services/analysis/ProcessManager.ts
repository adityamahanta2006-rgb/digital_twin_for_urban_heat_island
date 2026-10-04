import type Instance from '@giro3d/giro3d/core/Instance';

import type LayerManager from '@/services/LayerManager';

import { useAnalysisStore } from '@/stores/analysis';
import { useProcessesStore } from '@/stores/processes';
import ColorLayer from '@giro3d/giro3d/core/layer/ColorLayer';
import VectorSource from '@giro3d/giro3d/sources/VectorSource';
import GeoJSON from "ol/format/GeoJSON.js";
import { Fill, Stroke, Style } from 'ol/style';
import { useDatasetStore } from '@/stores/datasets';
import Coordinates from '@giro3d/giro3d/core/geographic/Coordinates';

export default class ProcessManager {
    private readonly _instance: Instance;
    private readonly _layerManager: LayerManager;
    private readonly _store = useAnalysisStore();
    private readonly _process_store = useProcessesStore();
    private readonly _layerPanelStore = useDatasetStore();

    public constructor(instance: Instance, layerManager: LayerManager) {
        this._instance = instance;
        this._layerManager = layerManager;

        const getGeoJsonPick = (mouseEvent: any) => {
            const pickResult = this._instance.pickObjectsAt(mouseEvent);
            const picked = pickResult[0];

            if (picked) {
                const { x, y } = picked.point;
                const coordinates = new Coordinates(this._instance.referenceCrs, x, y);
                const colorLayers = this._layerManager.getLayers();
                let selectedLayer = null;
                let features = [];
                for(let layer of colorLayers){                                       
                    if (layer.visible && layer.source.type == "VectorSource"){
                        const featuresAtCoordinate = (layer as any).getVectorFeaturesAtCoordinate(coordinates, {
                            radius: 5,
                            xTileRes: 5,
                            yTileRes: 5,
                        });
                        if(featuresAtCoordinate.length > 0){
                            features.push(...featuresAtCoordinate);
                            selectedLayer = layer;
                            break
                        }
                        // features.push(...featuresAtCoordinate);
                    }
                }

                if (features.length > 0) {
                    const firstFeature = features[0];
                    console.log(firstFeature);
                    this._process_store.pickFeature(firstFeature);
                    this._process_store.setEnableFeaturePicker("", "", false);
                }
            } 
        
        }

        this._process_store.$onAction(({ after, args, name }) => {
        after(() => {
                switch (name) {
                    case 'setEnableFeaturePicker':
                        console.log(args[2]);
                        if (args[2] == true){ // is enabled
                            console.log("enabled");
                            this._instance.domElement.addEventListener("click", getGeoJsonPick);
                        } else {
                            console.log("disabled");
                            this._instance.domElement.removeEventListener('click', getGeoJsonPick);
                        }
                        break
                }
            });
    })
    }

    public dispose(): void {}
}
