<template>
  <div class="app">
    <!-- Header -->
    <header class="header">
      <div class="header-inner">
        <div class="header-left">
          <h1 class="app-title">Care Intensity Engine</h1>
          <span class="app-sub">Medicare Agent Decision Support · MVP</span>
        </div>
        <div v-if="store.scoreResult" class="header-score">
          <span :class="['header-badge', `intensity-${store.scoreResult.intensity_level.toLowerCase().replace(' ', '-')}`]">
            {{ store.scoreResult.intensity_level }}
          </span>
          <span class="header-score-num">{{ store.scoreResult.total_score }}/100</span>
        </div>
      </div>
    </header>

    <!-- Main layout -->
    <main class="main">
      <!-- Left: Profile builder -->
      <div class="panel panel-left">
        <div class="panel-scroll">
          <DemographicSelector />
          <ConditionSelector />
          <ProviderSelector />
          <MedicationSelector />
        </div>
      </div>

      <!-- Right: Score + results -->
      <div class="panel panel-right">
        <div class="panel-scroll">
          <ScoreDisplay />
          <NarrativeSummary />
          <DiscussionTopics />
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { useBeneficiaryStore } from './stores/beneficiary'
import DemographicSelector from './components/DemographicSelector.vue'
import ConditionSelector from './components/ConditionSelector.vue'
import ProviderSelector from './components/ProviderSelector.vue'
import MedicationSelector from './components/MedicationSelector.vue'
import ScoreDisplay from './components/ScoreDisplay.vue'
import NarrativeSummary from './components/NarrativeSummary.vue'
import DiscussionTopics from './components/DiscussionTopics.vue'

const store = useBeneficiaryStore()
</script>

<style>
*, *::before, *::after { box-sizing: border-box; }

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f3f4f6;
  color: #111827;
}
</style>

<style scoped>
.app { min-height: 100vh; display: flex; flex-direction: column; }

.header {
  background: white;
  border-bottom: 1px solid #e5e7eb;
  padding: 0 24px;
  height: 56px;
  display: flex;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 10;
}
.header-inner {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.header-left { display: flex; align-items: baseline; gap: 12px; }
.app-title { font-size: 18px; font-weight: 700; color: #111827; margin: 0; }
.app-sub { font-size: 12px; color: #9ca3af; }
.header-score { display: flex; align-items: center; gap: 8px; }
.header-score-num { font-size: 16px; font-weight: 700; color: #374151; }

.header-badge {
  font-size: 12px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 20px;
  text-transform: uppercase;
}
.intensity-low { background: #dcfce7; color: #166534; }
.intensity-moderate { background: #fef3c7; color: #92400e; }
.intensity-high { background: #ffedd5; color: #9a3412; }
.intensity-very-high { background: #fee2e2; color: #991b1b; }

.main {
  flex: 1;
  display: grid;
  grid-template-columns: 420px 1fr;
  gap: 0;
  height: calc(100vh - 56px);
}
.panel { overflow: hidden; display: flex; flex-direction: column; }
.panel-left { border-right: 1px solid #e5e7eb; background: #f9fafb; }
.panel-right { background: #f3f4f6; }
.panel-scroll { flex: 1; overflow-y: auto; padding: 16px; }

@media (max-width: 900px) {
  .main { grid-template-columns: 1fr; height: auto; }
  .panel-left { border-right: none; border-bottom: 1px solid #e5e7eb; }
}
</style>
