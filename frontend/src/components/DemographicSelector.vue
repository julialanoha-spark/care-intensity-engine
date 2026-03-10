<template>
  <div class="section">
    <h3 class="section-title">Demographics</h3>
    <div class="demo-grid">
      <div class="field">
        <label class="field-label">Age Band</label>
        <select v-model="store.ageBand" class="select">
          <option value="unknown">— Select age —</option>
          <option value="under_65">Under 65</option>
          <option value="65_70">65–70</option>
          <option value="70_75">70–75</option>
          <option value="75_80">75–80</option>
          <option value="80_plus">80+</option>
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
          >
            {{ opt.label }}
          </button>
        </div>
      </div>

      <div class="field full-width">
        <label class="checkbox-row">
          <input type="checkbox" v-model="store.medicaidDual" class="checkbox" />
          <span class="checkbox-label">Medicaid dually eligible</span>
          <span class="badge badge-info">+3 pts</span>
        </label>
      </div>
    </div>

    <div v-if="store.ageBand === 'unknown' || store.sex === 'unknown'" class="warning-banner">
      Age and sex are unknown — demographic score will be 0.
    </div>
  </div>
</template>

<script setup>
import { useBeneficiaryStore } from '../stores/beneficiary'

const store = useBeneficiaryStore()

const sexOptions = [
  { value: 'female', label: 'Female' },
  { value: 'male', label: 'Male' },
  { value: 'unknown', label: 'Unknown' },
]
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
.demo-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.field { display: flex; flex-direction: column; gap: 6px; }
.full-width { grid-column: 1 / -1; }
.field-label { font-size: 13px; font-weight: 500; color: #374151; }
.select {
  padding: 8px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  background: white;
  cursor: pointer;
}
.toggle-group { display: flex; gap: 4px; }
.toggle-btn {
  flex: 1;
  padding: 7px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}
.toggle-btn.active {
  background: #1e40af;
  color: white;
  border-color: #1e40af;
}
.checkbox-row { display: flex; align-items: center; gap: 8px; cursor: pointer; }
.checkbox { width: 16px; height: 16px; accent-color: #1e40af; cursor: pointer; }
.checkbox-label { font-size: 14px; color: #374151; }
.badge { font-size: 11px; font-weight: 600; padding: 2px 6px; border-radius: 4px; }
.badge-info { background: #dbeafe; color: #1e40af; }
.warning-banner {
  margin-top: 10px;
  padding: 8px 12px;
  background: #fef9c3;
  border: 1px solid #fde047;
  border-radius: 6px;
  font-size: 12px;
  color: #713f12;
}
</style>
