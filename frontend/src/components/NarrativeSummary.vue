<template>
  <div class="talking-points-card" v-if="show">
    <div class="card-header">
      <span class="card-title">Agent Talking Points</span>
      <span v-if="talkingPoints.length" class="point-count">{{ talkingPoints.length }}</span>
    </div>

    <!-- Loading -->
    <div v-if="store.isLoading" class="loading-row">
      <div class="spinner"></div>
      <span class="loading-text">Generating talking points…</span>
    </div>

    <!-- No API key -->
    <div v-else-if="!narrativeAvailable" class="no-api">
      Add <code>OPENAI_API_KEY</code> to <code>backend/.env</code> to enable talking points.
    </div>

    <!-- Talking point cards -->
    <div v-else-if="talkingPoints.length" class="points-list">
      <div
        v-for="(point, i) in talkingPoints"
        :key="i"
        class="point-card"
      >
        <div class="point-attribute">{{ point.attribute }}</div>
        <div class="point-text">{{ point.text }}</div>
      </div>
    </div>

    <!-- Attribute-only disclaimer -->
    <div v-if="show && !store.isLoading" class="disclaimer">
      <span class="disclaimer-icon">ⓘ</span>
      Based on plan benefit attributes only. Drug formulary coverage and provider network participation are not assessed — verify separately before recommending.
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useBeneficiaryStore } from '../stores/beneficiary'

const store = useBeneficiaryStore()
const result = computed(() => store.scoreResult)

const talkingPoints      = computed(() => result.value?.talking_points || [])
const narrativeAvailable = computed(() => result.value?.narrative_available ?? true)
const show               = computed(() => !!result.value)
</script>

<style scoped>
.talking-points-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  margin-bottom: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}
.card-title {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  color: var(--text-muted);
}
.point-count {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 10px;
  background: var(--teal-dim);
  color: var(--teal);
  border: 1px solid rgba(13,148,136,0.2);
}

/* Loading */
.loading-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
}
.spinner {
  width: 14px; height: 14px;
  border: 2px solid var(--border-bright);
  border-top-color: var(--teal);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}
.loading-text {
  font-size: 12px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}
@keyframes spin { to { transform: rotate(360deg); } }

/* No API key */
.no-api {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.6;
  padding: 4px 0;
}
.no-api code {
  background: var(--bg-base);
  padding: 1px 5px;
  border-radius: 3px;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--accent);
  border: 1px solid var(--border-bright);
}

/* Talking point cards */
.points-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.point-card {
  padding: 12px 14px;
  background: var(--bg-base);
  border: 1px solid var(--border);
  border-left: 3px solid var(--teal);
  border-radius: var(--radius-sm);
}

.point-attribute {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--teal);
  margin-bottom: 6px;
}

.point-text {
  font-size: 13px;
  line-height: 1.65;
  color: var(--text-primary);
}

/* Disclaimer */
.disclaimer {
  margin-top: 12px;
  padding: 8px 12px;
  background: var(--bg-base);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-muted);
  line-height: 1.6;
  display: flex;
  align-items: flex-start;
  gap: 7px;
}
.disclaimer-icon { font-size: 11px; flex-shrink: 0; margin-top: 1px; }
</style>
