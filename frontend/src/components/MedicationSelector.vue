<template>
  <div class="section">
    <h3 class="section-title">Medications</h3>

    <div v-if="loading" class="loading">Loading…</div>
    <template v-else>
      <input
        v-model="search"
        class="search-input"
        placeholder="Search medications or categories…"
        type="text"
      />

      <div class="selected-count" v-if="store.selectedMedicationIds.length > 0">
        {{ store.selectedMedicationIds.length }} selected
        <span v-if="hasSpecialtySelected" class="specialty-flag">⚠ includes specialty drugs</span>
      </div>

      <div v-for="(group, category) in grouped" :key="category" class="category-group">
        <div class="category-header">{{ category }}</div>
        <ul class="med-list">
          <li v-for="med in group" :key="med.id" class="med-item">
            <label class="med-row">
              <input
                type="checkbox"
                class="checkbox"
                :checked="store.selectedMedicationIds.includes(med.id)"
                @change="store.toggleMedication(med.id)"
              />
              <span class="med-name">{{ med.name }}</span>
              <span class="med-dosage">{{ med.dosage }}</span>
              <span v-if="med.is_specialty" class="specialty-badge">Specialty</span>
            </label>
          </li>
        </ul>
      </div>

      <div v-if="Object.keys(grouped).length === 0" class="empty">
        No medications match your search.
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useBeneficiaryStore } from '../stores/beneficiary'
import { fetchMedications } from '../api/careEngine'

const store = useBeneficiaryStore()
const medications = ref([])
const loading = ref(true)
const search = ref('')

const filtered = computed(() => {
  const q = search.value.toLowerCase()
  if (!q) return medications.value
  return medications.value.filter(
    m => m.name.toLowerCase().includes(q) || m.category.toLowerCase().includes(q)
  )
})

const grouped = computed(() => {
  const result = {}
  for (const m of filtered.value) {
    const cat = m.category || 'Other'
    if (!result[cat]) result[cat] = []
    result[cat].push(m)
  }
  return result
})

const hasSpecialtySelected = computed(() => {
  const selectedIds = new Set(store.selectedMedicationIds)
  return medications.value.some(m => selectedIds.has(m.id) && m.is_specialty)
})

onMounted(async () => {
  try {
    medications.value = await fetchMedications()
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
.search-input {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  margin-bottom: 10px;
  box-sizing: border-box;
}
.selected-count { font-size: 12px; color: #1e40af; font-weight: 600; margin-bottom: 8px; display: flex; gap: 8px; align-items: center; }
.specialty-flag { color: #b45309; font-weight: 500; }
.category-group { margin-bottom: 10px; }
.category-header { font-size: 12px; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 4px; }
.med-list { list-style: none; padding: 0 0 0 4px; margin: 0; }
.med-item {}
.med-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 4px;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.1s;
}
.med-row:hover { background: #f9fafb; }
.checkbox { width: 14px; height: 14px; accent-color: #1e40af; cursor: pointer; flex-shrink: 0; }
.med-name { font-size: 13px; color: #374151; flex: 1; }
.med-dosage { font-size: 12px; color: #9ca3af; }
.specialty-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 5px;
  border-radius: 4px;
  background: #fef3c7;
  color: #92400e;
}
.loading, .empty { font-size: 14px; color: #9ca3af; }
</style>
