<template>
  <div class="score-card">
    <!-- Loading state -->
    <div v-if="store.isLoading" class="score-loading">
      <div class="spinner"></div>
      <span>Calculating…</span>
    </div>

    <!-- Empty state -->
    <div v-else-if="!result" class="score-empty">
      <p>Select conditions, providers, or medications to see the score.</p>
    </div>

    <!-- Score result -->
    <template v-else>
      <!-- Gauge -->
      <div class="gauge-container">
        <svg viewBox="0 0 120 70" class="gauge">
          <!-- Background arc -->
          <path d="M 10 65 A 50 50 0 0 1 110 65" fill="none" stroke="#e5e7eb" stroke-width="10" stroke-linecap="round"/>
          <!-- Score arc -->
          <path
            :d="arcPath"
            fill="none"
            :stroke="intensityColor"
            stroke-width="10"
            stroke-linecap="round"
            class="gauge-arc"
          />
        </svg>
        <div class="gauge-score">
          <span class="score-number">{{ result.total_score }}</span>
          <span class="score-max">/100</span>
        </div>
      </div>

      <!-- Intensity badge -->
      <div class="intensity-row">
        <span :class="['intensity-badge', `intensity-${result.intensity_level.toLowerCase().replace(' ', '-')}`]">
          {{ result.intensity_level }}
        </span>
        <span class="intensity-sub">Care Intensity</span>
      </div>

      <!-- Breakdown bars -->
      <div class="breakdown">
        <div v-for="item in breakdownItems" :key="item.label" class="breakdown-row">
          <span class="breakdown-label">{{ item.label }}</span>
          <div class="bar-track">
            <div class="bar-fill" :style="{ width: item.pct + '%', background: item.color }"></div>
          </div>
          <span class="breakdown-pts">{{ item.value }}<span class="breakdown-max">/{{ item.max }}</span></span>
        </div>
      </div>

      <!-- Interaction badges -->
      <div v-if="result.interactions_triggered?.length > 0" class="interactions">
        <span class="interactions-label">Comorbidity interactions:</span>
        <span
          v-for="pair in result.interactions_triggered"
          :key="pair"
          class="interaction-tag"
        >{{ pair }}</span>
      </div>

      <!-- Missing data warnings -->
      <div v-if="result.flags?.demographic_data_missing" class="flag-banner">
        Age/sex unknown — demographic score is 0
      </div>
      <div v-if="result.flags?.medication_data_missing" class="flag-banner">
        No medications recorded — medication score is 0
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useBeneficiaryStore } from '../stores/beneficiary'

const store = useBeneficiaryStore()
const result = computed(() => store.scoreResult)

const INTENSITY_COLORS = {
  'low': '#22c55e',
  'moderate': '#f59e0b',
  'high': '#f97316',
  'very-high': '#ef4444',
}

const intensityColor = computed(() => {
  if (!result.value) return '#e5e7eb'
  const key = result.value.intensity_level.toLowerCase().replace(' ', '-')
  return INTENSITY_COLORS[key] || '#6b7280'
})

// SVG arc for gauge: maps score 0-100 to half-circle arc
const arcPath = computed(() => {
  if (!result.value) return ''
  const score = result.value.total_score
  const fraction = score / 100
  const startAngle = Math.PI      // 180° (left)
  const endAngle = startAngle + fraction * Math.PI  // up to 0° (right)
  const cx = 60, cy = 65, r = 50
  const x1 = cx + r * Math.cos(Math.PI - startAngle)
  const y1 = cy - r * Math.sin(Math.PI - startAngle)
  const x2 = cx + r * Math.cos(Math.PI - endAngle)
  const y2 = cy - r * Math.sin(Math.PI - endAngle)
  const largeArc = fraction > 0.5 ? 1 : 0
  return `M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`
})

const breakdownItems = computed(() => {
  if (!result.value) return []
  const b = result.value.breakdown
  return [
    { label: 'Demographics', value: b.demographic_score, max: 15, color: '#8b5cf6' },
    { label: 'Conditions', value: b.condition_score, max: 35, color: '#ef4444' },
    { label: 'Providers', value: b.provider_score, max: 25, color: '#3b82f6' },
    { label: 'Medications', value: b.medication_score, max: 25, color: '#f59e0b' },
    { label: 'Interactions', value: b.interaction_bonus, max: 10, color: '#f97316' },
  ].map(item => ({ ...item, pct: Math.round((item.value / item.max) * 100) }))
})
</script>

<style scoped>
.score-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px;
}
.score-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 40px;
  color: #9ca3af;
  font-size: 14px;
}
.spinner {
  width: 20px; height: 20px;
  border: 2px solid #e5e7eb;
  border-top-color: #1e40af;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.score-empty { text-align: center; padding: 40px 20px; color: #9ca3af; font-size: 14px; }

.gauge-container { position: relative; width: 160px; margin: 0 auto 8px; }
.gauge { width: 100%; }
.gauge-arc { transition: all 0.4s ease; }
.gauge-score {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  text-align: center;
  line-height: 1;
}
.score-number { font-size: 32px; font-weight: 700; color: #111827; }
.score-max { font-size: 14px; color: #9ca3af; }

.intensity-row { display: flex; align-items: center; gap: 8px; justify-content: center; margin-bottom: 20px; }
.intensity-badge {
  font-size: 13px;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: 20px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.intensity-low { background: #dcfce7; color: #166534; }
.intensity-moderate { background: #fef3c7; color: #92400e; }
.intensity-high { background: #ffedd5; color: #9a3412; }
.intensity-very-high { background: #fee2e2; color: #991b1b; }
.intensity-sub { font-size: 13px; color: #6b7280; }

.breakdown { display: flex; flex-direction: column; gap: 8px; margin-bottom: 14px; }
.breakdown-row { display: flex; align-items: center; gap: 8px; }
.breakdown-label { font-size: 12px; color: #6b7280; width: 90px; flex-shrink: 0; }
.bar-track { flex: 1; height: 6px; background: #f3f4f6; border-radius: 3px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 3px; transition: width 0.4s ease; }
.breakdown-pts { font-size: 12px; font-weight: 600; color: #374151; width: 36px; text-align: right; flex-shrink: 0; }
.breakdown-max { font-weight: 400; color: #9ca3af; }

.interactions { margin-bottom: 10px; display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.interactions-label { font-size: 11px; color: #6b7280; }
.interaction-tag {
  font-size: 11px;
  padding: 2px 8px;
  background: #ffedd5;
  color: #9a3412;
  border-radius: 10px;
  font-weight: 500;
}
.flag-banner {
  margin-top: 6px;
  padding: 6px 10px;
  background: #fef9c3;
  border: 1px solid #fde047;
  border-radius: 6px;
  font-size: 12px;
  color: #713f12;
}
</style>
