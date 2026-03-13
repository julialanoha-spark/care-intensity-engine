<template>
  <div class="app">
    <header class="header">
      <div class="header-inner">
        <div class="header-left">
          <div class="app-wordmark">
            <span class="w-care">MEDICARE</span>
            <span class="w-sep">·</span>
            <span class="w-intensity">PLAN</span>
            <span class="w-sep">·</span>
            <span class="w-engine">DECISION SUPPORT</span>
          </div>
        </div>
      </div>
    </header>

    <main class="main">
      <div class="panel panel-left">
        <div class="panel-scroll">
          <ScoreDisplay />
          <DemographicSelector />
          <ConditionSelector />
          <ProviderSelector />
          <MedicationSelector />
        </div>
      </div>
      <div class="panel panel-right">
        <div class="panel-scroll">
          <PlanBrowser />
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
import PlanBrowser from './components/PlanBrowser.vue'
import ScoreDisplay from './components/ScoreDisplay.vue'
import DiscussionTopics from './components/DiscussionTopics.vue'

const store = useBeneficiaryStore()
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&display=swap');

:root {
  --bg-base:       #EDE9E3;
  --bg-surface:    #FFFFFF;
  --bg-elevated:   #FDFCFA;
  --bg-hover:      #F7F3ED;
  --border:        #D6D0C7;
  --border-bright: #BDB6AA;

  --text-primary:  #131F5B;
  --text-secondary:#434B72;
  --text-muted:    #8B8FA8;

  --accent:        #131F5B;
  --accent-dim:    rgba(19,31,91,0.08);
  --accent-glow:   rgba(19,31,91,0.18);
  --teal:          #2F4EC4;
  --teal-dim:      rgba(47,78,196,0.08);
  --teal-glow:     rgba(47,78,196,0.15);

  --low:           #2D7A5B;
  --low-dim:       rgba(45,122,91,0.08);
  --moderate:      #B8762A;
  --moderate-dim:  rgba(184,118,42,0.08);
  --high:          #C25630;
  --high-dim:      rgba(194,86,48,0.08);
  --very-high:     #B02B2B;
  --very-high-dim: rgba(176,43,43,0.08);

  --radius:        12px;
  --radius-sm:     8px;
  --font-ui:       'DM Sans', system-ui, sans-serif;
  --font-mono:     'DM Sans', system-ui, sans-serif;
  --font-display:  'DM Serif Display', serif;
}

*, *::before, *::after { box-sizing: border-box; }

body {
  margin: 0;
  font-family: var(--font-ui);
  background: var(--bg-base);
  color: var(--text-primary);
  -webkit-font-smoothing: antialiased;
}

::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-bright); border-radius: 2px; }
</style>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  background: #131F5B;
  border-bottom: none;
  padding: 0 24px;
  height: 54px;
  display: flex;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 8px rgba(19,31,91,0.18);
}

.header-inner {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.app-wordmark {
  display: flex;
  align-items: baseline;
  gap: 6px;
  font-family: var(--font-display);
  font-size: 20px;
  letter-spacing: -0.01em;
}
.w-care      { color: #FFFFFF; font-style: italic; }
.w-intensity { color: #A8B8F0; font-style: normal; }
.w-engine    { color: rgba(255,255,255,0.55); font-size: 13px; font-family: var(--font-ui); font-weight: 400; letter-spacing: 0.02em; align-self: center; }
.w-sep       { color: rgba(255,255,255,0.25); font-size: 10px; }

.app-sub {
  font-size: 10px;
  font-weight: 400;
  color: var(--text-muted);
  letter-spacing: 0.04em;
  font-family: var(--font-mono);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-score-label {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-muted);
  margin-right: 2px;
}

.header-score-num {
  font-family: var(--font-display);
  font-size: 26px;
  line-height: 1;
  color: var(--text-primary);
}
.header-score-denom {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
}

.header-badge {
  font-size: 9px;
  font-weight: 700;
  font-family: var(--font-mono);
  padding: 3px 9px;
  border-radius: 20px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}
.intensity-low       { background: var(--low-dim);       color: var(--low);       border: 1px solid rgba(5,150,105,0.3); }
.intensity-moderate  { background: var(--moderate-dim);  color: var(--moderate);  border: 1px solid rgba(217,119,6,0.3); }
.intensity-high      { background: var(--high-dim);      color: var(--high);      border: 1px solid rgba(234,88,12,0.3); }
.intensity-very-high { background: var(--very-high-dim); color: var(--very-high); border: 1px solid rgba(220,38,38,0.3); }

.main {
  flex: 1;
  display: grid;
  grid-template-columns: 2fr 3fr;
  height: calc(100vh - 54px);
}

.panel { overflow: hidden; display: flex; flex-direction: column; }
.panel-left  { border-right: 1px solid var(--border); background: var(--bg-base); }
.panel-right { background: var(--bg-base); }
.panel-scroll { flex: 1; overflow-y: auto; padding: 12px; }

@media (max-width: 1100px) {
  .main { grid-template-columns: 1fr; height: auto; }
  .panel-left { border-right: none; border-bottom: 1px solid var(--border); }
}
</style>
