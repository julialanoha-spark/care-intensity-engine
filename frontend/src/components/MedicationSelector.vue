<template>
  <div class="section">
    <div class="section-header">
      <span class="section-label">Medications</span>
      <span v-if="store.medicationEntries.length > 0" class="count-chip">
        {{ store.medicationEntries.length }}
      </span>
      <span v-if="hasSpecialty" class="specialty-chip">Specialty Rx</span>
    </div>

    <!-- Add-medication form -->
    <div class="add-form">

      <!-- Step 1: Drug name typeahead -->
      <div class="form-row">
        <label class="form-label">Medication</label>
        <div class="search-wrap">
          <svg class="search-icon" viewBox="0 0 16 16" fill="none">
            <circle cx="6.5" cy="6.5" r="4.5" stroke="currentColor" stroke-width="1.5"/>
            <path d="M10 10L14 14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <input
            v-model="drugQuery"
            ref="drugInputEl"
            class="form-input"
            placeholder="Search drug name…"
            type="text"
            autocomplete="off"
            @focus="showDrugDropdown = true"
            @blur="onDrugBlur"
            @input="onDrugInput"
          />
          <button v-if="drugQuery && !selectedDrug" class="input-clear" @mousedown.prevent @click="clearDrug">×</button>
          <span v-if="selectedDrug" class="input-check">✓</span>
        </div>

        <!-- Drug dropdown -->
        <div v-if="showDrugDropdown && filteredDrugs.length > 0" class="dropdown">
          <button
            v-for="drug in filteredDrugs"
            :key="drug"
            class="dropdown-item"
            :class="{ selected: selectedDrug === drug }"
            @mousedown.prevent
            @click="selectDrug(drug)"
          >
            <span class="di-name">{{ drug }}</span>
            <span v-if="isDrugSpecialty(drug)" class="di-spec">Specialty</span>
          </button>
        </div>
        <div v-if="showDrugDropdown && drugQuery.length >= 2 && filteredDrugs.length === 0" class="dropdown">
          <div class="dropdown-empty">No results for "{{ drugQuery }}"</div>
        </div>
      </div>

      <!-- Step 2: Dosage (only after drug selected) -->
      <transition name="fade-down">
        <div v-if="selectedDrug" class="form-row">
          <label class="form-label">Dosage</label>
          <select v-model="selectedMedId" class="form-select">
            <option value="">— Select dosage —</option>
            <option
              v-for="med in dosageOptions"
              :key="med.id"
              :value="med.id"
            >{{ extractDosageForm(med.dosage, med.name) }}</option>
          </select>
        </div>
      </transition>

      <!-- Step 3: Quantity + Frequency (only after dosage selected) -->
      <transition name="fade-down">
        <div v-if="selectedMedId" class="form-row form-row-split">
          <div class="form-col">
            <label class="form-label">Quantity</label>
            <input
              v-model.number="quantity"
              type="number"
              min="1"
              max="999"
              class="form-input qty-input"
              placeholder="30"
            />
          </div>
          <div class="form-col">
            <label class="form-label">Frequency</label>
            <select v-model="frequency" class="form-select">
              <option v-for="f in FREQUENCIES" :key="f.value" :value="f.value">
                {{ f.label }}
              </option>
            </select>
          </div>
        </div>
      </transition>

      <!-- Add button -->
      <transition name="fade-down">
        <button
          v-if="selectedMedId"
          class="add-btn"
          :disabled="!canAdd"
          @click="addEntry"
        >
          + Add Medication
        </button>
      </transition>
    </div>

    <!-- Medication entries list -->
    <div v-if="store.medicationEntries.length > 0" class="entries-list">
      <div class="entries-label">Added Medications</div>
      <div
        v-for="(entry, idx) in store.medicationEntries"
        :key="idx"
        class="entry-card"
        :class="{ 'entry-specialty': entry.isSpecialty }"
      >
        <div class="entry-main">
          <div class="entry-top">
            <span class="entry-drug">{{ entry.drugName }}</span>
            <span v-if="entry.isSpecialty" class="entry-spec-badge">Specialty</span>
          </div>
          <div class="entry-dosage">{{ extractDosageForm(entry.dosageName, entry.drugName) }}</div>
        </div>
        <div class="entry-meta">
          <span class="entry-qty">{{ entry.quantity }}</span>
          <span class="entry-sep">×</span>
          <span class="entry-freq">{{ freqLabel(entry.frequency) }}</span>
        </div>
        <button class="entry-remove" @click="store.removeMedication(idx)">×</button>
      </div>
    </div>

    <p v-else-if="allMedications.length > 0 && store.medicationEntries.length === 0" class="hint">
      Search and add medications to the profile
    </p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useBeneficiaryStore } from '../stores/beneficiary'
