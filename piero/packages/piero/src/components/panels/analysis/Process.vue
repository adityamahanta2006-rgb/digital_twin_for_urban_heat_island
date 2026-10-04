<script setup lang="ts">
    import { nextTick, ref } from 'vue';

    import ButtonWithIcon from '@/components/atoms/ButtonWithIcon.vue';
    import BarChart from '@/components/charts/BarChart.vue';
    import DoughnutChart from '@/components/charts/DoughnutChart.vue';
    import DropdownView from '@/components/DropdownView.vue';
    import LoadingIndicator from '@/components/panels/LoadingIndicator.vue';
    import { useProcessesStore } from '@/stores/processes';
    import { ProcessJob, ProcessParams } from '@/types/Process';
    import { useDatasetStore } from '@/stores/datasets';

    const props = defineProps<{
        id: string;
    }>();

    const store = useProcessesStore();
    const datasetStore = useDatasetStore();
    const mapStore = useDatasetStore();

    const loadingProps = ref<boolean>(true);
    const loadingExecution = ref<boolean>(false);
    const loadingJobs = ref<boolean>(true);
    const newProcessTitle = ref<string>("")
    const hasMapOutput = ref<boolean>(false)

    let jobs = ref<ProcessJob[]>([])

    const geoJsonMedia = "application/geo+json";
    const jsonMedia = "application/json";

    function buildOptionsDict(options: string[]) : any{
        return options.map((el) => {
            return {
                "name": el,
                "value": el
            }
        }); 
    }

    function checkMapOutput(){
        const outputs = store.processParams[props.id].outputs;
        
        for(let key of Object.keys(outputs)){            
            if(outputs[key].schema.format.mediaType == "application/geo+json"){
                hasMapOutput.value = true;
                return key;
            }
        }
        hasMapOutput.value = false;
        return null;
    }

    function startSelectFeature(propId: string, propKey: string){
        store.setEnableFeaturePicker(propId, propKey, true);
    }

    async function showResults(jobId: string, outputKey: string){
        // Fetch the response:
        const newDataset = await store.getJobResults(jobId);
        const datasetGeoJson = newDataset[outputKey].value;
        const mediaType = store.processParams[props.id].outputs[outputKey].schema.format.mediaType;
        const jobTitle = jobs.value.find((element) => element.jobID == jobId)?.title;
        console.log(datasetGeoJson);

        // Show in map GeoJSON type
        if(mediaType == "application/geo+json"){
            datasetStore.addResult(jobTitle!, datasetGeoJson);

        } else if (mediaType == "application/json") {

        }
        
    }

    async function fetchProcessJobs(): Promise<void> {
        loadingJobs.value = true;
        // Fetch the params of the process from the API
        try {
            let base_url = "http://127.0.0.1:8000"
            const url = base_url + '/api/jobs?processID=' + props.id;
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
            let processJobsData: ProcessJob[] = data["jobs"];
            jobs.value = processJobsData;            
            
        } catch (err) {
            console.error('Request failed:', err);
        }
        loadingJobs.value = false;
    }

    async function fetchProcessParameters(): Promise<void> {
        if(!store.processParams[props.id]){
            // Fetch the params of the process from the API
            try {
                let base_url = "http://127.0.0.1:8000"
                const url = base_url + '/api/processes/' + props.id;
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
                let processParamsData: ProcessParams = data;
                store.processParams[props.id] = processParamsData;
                store.processParamsValues[props.id] = {}

                for (let key in processParamsData.inputs){
                    if(processParamsData.inputs[key].options != null){
                        store.processParamsValues[props.id][key] = {
                            "name": null,
                            "value": null
                        };
                    } else if (processParamsData.inputs[key].schema.type == "boolean") {
                        store.processParamsValues[props.id][key] = true;
                    } else {
                        store.processParamsValues[props.id][key] = null;
                    }
                }
                
                checkMapOutput(); 
                loadingProps.value = false;
                
            } catch (err) {
                console.error('Request failed:', err);
            }
        } else {
            checkMapOutput(); 
            loadingProps.value = false;
        }
    }

    async function executeProcess(): Promise<void> {
        loadingExecution.value = true;
        const executeUrl = store.getProcessParamExecuteLink(props.id);        
        const executeParameters = store.getParamsForExecution(props.id);

        const body = {
            "inputs": {
                ...executeParameters
            },
            "title": newProcessTitle.value,
            "response": "document"
        }
        JSON.stringify(executeParameters)

        const headers = { 
            'Content-Type': 'application/json',
            'Prefer': 'respond-async'
        }

        try {
            const response = await fetch(executeUrl, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(body)
            });

            if (!response.ok) {
                const text = await response.text();
                console.error('Server error:', response.status, text);
                return;
            }

            const result = await response.json();
            console.log('Execution result:', result);
            refreshJobs()

        } catch (err) {
            console.error('Request failed:', err);
        }
        
        newProcessTitle.value = "";
        loadingExecution.value = false;
    }

    function updateValue(value: any, inputIndex: string){
        store.processParamsValues[props.id][inputIndex] = value;
    }

    function refreshJobs(){
        fetchProcessJobs();
    }

    fetchProcessParameters();
    fetchProcessJobs();

