<template>
  <div class="section">
    <div class="section-header">
      <span class="section-label">Providers</span>
      <span v-if="store.selectedProviderIds.length > 0" class="count-chip">
        {{ store.selectedProviderIds.length }}
      </span>
    </div>

    <!-- Typeahead input -->
    <div class="search-wrap">
      <svg class="search-icon" viewBox="0 0 16 16" fill="none">
        <circle cx="6.5" cy="6.5" r="4.5" stroke="currentColor" stroke-width="1.5"/>
        <path d="M10 10L14 14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
      <input
        v-model="query"
        ref="inputEl"
        class="search-input"
        placeholder="Search provider name…"
        type="text"
        autocomplete="off"
        @focus="showDropdown = true"
        @blur="onBlur"
      />
      <div v-if="loading" class="input-spinner"></div>
      <button v-else-if="query" class="search-clear" @mousedown.prevent @click="clearQuery">×</button>
    </div>

    <!-- Dropdown results -->
    <div v-if="showDropdown && (results.length > 0 || (query.length >= 2 && !loading))" class="dropdown">
      <div v-if="results.length === 0" class="dropdown-empty">
        No providers found for "{{ query }}"
      </div>
      <template v-else>
        <div
          v-for="group in grouped"
          :key="group.tier"
          class="result-group"
        >
          <div :class="['result-tier-header', `tier-${group.tier}`]">
            <span class="tier-bar-sm"></span>
            {{ group.label }}
          </div>
          <button
            v-for="p in group.providers"
            :key="p.id"
            :class="['result-item', { selected: isSelected(p.id) }]"
            @mousedown.prevent
            @click="toggleProvider(p)"
          >
            <span class="result-name">{{ p.name }}</span>
            <span class="result-specialty">{{ p.specialty }}</span>
            <span v-if="isSelected(p.id)" class="result-check">✓</span>
          </button>
        </div>
      </template>
    </div>

    <!-- Selected chips -->
    <div v-if="selectedProviders.length > 0" class="selected-chips">
      <div
        v-for="p in selectedProviders"
        :key="p.id"
        class="provider-chip"
      >
        <span :class="['chip-dot', `dot-${p.specialty_tier}`]"></span>
        <span class="chip-name">{{ p.name }}</span>
        <span class="chip-spec">{{ p.specialty || '—' }}</span>
        <button class="chip-remove" @click="store.toggleProvider(p.id)">×</button>
      </div>
    </div>

    <p v-if="selectedProviders.length === 0 && store.selectedProviderIds.length === 0" class="hint">
      Type 2+ characters to search 400K providers
    </p>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import { useBeneficiaryStore } from '../stores/beneficiary'
import { searchProviders } from '../api/careEngine'

const store = useBeneficiaryStore()
const query = ref('')
const results = ref([])
const loading = ref(false)
const showDropdown = ref(false)
const inputEl = ref(null)

// Map of id → provider object for selected providers
const providerCache = ref({})

const isSelected = id => store.selectedProviderIds.includes(id)

const selectedProviders = computed(() =>
  store.selectedProviderIds.map(id => providerCache.value[id]).filter(Boolean)
)

function toggleProvider(p) {
  providerCache.value[p.id] = p   // cache for chip display
  store.toggleProvider(p.id)
}

function clearQuery() {
  query.value = ''
  results.value = []
}

function onBlur() {
  // Delay so clicks inside dropdown register first
  setTimeout(() => { showDropdown.value = false }, 150)
}

// Group results by specialty tier for display
const TIER_ORDER = ['high', 'medium', 'low', 'base']
const TIER_LABELS = {
  high:   'High Complexity',
  medium: 'Moderate Complexity',
  low:    'Other Specialists',
  base:   'Primary Care',
}
const grouped = computed(() => {
  const byTier = {}
  for (const p of results.value) {
    const t = p.specialty_tier || 'low'
    if (!byTier[t]) byTier[t] = []
    byTier[t].push(p)
  }
  return TIER_ORDER
    .filter(t => byTier[t])
    .map(t => ({ tier: t, label: TIER_LABELS[t], providers: byTier[t] }))
})

