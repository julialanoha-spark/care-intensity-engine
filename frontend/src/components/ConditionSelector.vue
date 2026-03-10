<template>
  <div class="section">
    <h3 class="section-title">Chronic Conditions</h3>

    <div v-if="loading" class="loading">Loading…</div>

    <ul v-else class="condition-list">
      <li
        v-for="condition in conditions"
        :key="condition.id"
        class="condition-item"
      >
        <label class="condition-row">
          <input
            type="checkbox"
            class="checkbox"
            :checked="store.selectedConditionIds.includes(condition.id)"
            @change="store.toggleCondition(condition.id)"
          />
          <span class="condition-name">{{ condition.name }}</span>
          <span :class="['tier-badge', `tier-${condition.tier}`]">
            {{ tierLabel(condition.tier) }}
          </span>
        </label>

        <!-- Cancer severity toggle -->
        <div
          v-if="isCancer(condition) && store.selectedConditionIds.includes(condition.id)"
          class="severity-panel"
        >
          <span class="severity-label">Severity:</span>
          <button
            v-for="opt in severityOptions"
            :key="opt.value"
            :class="['severity-btn', { active: store.cancerSeverity === opt.value }]"
            @click="store.cancerSeverity = opt.value"
          >
            {{ opt.label }}
            <span class="severity-pts">{{ opt.pts }}</span>
          </button>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useBeneficiaryStore } from '../stores/beneficiary'
import { fetchConditions } from '../api/careEngine'

const store = useBeneficiaryStore()
const conditions = ref([])
const loading = ref(true)

const severityOptions = [
  { value: 'active', label: 'Active / Metastatic', pts: '14 pts' },
  { value: 'managed', label: 'History / Managed', pts: '7 pts' },
  { value: 'unspecified', label: 'Unspecified', pts: '10 pts' },
]

function isCancer(condition) {
  return condition.name === 'Cancer'
}

function tierLabel(tier) {
  return { high: 'High', medium: 'Medium', low: 'Low' }[tier] || tier
}

onMounted(async () => {
  try {
    conditions.value = await fetchConditions()
    const cancer = conditions.value.find(c => c.name === 'Cancer')
    if (cancer) store.setCancerConditionId(cancer.id)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.section {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
}
.section-title {
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #6b7280;
  margin: 0 0 12px;
}
.loading { color: #9ca3af; font-size: 14px; }
.condition-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 2px; }
.condition-item { border-radius: 6px; overflow: hidden; }
.condition-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 6px;
  cursor: pointer;
  border-radius: 6px;
  transition: background 0.1s;
}
.condition-row:hover { background: #f9fafb; }
.checkbox { width: 16px; height: 16px; accent-color: #1e40af; cursor: pointer; flex-shrink: 0; }
.condition-name { flex: 1; font-size: 14px; color: #111827; }
.tier-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 10px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.tier-high { background: #fee2e2; color: #991b1b; }
.tier-medium { background: #fef3c7; color: #92400e; }
.tier-low { background: #d1fae5; color: #065f46; }

.severity-panel {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 6px 8px 30px;
  flex-wrap: wrap;
}
.severity-label { font-size: 12px; color: #6b7280; font-weight: 500; }
.severity-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: 1px solid #d1d5db;
  border-radius: 20px;
  background: white;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}
.severity-btn.active {
  background: #1e40af;
  color: white;
  border-color: #1e40af;
}
.severity-pts {
  font-size: 11px;
  opacity: 0.7;
}
</style>
