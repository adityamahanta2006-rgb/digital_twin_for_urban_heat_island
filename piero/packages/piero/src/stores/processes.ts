import { defineStore } from 'pinia';

import type { ProcessParams } from '@/types/Process';
import { reactive, ref } from 'vue';
import { Feature } from 'ol';
import GeoJSONFormat from 'ol/format/GeoJSON';

export const useProcessesStore = defineStore('processes', () => {

    const executeLinkRel = "http://www.opengis.net/def/rel/ogc/1.0/execute";
    
    type processParamsType = { [id: string] : ProcessParams; }
    type processParamsValueType = { [id: string] : any; }

    const processParams = reactive<processParamsType>({})

    const processParamsValues = reactive<processParamsValueType>({})

    const enableFeaturePicker = ref({paramsId: "", propName: "", enabled: false });
    function getEnableFeaturePicker() {
        return enableFeaturePicker.value;
    }
    function setEnableFeaturePicker(paramsId: string, propName: string, enabled: boolean) : void {
        enableFeaturePicker.value = {
            paramsId: paramsId,
            propName: propName,
            enabled: enabled
        } 
    }

    function pickFeature(feature: Feature){
        const format = new GeoJSONFormat();
        const geojsonString = format.writeFeature(feature, { dataProjection: 'EPSG:4326', featureProjection: 'EPSG:3857'});
        console.log(geojsonString);
        const featurePickerInfo = enableFeaturePicker.value;
        processParamsValues[featurePickerInfo.paramsId][featurePickerInfo.propName] = geojsonString;
        setEnableFeaturePicker("", "", false);

    }
    

    const executeBaseUrl = "http://127.0.0.1:8000"

    async function getJobResults(jobId: string): Promise<any>{
        try {
            const url = executeBaseUrl + '/api/jobs/' + jobId + '/results';
            const response = await fetch(url, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) {
                const text = await response.json();
                console.error('Server error:', response.status, text);
                return;
            }

            const data = await response.json();
            return data;
            
        } catch (err) {
            console.error('Request failed:', err);
        }
    }

    function getParamsForExecution(id: string){
        let params: { [id: string] : any; } = {};
        for (const key of Object.keys(processParamsValues[id])){
            if (processParams[id].inputs[key].options != null){
                params[key] = String(processParamsValues[id][key]["value"]);
            } else if(processParams[id].inputs[key].schema.type == "array"){
                params[key] = String(processParamsValues[id][key]).split(",")
            } else {
                params[key] = processParamsValues[id][key];
            }
        }
        return params;
    }

    function getProcessParamExecuteLink(id: string){
        // const links = processParams[id].links;
        // for (let link of links){
        //     if (link.rel == executeLinkRel){
        //         return link.href
        //     }
        // }
        // return null
        const executeUrl = executeBaseUrl + '/api/processes/' + id + "/execution";
        return executeUrl
    }
    

    return {
        processParams,
        processParamsValues,
        getProcessParamExecuteLink,
        getParamsForExecution,
        getJobResults,
        getEnableFeaturePicker,
        setEnableFeaturePicker,
        pickFeature,
    }
});
