<template>
  <div class="section">
    <h3 class="section-title">Providers</h3>

    <div v-if="loading" class="loading">Loading…</div>
    <template v-else>
      <input
        v-model="search"
        class="search-input"
        placeholder="Search providers or specialties…"
        type="text"
      />

      <div class="selected-count" v-if="store.selectedProviderIds.length > 0">
        {{ store.selectedProviderIds.length }} selected
      </div>

      <!-- Group by specialty -->
      <div v-for="(group, specialty) in grouped" :key="specialty" class="specialty-group">
        <div class="specialty-header">
          <span class="specialty-name">{{ specialty }}</span>
          <span :class="['tier-badge', `tier-${groupTier(group)}`]">
            {{ tierLabel(groupTier(group)) }}
          </span>
        </div>
        <ul class="provider-list">
          <li v-for="provider in group" :key="provider.id" class="provider-item">
            <label class="provider-row">
              <input
                type="checkbox"
                class="checkbox"
                :checked="store.selectedProviderIds.includes(provider.id)"
                @change="store.toggleProvider(provider.id)"
              />
              <span class="provider-name">{{ provider.name }}</span>
            </label>
          </li>
        </ul>
      </div>

      <div v-if="Object.keys(grouped).length === 0" class="empty">
        No providers match your search.
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useBeneficiaryStore } from '../stores/beneficiary'
import { fetchProviders } from '../api/careEngine'

const store = useBeneficiaryStore()
const providers = ref([])
const loading = ref(true)
const search = ref('')

const filtered = computed(() => {
  const q = search.value.toLowerCase()
  if (!q) return providers.value
  return providers.value.filter(
    p => p.name.toLowerCase().includes(q) || p.specialty.toLowerCase().includes(q)
  )
})

const grouped = computed(() => {
  const result = {}
  for (const p of filtered.value) {
    if (!result[p.specialty]) result[p.specialty] = []
    result[p.specialty].push(p)
  }
  return result
})

function groupTier(group) {
  return group[0]?.specialty_tier || 'low'
}

function tierLabel(tier) {
  return { high: 'High', medium: 'Medium', low: 'Other', base: 'Primary Care' }[tier] || tier
}

onMounted(async () => {
  try {
    providers.value = await fetchProviders()
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
.selected-count { font-size: 12px; color: #1e40af; font-weight: 600; margin-bottom: 8px; }
.specialty-group { margin-bottom: 10px; }
.specialty-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.specialty-name { font-size: 13px; font-weight: 600; color: #374151; }
.provider-list { list-style: none; padding: 0 0 0 8px; margin: 0; }
.provider-item {}
.provider-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 4px;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.1s;
}
.provider-row:hover { background: #f9fafb; }
.checkbox { width: 14px; height: 14px; accent-color: #1e40af; cursor: pointer; }
.provider-name { font-size: 13px; color: #374151; }
.tier-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 10px;
  text-transform: uppercase;
}
.tier-high { background: #fee2e2; color: #991b1b; }
.tier-medium { background: #fef3c7; color: #92400e; }
.tier-low { background: #f3f4f6; color: #6b7280; }
.tier-base { background: #d1fae5; color: #065f46; }
.loading, .empty { font-size: 14px; color: #9ca3af; }
</style>
