<template>
  <div class="section">
    <div class="section-header">
      <span class="section-label">Chronic Conditions</span>
      <span v-if="selectedCount > 0" class="count-chip">{{ selectedCount }}</span>
    </div>

    <div v-if="loading" class="loading">Loading…</div>

    <div v-else class="conditions-grid">
      <button
        v-for="condition in conditions"
        :key="condition.id"
        :class="['condition-pill', `tier-${condition.tier}`, { selected: isSelected(condition.id) }]"
        @click="store.toggleCondition(condition.id)"
      >
        <span :class="['tier-dot', `dot-${condition.tier}`]"></span>
        <span class="pill-name">{{ condition.name }}</span>
      </button>
    </div>

    <!-- Cancer severity -->
    <transition name="fade-down">
      <div v-if="cancerSelected" class="severity-panel">
        <span class="severity-label">Cancer severity</span>
        <div class="severity-options">
          <button
            v-for="opt in severityOptions"
            :key="opt.value"
            :class="['severity-btn', { active: store.cancerSeverity === opt.value }]"
            @click="store.cancerSeverity = opt.value"
          >
            <span class="sev-label">{{ opt.label }}</span>
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useBeneficiaryStore } from '../stores/beneficiary'
import { fetchConditions } from '../api/careEngine'

const store = useBeneficiaryStore()
const conditions = ref([])
const loading = ref(true)

const severityOptions = [
  { value: 'active',      label: 'Active / Metastatic' },
  { value: 'managed',     label: 'History / Managed'   },
  { value: 'unspecified', label: 'Unspecified'          },
]

const isSelected   = id => store.selectedConditionIds.includes(id)
const selectedCount = computed(() => store.selectedConditionIds.length)
const cancerSelected = computed(() => store.hasCancer)

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
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px;
  margin-bottom: 8px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.section-label {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  color: var(--text-muted);
}
.count-chip {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 10px;
  background: var(--teal-dim);
  color: var(--teal);
  border: 1px solid rgba(45,212,191,0.2);
}

.loading { font-size: 12px; color: var(--text-muted); }

.conditions-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 5px;
}

.condition-pill {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 7px 10px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: var(--bg-surface);
  cursor: pointer;
  text-align: left;
  transition: all 0.15s;
  font-family: var(--font-ui);
}
.condition-pill:hover {
  border-color: var(--border-bright);
  background: var(--bg-hover);
}

/* Tier-based selected states */
.condition-pill.tier-high.selected  { background: rgba(248,113,113,0.08); border-color: rgba(248,113,113,0.35); }
.condition-pill.tier-medium.selected { background: rgba(251,191,36,0.08); border-color: rgba(251,191,36,0.30); }
.condition-pill.tier-low.selected   { background: rgba(52,211,153,0.08); border-color: rgba(52,211,153,0.30); }

.tier-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot-high   { background: var(--very-high); box-shadow: 0 0 4px rgba(248,113,113,0.5); }
.dot-medium { background: var(--moderate);  box-shadow: 0 0 4px rgba(251,191,36,0.4); }
.dot-low    { background: var(--low);       box-shadow: 0 0 4px rgba(52,211,153,0.4); }

.pill-name {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.3;
  flex: 1;
}
.condition-pill.selected .pill-name { color: var(--text-primary); }

/* Severity panel */
.severity-panel {
  margin-top: 10px;
  padding: 10px 12px;
  background: rgba(248,113,113,0.05);
  border: 1px solid rgba(248,113,113,0.2);
  border-radius: var(--radius-sm);
}
.severity-label {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--very-high);
  display: block;
  margin-bottom: 8px;
}
.severity-options { display: flex; gap: 5px; flex-wrap: wrap; }
.severity-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  border: 1px solid var(--border-bright);
  border-radius: 20px;
  background: var(--bg-surface);
  cursor: pointer;
  transition: all 0.15s;
  font-family: var(--font-ui);
}
.severity-btn:hover { border-color: var(--very-high); }
.severity-btn.active {
  background: rgba(248,113,113,0.12);
  border-color: var(--very-high);
}
.sev-label { font-size: 11px; color: var(--text-secondary); }
.severity-btn.active .sev-label { color: var(--very-high); }
.sev-pts {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-muted);
}
.severity-btn.active .sev-pts { color: rgba(248,113,113,0.7); }

/* Transition */
.fade-down-enter-active { transition: all 0.2s ease; }
.fade-down-leave-active { transition: all 0.15s ease; }
.fade-down-enter-from   { opacity: 0; transform: translateY(-6px); }
.fade-down-leave-to     { opacity: 0; transform: translateY(-4px); }
</style>