// Debounced search
let debounceTimer = null
watch(query, val => {
  clearTimeout(debounceTimer)
  if (val.length < 2) {
    results.value = []
    loading.value = false
    return
  }
  showDropdown.value = true
  loading.value = true
  debounceTimer = setTimeout(async () => {
    try {
      results.value = await searchProviders(val)
    } catch {
      results.value = []
    } finally {
      loading.value = false
    }
  }, 300)
})

onUnmounted(() => clearTimeout(debounceTimer))
</script>

<style scoped>
.section {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px;
  margin-bottom: 8px;
}
.section-header { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
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

/* Search input */
.search-wrap {
  position: relative;
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}
.search-icon {
  position: absolute;
  left: 9px;
  width: 13px;
  height: 13px;
  color: var(--text-muted);
  pointer-events: none;
}
.search-input {
  width: 100%;
  padding: 8px 28px 8px 28px;
  border: 1px solid var(--border-bright);
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-family: var(--font-ui);
  background: var(--bg-surface);
  color: var(--text-primary);
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.search-input::placeholder { color: var(--text-muted); }
.search-input:focus {
  border-color: var(--teal);
  box-shadow: 0 0 0 2px var(--teal-dim);
}
.search-clear {
  position: absolute;
  right: 8px;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 16px;
  padding: 0;
  line-height: 1;
}
.search-clear:hover { color: var(--text-secondary); }
.input-spinner {
  position: absolute;
  right: 9px;
  width: 12px; height: 12px;
  border: 1.5px solid var(--border-bright);
  border-top-color: var(--teal);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Dropdown */
.dropdown {
  background: var(--bg-surface);
  border: 1px solid var(--border-bright);
  border-radius: var(--radius-sm);
  max-height: 280px;
  overflow-y: auto;
  margin-bottom: 8px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.4);
}
.dropdown-empty {
  padding: 12px 14px;
  font-size: 12px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.result-group { }
.result-tier-header {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 6px 10px 4px;
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  background: var(--bg-elevated);
  position: sticky;
  top: 0;
}
.tier-bar-sm {
  display: inline-block;
  width: 3px;
  height: 10px;
  border-radius: 2px;
  flex-shrink: 0;
}
.result-tier-header.tier-high   { color: var(--very-high); }
.result-tier-header.tier-high .tier-bar-sm   { background: var(--very-high); }
.result-tier-header.tier-medium { color: var(--moderate); }
.result-tier-header.tier-medium .tier-bar-sm { background: var(--moderate); }
.result-tier-header.tier-low    { color: var(--text-muted); }
.result-tier-header.tier-low .tier-bar-sm    { background: var(--border-bright); }
.result-tier-header.tier-base   { color: var(--low); }
.result-tier-header.tier-base .tier-bar-sm   { background: var(--low); }

.result-item {
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
.result-item:hover { background: var(--bg-hover); }
.result-item.selected { background: var(--teal-dim); }

.result-name { font-size: 12px; color: var(--text-primary); flex: 1; }
.result-specialty {
  font-size: 10px;
  color: var(--text-muted);
  font-family: var(--font-mono);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 120px;
}
.result-check { font-size: 12px; color: var(--teal); flex-shrink: 0; }

/* Selected chips */
.selected-chips {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 8px;
}
.provider-chip {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 6px 10px;
  background: var(--bg-surface);
  border: 1px solid var(--border-bright);
  border-radius: var(--radius-sm);
}
.chip-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot-high   { background: var(--very-high); box-shadow: 0 0 4px rgba(248,113,113,0.5); }
.dot-medium { background: var(--moderate);  box-shadow: 0 0 4px rgba(251,191,36,0.4);  }
.dot-low    { background: var(--border-bright); }
.dot-base   { background: var(--low); box-shadow: 0 0 4px rgba(52,211,153,0.4); }

.chip-name { font-size: 12px; color: var(--text-primary); flex: 1; }
.chip-spec {
  font-size: 10px;
  color: var(--text-muted);
  font-family: var(--font-mono);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 110px;
}
.chip-remove {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 14px;
  padding: 0;
  line-height: 1;
  flex-shrink: 0;
}
.chip-remove:hover { color: var(--very-high); }

.hint {
  font-size: 11px;
  color: var(--text-muted);
  font-family: var(--font-mono);
  margin: 6px 0 0;
}
</style>