import { fetchMedications } from '../api/careEngine'

const store = useBeneficiaryStore()

const allMedications = ref([])
const loadError = ref(false)

const drugQuery        = ref('')
const selectedDrug     = ref('')
const selectedMedId    = ref('')
const quantity         = ref(30)
const frequency        = ref('ONE')
const showDrugDropdown = ref(false)
const drugInputEl      = ref(null)

const FREQUENCIES = [
  { value: 'ONE',    label: 'Once daily'          },
  { value: 'TWO',    label: 'Twice daily'          },
  { value: 'THREE',  label: 'Three times daily'    },
  { value: 'SIX',    label: 'Six times daily'      },
  { value: 'TWELVE', label: 'Twelve times daily'   },
]

function freqLabel(val) {
  return FREQUENCIES.find(f => f.value === val)?.label ?? val
}

const drugNames = computed(() => {
  const names = [...new Set(allMedications.value.map(m => m.name))]
  return names.sort((a, b) => a.localeCompare(b))
})

const filteredDrugs = computed(() => {
  const q = drugQuery.value.toLowerCase().trim()
  if (q.length < 2) return []
  return drugNames.value
    .filter(n => n.toLowerCase().includes(q))
    .slice(0, 50)
})

const dosageOptions = computed(() => {
  if (!selectedDrug.value) return []
  return allMedications.value.filter(m => m.name === selectedDrug.value)
})

function isDrugSpecialty(drugName) {
  return allMedications.value.some(m => m.name === drugName && m.is_specialty)
}

function extractDosageForm(dosageName, drugName) {
  if (!dosageName) return ''
  const prefix = drugName ? drugName.trim() + ' ' : ''
  if (prefix && dosageName.startsWith(prefix)) {
    return dosageName.slice(prefix.length).trim()
  }
  return dosageName
}

const hasSpecialty = computed(() =>
  store.medicationEntries.some(e => e.isSpecialty)
)

const canAdd = computed(() =>
  selectedMedId.value && quantity.value > 0
)

function onDrugInput() {
  if (selectedDrug.value && drugQuery.value !== selectedDrug.value) {
    selectedDrug.value = ''
    selectedMedId.value = ''
  }
  showDrugDropdown.value = true
}

function onDrugBlur() {
  setTimeout(() => { showDrugDropdown.value = false }, 150)
}

function selectDrug(drug) {
  selectedDrug.value = drug
  drugQuery.value    = drug
  selectedMedId.value = ''
  showDrugDropdown.value = false
  const opts = allMedications.value.filter(m => m.name === drug)
  if (opts.length === 1) selectedMedId.value = String(opts[0].id)
}

function clearDrug() {
  drugQuery.value     = ''
  selectedDrug.value  = ''
  selectedMedId.value = ''
}

function addEntry() {
  if (!canAdd.value) return
  const med = allMedications.value.find(m => m.id === parseInt(selectedMedId.value))
  if (!med) return

  store.addMedication({
    id:          med.id,
    drugName:    med.name,
    dosageName:  med.dosage,
    quantity:    quantity.value,
    frequency:   frequency.value,
    isSpecialty: med.is_specialty,
  })

  drugQuery.value     = ''
  selectedDrug.value  = ''
  selectedMedId.value = ''
  quantity.value      = 30
  frequency.value     = 'ONE'
}

