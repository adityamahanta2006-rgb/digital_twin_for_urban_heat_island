<script setup lang="ts">
    import { useAnalysisStore } from '@/stores/analysis';

    import CrossSection from './analysis/CrossSection.vue';
    import FloodingPlane from './analysis/FloodingPlane.vue';
    import Statistics from './analysis/Statistics.vue';
    import Process from './analysis/Process.vue';
    import ToolWrapper from './analysis/ToolWrapper.vue';
    import { ProcessBasic } from '@/types/Process';
    import { ref } from 'vue';

    const analysis = useAnalysisStore();    

    const loading = ref(true);
    
    async function getProcessesList(){
        try {
            let base_url = "http://127.0.0.1:8000"
            const url = base_url + '/api/processes';
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
            let processesListData: ProcessBasic[] = data["processes"];
            analysis.openedProcesses["flooding-plane"] = false;            
              
            for (let value of processesListData){
                analysis.openedProcesses[value.id] = false;
            }
            
            analysis.setProcessList(processesListData)
            loading.value = false;
            
        } catch (err) {
            console.error('Request failed:', err);
        }
        
    }

    if (analysis.getProcessList().length == 0){
        getProcessesList();
    } else {
        loading.value = false;
    }


</script>

<template>
    <div v-if="!loading">
        <div>
            <ToolWrapper
                class="tool"
                id="flooding-plane"
                title="Flooding plane"
                icon="bi-layers-half"
                :expanded="analysis.openedProcesses['flooding-plane']"
                :collapsible="true"
                @update:expanded="analysis.updateOpen"
            >
                <FloodingPlane />
            </ToolWrapper>
        </div>
        <!-- <ToolWrapper
            class="tool"
            id="cross-section"
            title="Cross section"
            icon="bi-circle-half"
            :expanded="analysis.isCrossSectionEnabled()"
            :collapsible="true"
            @update:expanded="analysis.enableCrossSection"
        >
            <CrossSection />
        </ToolWrapper> -->

        <!-- <ToolWrapper
            class="tool"
            id="clipping-box"
            title="Clipping Box"
            icon="bi-bounding-box"
            :expanded="analysis.isClippingBoxEnabled()"
            :collapsible="true"
            @update:expanded="analysis.enableClippingBox"
        >
            <ClippingBox />
        </ToolWrapper> -->

        <!-- <ToolWrapper
            class="tool"
            id="statistics"
            title="Statistics"
            icon="bi-bar-chart-line"
            :expanded="analysis.isStatisticsEnabled()"
            :collapsible="true"
            @update:expanded="analysis.enableStatistics"
        >
            <Statistics />
        </ToolWrapper> -->
        <div 
            v-for="(item, idx) in analysis.getProcessList()" :key="idx">
            <ToolWrapper
                class="tool"
                :id=item.id
                :title=item.title
                icon="bi-bar-chart-line"
                :expanded="analysis.openedProcesses[item.id]"
                :collapsible="true"
                @update:expanded="analysis.updateOpen"
            >
                <Process :id="item.id" />
            </ToolWrapper>
        </div>
    </div>
</template>

<style scoped>
    .tool {
        box-shadow: 1px 1px 5px rgba(0, 0, 0, 0.1);
        margin-top: 1rem;
    }
</style>
