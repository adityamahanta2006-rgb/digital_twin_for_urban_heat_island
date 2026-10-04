import type {
    FeatureElevationCallback,
    FeatureExtrusionOffsetCallback,
    FeatureStyle,
    FeatureStyleCallback,
    FillStyle,
} from '@giro3d/giro3d/core/FeatureTypes';
import type Feature from 'ol/Feature';

import Extent from '@giro3d/giro3d/core/geographic/Extent';
import FeatureCollection from '@giro3d/giro3d/entities/FeatureCollection';
import { GeoJSON } from 'ol/format';
import { tile } from 'ol/loadingstrategy.js';
import VectorSource from 'ol/source/Vector';
import { createXYZ } from 'ol/tilegrid.js';
import { Color } from 'three';

import type { FeatureCollectionDatasetConfig } from '@/types/configuration/datasets/featureCollection';

import { fillObject3DUserData } from '@/loaders/userData';

import type { EntityBuilder } from '../EntityBuilder';
import type { FeatureProjectionMixin } from '../sources/mixins';

/** Options for the Giro3D FeatureCollection */
type FeatureCollectionConstructorOptions = ConstructorParameters<typeof FeatureCollection>[0];

/** Options for {@link FeatureCollectionEntity} */
export interface FeatureCollectionEntityOptions
    extends Partial<
            Pick<
                FeatureCollectionConstructorOptions,
                'extent' | 'ignoreZ' | 'maxLevel' | 'minLevel'
            >
        >,
        Required<FeatureProjectionMixin> {
    /**
     * Set the elevation of the features received from the source.
     * It can be a constant for every feature, or a callback.
     * The callback version is particularly useful to derive the elevation
     * from the properties of the feature.
     * Requires {@link _ignoreZ} to be `false`.
     */
    elevation?: FeatureElevationCallback | number;
    
    /**
     * The name of the layer as exposed by the source.
     */
    layerName?: string;

    /** 
     * The base url of the WFS server
     */
    baseUrl?: string;

    /** 
     * The properties to use as height and elevation for extrusion 
     */
    heightProperty?: string;
    elevationProperty?: string;

    /**
     * If set, this will cause 2D features to be extruded of the corresponding amount.
     * If a single value is given, it will be used for all the vertices of every feature.
     * If an array is given, each extruded vertex will use the corresponding value.
     * If a callback is given, it allows to extrude each feature individually.
     */
    extrusionOffset?: FeatureExtrusionOffsetCallback | number;
    /** Source to use */
    source: 'bdtopo' | 'geojson3d';
    /**
     * An style or a callback returning a style to style the individual features.
     * If an object is used, the informations it contains will be used to style every
     * feature the same way. If a function is provided, it will be called with the feature.
     * This allows to individually style each feature.
     */
    style?: FeatureStyle | FeatureStyleCallback;
}

/**
 * Entity for displaying 3D buildings
 */
export class FeatureCollectionEntity extends FeatureCollection {
    public constructor(options: FeatureCollectionEntityOptions) {

        const crs = options.featureProjection;
        const heightProperty = options.heightProperty ?? 'height';
        const elevationProperty = options.elevationProperty ?? 'elevation';

        let filename: string;
        let wfsUrl: string;
        switch (options.source) {

            case "geojson3d":
                filename = options.layerName ?? 'buildings';
                wfsUrl = options.baseUrl ?? "http://localhost:8081/geoserver/ows"
                break;
            
            case 'bdtopo':
                filename = 'BDTOPO_V3:batiment';
                wfsUrl = "https://data.geopf.fr/wfs/ows"
                break;
            default: {
                // Exhaustiveness checking
                const _exhaustiveCheck: never = options.source;
                return _exhaustiveCheck;
            }
        }

        const vectorSource = new VectorSource({
            format: new GeoJSON(),
            strategy: tile(createXYZ({ tileSize: 1024 })),
            url: function url(bbox): string {
                
                const featureCollectionUrl = `${
                    wfsUrl +
                    '?SERVICE=WFS' +
                    '&VERSION=2.0.0' +
                    '&request=GetFeature' +
                    `&typename=${filename}` +
                    '&outputFormat=application/json' +
                    `&SRSNAME=${crs}` +
                    '&startIndex=0' +
                    `&bbox=${bbox.join(',')},${crs}`
                }`;
                return featureCollectionUrl
            },
        });        

        // url: function url(bbox): string {
        //     return `${
        //         'https://data.geopf.fr/wfs/ows' +
        //         '?SERVICE=WFS' +
        //         '&VERSION=2.0.0' +
        //         '&request=GetFeature' +
        //         '&typename=BDTOPO_V3:batiment' +
        //         '&outputFormat=application/json' +
        //         `&SRSNAME=${crs}` +
        //         '&startIndex=0' +
        //         '&bbox='
        //     }${bbox.join(',')},${crs}`;
        // },

        let extent: Extent;
        if (options.extent === undefined) {
            extent = new Extent('EPSG:4326', -180, 180, -90, 90); // all the world
        } else {
            extent = new Extent(options.extent!.crs, options.extent!.west, options.extent!.east, options.extent!.south, options.extent!.north);
        }        

        const elevation =
            options.elevation ??
            ((feature: Feature): number => {
                const properties = feature.getProperties();
                
                const elevation = properties[elevationProperty];

                if (Number.isNaN(extrusionOffset)) {
                    return 0;
                }
                return elevation;
            });

        const extrusionOffset =
            options.extrusionOffset ??
            ((feature: Feature): number => {
                const properties = feature.getProperties();
                
                const buildingHeight = properties[heightProperty];

                if (Number.isNaN(extrusionOffset)) {
                    return 0;
                }
                return buildingHeight;
            });
        const style =
            options.style ??
            ((feature: Feature): FeatureStyle => {
                const properties = feature.getProperties();
                let fillColor = '#FFFFFF';

                switch (properties.usage_1) {
                    case 'Agricole':
                        fillColor = '#96ff0d';
                        break;
                    case 'Commercial et services':
                        fillColor = '#d8ffd4';
                        break;
                    case 'Industriel':
                        fillColor = '#f0bb41';
                        break;
                    case 'Religieux':
                        fillColor = '#41b5f0';
                        break;
                    case 'Résidentiel':
                        fillColor = '#cec8be';
                        break;
                    case 'Sportif':
                        fillColor = '#ff0d45';
                        break;
                    default:
                        fillColor = '#d0ddff';
                }

                const fill: FillStyle = {
                    color: new Color(fillColor),
                    shading: true,
                };

                return {
                    fill: fill,
                    stroke: {
                        color: 'black',
                        lineWidth: undefined,
                    },
                };
            });

        const parentOptions: ConstructorParameters<typeof FeatureCollection>[0] = {
            extent,
            extrusionOffset,
            elevation,
            maxLevel: options.maxLevel ?? 11,
            minLevel: options.minLevel ?? 11,
            source: vectorSource,
            style,
        };

        super(parentOptions);
        this.name = options.source;
        fillObject3DUserData(this, { filename });
    }
}

export const build: EntityBuilder = context => {
    const cfg = context.dataset.config as FeatureCollectionDatasetConfig;
    const entity = new FeatureCollectionEntity({
        ...cfg,
        featureProjection: context.instance.referenceCrs,
    });

    return Promise.resolve(entity);
};
