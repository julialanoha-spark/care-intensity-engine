<template>
  <div class="section">
    <div class="section-header">
      <span class="section-label">Demographics</span>
    </div>

    <div class="demo-grid">
      <div class="field">
        <label class="field-label">Age Band</label>
        <select v-model="store.ageBand" class="select">
          <option value="unknown">— Select —</option>
          <option value="under_65">Under 65</option>
          <option value="65_70">65 – 70</option>
          <option value="70_75">70 – 75</option>
          <option value="75_80">75 – 80</option>
          <option value="80_plus">80 +</option>
        </select>
      </div>

      <div class="field">
        <label class="field-label">Sex</label>
        <div class="toggle-group">
          <button
            v-for="opt in sexOptions"
            :key="opt.value"
            :class="['toggle-btn', { active: store.sex === opt.value }]"
            @click="store.sex = opt.value"
          >{{ opt.label }}</button>
        </div>
      </div>

      <div class="field full-width">
        <div class="medicaid-row" @click="store.medicaidDual = !store.medicaidDual">
          <div class="custom-cb" :class="{ checked: store.medicaidDual }">
            <svg v-if="store.medicaidDual" viewBox="0 0 10 10" fill="none">
              <path d="M1.5 5L4 7.5L8.5 2.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <span class="medicaid-label">Medicaid dually eligible</span>
          <span class="pts-chip">+3 pts</span>
        </div>
      </div>

      <div class="field full-width">
        <label class="field-label">Service Area ZIP</label>
        <input
          v-model="store.zip"
          class="zip-input"
          type="text"
          inputmode="numeric"
          maxlength="5"
          placeholder="e.g. 90210"
        />
        <span class="zip-hint">Filters available plans to your market</span>
      </div>
    </div>

    <div v-if="store.ageBand === 'unknown' || store.sex === 'unknown'" class="warn-banner">
      <span class="warn-icon">▲</span>
      Age / sex unknown — demographic score is 0
    </div>
  </div>
</template>

<script setup>
import { useBeneficiaryStore } from '../stores/beneficiary'

const store = useBeneficiaryStore()
const sexOptions = [
  { value: 'female', label: 'F' },
  { value: 'male',   label: 'M' },
  { value: 'unknown', label: '?' },
]
</script>

<style scoped>
.section {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px;
  margin-bottom: 8px;
}

.section-header { margin-bottom: 12px; }
.section-label {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  color: var(--text-muted);
}

.demo-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.field { display: flex; flex-direction: column; gap: 5px; }
.full-width { grid-column: 1 / -1; }

.field-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.select {
  padding: 7px 10px;
  border: 1px solid var(--border-bright);
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-family: var(--font-ui);
  background: var(--bg-surface);
  color: var(--text-primary);
  cursor: pointer;
  outline: none;
  transition: border-color 0.15s;
}
.select:focus { border-color: var(--teal); box-shadow: 0 0 0 2px var(--teal-dim); }
.select option { background: var(--bg-surface); color: var(--text-primary); }

.toggle-group { display: flex; gap: 3px; }
.toggle-btn {
  flex: 1;
  padding: 7px 4px;
  border: 1px solid var(--border-bright);
  border-radius: var(--radius-sm);
  background: var(--bg-surface);
  color: var(--text-secondary);
  font-size: 12px;
  font-family: var(--font-ui);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}
.toggle-btn:hover { border-color: var(--teal); color: var(--teal); }
.toggle-btn.active {
  background: var(--teal-dim);
  border-color: var(--teal);
  color: var(--teal);
  font-weight: 600;
}

.medicaid-row {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 4px 0;
  user-select: none;
}
.custom-cb {
  width: 16px;
  height: 16px;
  border: 1px solid var(--border-bright);
  border-radius: 4px;
  background: var(--bg-surface);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.15s;
  color: var(--teal);
}
.custom-cb svg { width: 10px; height: 10px; }
.custom-cb.checked {
  background: var(--teal-dim);
  border-color: var(--teal);
}
.medicaid-label { font-size: 13px; color: var(--text-primary); flex: 1; }
.pts-chip {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 10px;
  background: var(--teal-dim);
  color: var(--teal);
  border: 1px solid rgba(45,212,191,0.2);
}

.warn-banner {
  margin-top: 10px;
  padding: 7px 11px;
  background: var(--accent-dim);
  border: 1px solid rgba(245,158,11,0.2);
  border-radius: var(--radius-sm);
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--accent);
  display: flex;
  align-items: center;
  gap: 8px;
}
.warn-icon { font-size: 9px; }

/* ZIP input */
.zip-input {
  padding: 7px 10px;
  border: 1px solid var(--border-bright);
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-family: var(--font-ui);
  background: var(--bg-surface);
  color: var(--text-primary);
  outline: none;
  transition: border-color 0.15s;
  width: 100%;
}
.zip-input:focus { border-color: var(--teal); box-shadow: 0 0 0 2px var(--teal-dim); }
.zip-input::placeholder { color: var(--text-muted); }
.zip-hint {
  font-size: 10px;
  color: var(--text-muted);
  font-family: var(--font-mono);
  margin-top: 2px;
}
</style>