</script>

<template>
    <div v-if="!loadingProps">
        
        <h5>{{ store.processParams[props.id]?.title }}</h5>
        <p>{{ store.processParams[props.id]?.description }}</p>

        <hr></hr>
        <h5>Process Parameters</h5>

        <div class="mb-3" 
            v-for="(item, idx) in store.processParams[props.id].inputs" :key="idx"
        >

            <div class="input-group" v-if="item.schema.type == 'boolean'">
                <div class="form-check form-switch">
                    <input
                        class="form-check-input"
                        :checked="store.processParamsValues[props.id][idx]"
                        type="checkbox"
                        role="switch"
                        :required="item.minOccurs >= 1"
                        id="enable-clippingbox-helper"
                        @input="updateValue(!store.processParamsValues[props.id][idx], String(idx))"
                    />
                    <label class="form-check-label" for="enable-clippingbox-helper"
                        >{{ item.title }}</label
                    >
                </div>
            </div>

            <div 
                v-if="(item.schema.type == 'number' || item.schema.type == 'integer') && item.options == null"
            >
                <label :for="String(idx)" class="form-label">{{ item.title }}</label>
                <input 
                    type="number" 
                    class="form-control"
                    :required="item.minOccurs >= 1"
                    :for="String(idx)" 
                    :id="String(idx)" 
                    :value="store.processParamsValues[props.id][idx]"
                    @input="event => updateValue((event.target as HTMLInputElement).valueAsNumber, String(idx))"
                >
            </div>

            <div
                v-if="(item.schema.type == 'string' || item.schema.type == 'object') && item.options == null"
            >
                <label :for="String(idx)" class="form-label">{{ item.title }}</label>
                <textarea 
                    class="form-control"
                    type="textarea" 
                    :for="String(idx)" 
                    :required="item.minOccurs >= 1"
                    :id="String(idx)" 
                    :value="store.processParamsValues[props.id][idx]"
                    @input="event => updateValue((event.target as HTMLInputElement).value, String(idx))"
                ></textarea>
                <ButtonWithIcon
                    title=""
                    class="btn-primary w-100"
                    @click="startSelectFeature(props.id, String(idx))"
                    icon="bi-pie-chart-fill"
                    text="Select from Map"
                />
            </div>

            <DropdownView
                v-if="item.options != null"
                :label="item.title"
                :for="String(idx)" 
                :required="item.minOccurs >= 1"
                :current="store.processParamsValues[props.id][idx]"
                :items="buildOptionsDict(item.options)"
                @updated:current="src => updateValue(src, String(idx))"
            />
            
            <div v-if="item.schema.type == 'array'">
                <label :for="String(idx)" class="form-label">{{ item.title }}</label>
                <input 
                    type="text" 
                    class="form-control"
                    :for="String(idx)" 
                    :required="item.minOccurs >= 1"
                    :id="String(idx)" 
                    :value="store.processParamsValues[props.id][idx]"
                    @input="event => updateValue((event.target as HTMLInputElement).value, String(idx))"
                >
            </div>
            
            
        </div>

        <hr></hr>

        <input 
            type="text" 
            class="form-control"
            placeholder="Process Title"
            required
            :value="newProcessTitle"
            @input="event => { newProcessTitle = ((event.target as HTMLInputElement).value) }"

        >
        <ButtonWithIcon
            title="Generate stats..."
            class="btn-primary w-100"
            @click="executeProcess"
            icon="bi-pie-chart-fill"
            text="Execute"
        />
        
        <hr></hr>

        <div class="accordion mt-3">
            <div class="accordion-item">
                <h2 class="accordion-header">
                    <button
                        class="accordion-button"
                        type="button"
                        data-bs-toggle="collapse"
                        data-bs-target="#clippingbox-size"
                        aria-expanded="false"
                        aria-controls="clippingbox-size"
                    >
                        Process Results

                    </button>
                </h2>
                <div
                    id="clippingbox-size"
                    class="accordion-collapse collapse show"
                    data-bs-parent="#accordionExample"
                >

                    <LoadingIndicator text="processing..." v-if="loadingJobs" />                    
                    
                    <div class="accordion-body jobs-list" v-if="!loadingJobs">

                        <ButtonWithIcon
                            title=""
                            class="btn-primary w-100 mb-3"
                            @click="refreshJobs()"
                            icon="bi-arrow-clockwise"
                            text="Refresh Results"
                        />

                        <div 
                            class="job-element" 
                            v-for="(item, idx) in jobs" :key="idx"
                        >
                            <div class="justify-content-between align-items-end w-100">
                                <div class="row w-100">
                                    <div class="col-12">
                                        <span class="job-title">{{ item.title != "" ? item.title : "No title" }}</span>
                                    </div>
                                    <div class="col-12">
                                        <span class="job-id">Job ID: {{ item.jobID }}</span>
                                    </div>
                                    <div class="col-12">
                                        <span class="job-meta">Status: {{ item.status }}</span>
                                    </div>
                                    <div class="col-12">
                                        <span class="job-meta">Progress: {{ item.progress }}</span>
                                    </div>
                                </div>
                                <div class="row w-100" v-if="item.status == 'successful'">
                                    <div v-for="(jobOutput, outputKey) in store.processParams[props.id].outputs" :key="outputKey">
                                        <div class="col-12" v-if="jobOutput.schema.format.mediaType == geoJsonMedia">
                                            <button
                                                type="button"
                                                class="btn btn-outline-secondary w-100"
                                                @click="showResults(item.jobID, String(outputKey))"
                                            >
                                                Add to Map
                                            </button>
                                        </div>

                                        <div class="col-12" v-if="jobOutput.schema.format.mediaType == jsonMedia">
                                            <button
                                                type="button"
                                                class="btn btn-outline-secondary w-100"
                                                @click="showResults(item.jobID, String(outputKey))"
                                            >
                                                View Results
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <hr></hr>
                        </div>
                        
                    </div>
                </div>
            </div>
        </div>

    </div>

    <div class="row w-100 my-2">
        <LoadingIndicator text="processing..." v-if="loadingExecution" />
    </div>
</template>

<style scoped>
    .loading-indicator {
        width: 100%;
        height: 100% !important;
        vertical-align: middle;
        font-size: large !important;
        text-align: center;
    }

    .jobs-list{
        max-height: 500px;
        overflow-y: scroll;
    }

    .job-title{
        font-size: 20px;
    }
    .job-id{
        font-size: 10px;
    }
    .job-meta{
        font-size: 15px;
    }
</style>