onMounted(async () => {
  try {
    allMedications.value = await fetchMedications()
  } catch {
    loadError.value = true
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
.section-header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
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
.specialty-chip {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 10px;
  background: var(--moderate-dim);
  color: var(--moderate);
  border: 1px solid rgba(251,191,36,0.2);
}
.add-form {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 12px;
  margin-bottom: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.form-row { display: flex; flex-direction: column; gap: 5px; position: relative; }
.form-row-split { flex-direction: row; gap: 8px; }
.form-col { flex: 1; display: flex; flex-direction: column; gap: 5px; }
.form-label {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-muted);
}
.search-wrap { position: relative; display: flex; align-items: center; }
.search-icon {
  position: absolute;
  left: 9px;
  width: 12px; height: 12px;
  color: var(--text-muted);
  pointer-events: none;
}
.form-input {
  width: 100%;
  padding: 7px 26px 7px 28px;
  border: 1px solid var(--border-bright);
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-family: var(--font-ui);
  background: var(--bg-elevated);
  color: var(--text-primary);
  outline: none;
  transition: border-color 0.15s;
}
.form-input::placeholder { color: var(--text-muted); }
.form-input:focus { border-color: var(--teal); box-shadow: 0 0 0 2px var(--teal-dim); }
.qty-input { padding-left: 10px; text-align: center; }
.input-clear, .input-check {
  position: absolute;
  right: 8px;
  background: none;
  border: none;
  font-size: 14px;
  padding: 0;
  line-height: 1;
}
.input-clear { color: var(--text-muted); cursor: pointer; }
.input-clear:hover { color: var(--very-high); }
.input-check { color: var(--teal); cursor: default; }
.form-select {
  padding: 7px 10px;
  border: 1px solid var(--border-bright);
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-family: var(--font-ui);
  background: var(--bg-elevated);
  color: var(--text-primary);
  outline: none;
  cursor: pointer;
  transition: border-color 0.15s;
}
.form-select:focus { border-color: var(--teal); }
.form-select option { background: var(--bg-surface); }
.dropdown {
  position: absolute;
  top: calc(100% + 2px);
  left: 0; right: 0;
  background: var(--bg-surface);
  border: 1px solid var(--border-bright);
  border-radius: var(--radius-sm);
  max-height: 200px;
  overflow-y: auto;
  z-index: 50;
  box-shadow: 0 8px 24px rgba(0,0,0,0.5);
}
.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 7px 12px;
  background: none;
  border: none;
  cursor: pointer;
  text-align: left;
  transition: background 0.1s;
  font-family: var(--font-ui);
}
.dropdown-item:hover { background: var(--bg-hover); }
.dropdown-item.selected { background: var(--teal-dim); }
.di-name { font-size: 12px; color: var(--text-primary); flex: 1; }
.di-spec {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 8px;
  background: var(--moderate-dim);
  color: var(--moderate);
}
.dropdown-empty { padding: 10px 12px; font-size: 12px; color: var(--text-muted); font-family: var(--font-mono); }
.add-btn {
  padding: 8px;
  background: var(--teal-dim);
  border: 1px solid rgba(45,212,191,0.3);
  border-radius: var(--radius-sm);
  color: var(--teal);
  font-size: 12px;
  font-weight: 600;
  font-family: var(--font-ui);
  cursor: pointer;
  transition: all 0.15s;
  width: 100%;
}
.add-btn:hover:not(:disabled) { background: rgba(45,212,191,0.18); border-color: var(--teal); }
.add-btn:disabled { opacity: 0.35; cursor: not-allowed; }
.entries-list { display: flex; flex-direction: column; gap: 5px; }
.entries-label {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-muted);
  margin-bottom: 2px;
}
.entry-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-left: 3px solid var(--border-bright);
  border-radius: var(--radius-sm);
  transition: border-left-color 0.15s;
}
.entry-card:hover { border-left-color: var(--teal); }
.entry-specialty { border-left-color: rgba(251,191,36,0.5) !important; }
.entry-specialty:hover { border-left-color: var(--moderate) !important; }
.entry-main { flex: 1; min-width: 0; }
.entry-top { display: flex; align-items: center; gap: 6px; margin-bottom: 2px; }
.entry-drug { font-size: 12px; font-weight: 600; color: var(--text-primary); }
.entry-spec-badge {
  font-family: var(--font-mono);
  font-size: 9px;
  padding: 1px 5px;
  border-radius: 8px;
  background: var(--moderate-dim);
  color: var(--moderate);
}
.entry-dosage {
  font-size: 11px;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.entry-meta { display: flex; align-items: center; gap: 3px; flex-shrink: 0; }
.entry-qty { font-family: var(--font-mono); font-size: 12px; font-weight: 600; color: var(--text-primary); }
.entry-sep { font-size: 10px; color: var(--text-muted); }
.entry-freq { font-family: var(--font-mono); font-size: 10px; color: var(--text-secondary); }
.entry-remove {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 16px;
  cursor: pointer;
  padding: 0;
  line-height: 1;
  flex-shrink: 0;
}
.entry-remove:hover { color: var(--very-high); }
.hint { font-size: 11px; color: var(--text-muted); font-family: var(--font-mono); margin: 4px 0 0; }
.fade-down-enter-active { transition: all 0.18s ease; }
.fade-down-leave-active { transition: all 0.12s ease; }
.fade-down-enter-from   { opacity: 0; transform: translateY(-4px); }
.fade-down-leave-to     { opacity: 0; transform: translateY(-4px); }
</style>
