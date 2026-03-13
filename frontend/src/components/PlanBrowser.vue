<template>
  <div class="plan-browser" ref="browserEl">

    <!-- ── Plan browser header (always at top) ────────────────────── -->
    <div class="browser-header">
      <div class="browser-title-row">
        <span class="section-label">Plans</span>
        <span v-if="store.zip && store.zip.length === 5" class="zip-badge">{{ store.zip }}</span>
        <span v-if="filteredPlans.length" class="count-badge">{{ filteredPlans.length }}</span>
      </div>

      <!-- Search -->
      <div class="search-row">
        <div class="search-wrap">
          <input
            v-model="query"
            class="search-input"
            type="text"
            placeholder="Search plans…"
            @input="onSearchInput"
          />
          <span v-if="loading" class="search-spinner"></span>
        </div>

        <!-- Filters toggle -->
        <button
          :class="['filter-btn', { active: hasActiveFilters }]"
          @click="showFilters = !showFilters"
          title="Toggle filters"
        >
          ⊟ Filters
          <span v-if="activeFilterCount" class="filter-count">{{ activeFilterCount }}</span>
        </button>
      </div>

      <!-- Filter bar -->
      <div v-if="showFilters" class="filter-bar">

        <!-- Min star rating -->
        <div class="filter-group">
          <span class="filter-label">Stars</span>
          <div class="chip-row">
            <button
              v-for="opt in starOptions"
              :key="opt.value"
              :class="['chip', { active: minStars === opt.value }]"
              @click="minStars = minStars === opt.value ? null : opt.value"
            >{{ opt.label }}</button>
          </div>
        </div>

        <!-- Plan type -->
        <div class="filter-group">
          <span class="filter-label">Type</span>
          <div class="chip-row">
            <button
              v-for="pt in planTypeOptions"
              :key="pt"
              :class="['chip', { active: selectedTypes.has(pt) }]"
              @click="toggleType(pt)"
            >{{ pt }}</button>
          </div>
        </div>

        <!-- SNP type -->
        <div class="filter-group">
          <span class="filter-label">SNP</span>
          <div class="chip-row">
            <button
              v-for="snp in snpOptions"
              :key="snp"
              :class="['chip', { active: selectedSnps.has(snp) }]"
              @click="toggleSnp(snp)"
            >{{ snp }}</button>
          </div>
        </div>

        <!-- Carrier -->
        <div class="filter-group carrier-group">
          <span class="filter-label">Carrier</span>
          <div class="carrier-select-wrap">
            <select v-model="selectedCarrier" class="carrier-select">
              <option value="">All carriers</option>
              <option v-for="c in availableCarriers" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>
        </div>

        <!-- Clear -->
        <button v-if="hasActiveFilters" class="clear-filters-btn" @click="clearFilters">
          Clear all
        </button>
      </div>
    </div>

    <!-- Plan list -->
    <div class="plan-list">

      <!-- No ZIP state -->
      <div v-if="!store.zip || store.zip.length < 5" class="empty-state">
        <div class="empty-icon">◎</div>
        <p class="empty-text">Enter a ZIP code in the beneficiary panel to load plans for that market.</p>
      </div>

      <!-- Loading -->
      <div v-else-if="loading && !allPlans.length" class="empty-state">
        <div class="spinner"></div>
        <span class="empty-text">Loading plans…</span>
      </div>

      <!-- No results -->
      <div v-else-if="!loading && allPlans.length === 0" class="empty-state">
        <p class="empty-text">No plans found for ZIP {{ store.zip }}.</p>
      </div>

      <!-- No filtered results -->
      <div v-else-if="!loading && filteredPlans.length === 0" class="empty-state">
        <p class="empty-text">No plans match your filters.</p>
      </div>

      <!-- Plan cards -->
      <div
        v-for="plan in filteredPlans"
        :key="`${plan.contract_id}-${plan.plan_id}-${plan.segment_id}`"
        :class="['plan-card', { selected: isSelected(plan) }]"
      >
        <!-- Card header -->
        <div class="card-top">
          <div class="card-name-row">
            <span class="card-name">{{ plan.plan_name }}</span>
            <span v-if="plan.overall_star_rating" class="card-stars">★ {{ plan.overall_star_rating }}</span>
          </div>
          <div class="card-meta-row">
            <span class="plan-type-chip">{{ plan.plan_type_label }}</span>
            <span
              v-if="plan.snp_type"
              :class="['snp-badge', snpClass(plan.snp_type)]"
            >
              {{ plan.snp_type }}<template v-if="plan.csnp_condition"> · {{ plan.csnp_condition }}</template>
            </span>
            <span v-if="plan.snp_type === 'D-SNP' && store.medicaidDual" class="dsnp-match">✓ Dual</span>
            <span class="card-org">{{ plan.parent_org }}</span>
          </div>
        </div>

        <!-- Cost grid -->
        <div class="cost-grid">
          <div class="cost-cell">
            <span class="cost-label">Premium</span>
            <span class="cost-value">{{ formatDollar(plan.monthly_premium) }}<span class="cost-unit">/mo</span></span>
          </div>
          <div class="cost-cell">
            <span class="cost-label">PCP Copay</span>
            <span class="cost-value">{{ formatDollar(plan.pcp_copay_max) }}</span>
          </div>
          <div class="cost-cell">
            <span class="cost-label">Specialist</span>
            <span class="cost-value">{{ formatCopayRange(plan.specialist_copay_min, plan.specialist_copay_max) }}</span>
          </div>
          <div class="cost-cell">
            <span class="cost-label">Med Deductible</span>
            <span class="cost-value">{{ formatDollar(plan.health_deductible) }}</span>
          </div>
          <div class="cost-cell">
            <span class="cost-label">Rx Deductible</span>
            <span class="cost-value">{{ formatDollar(plan.drug_deductible) }}</span>
          </div>
          <div class="cost-cell">
            <span class="cost-label">MOOP</span>
            <span class="cost-value">{{ formatDollar(plan.moop_in_network) }}</span>
          </div>
        </div>

        <!-- Action row -->
        <div class="card-action-row">
          <button
            v-if="!isSelected(plan)"
            class="select-btn"
            @click="store.selectPlan(plan)"
          >
            Select for Reasoning
          </button>
          <div v-else class="selected-row">
            <span class="selected-label">✓ Selected for Reasoning</span>
            <button class="deselect-btn" @click="store.clearPlan()">Remove</button>
          </div>
        </div>

        <!-- Inline reasoning (expands when this plan is selected) -->
        <div v-if="isSelected(plan)" class="inline-reasoning">
          <div class="reasoning-header">
            <span class="section-label">Plan Reasoning</span>
            <span v-if="talkingPoints.length" class="point-count">{{ talkingPoints.length }}</span>
            <div v-if="store.reasoningLoading && talkingPoints.length" class="reasoning-recalc">
              <div class="reasoning-spinner"></div>
              <span class="loading-text">Updating…</span>
            </div>
          </div>

          <!-- First load: no existing points yet -->
          <div v-if="store.reasoningLoading && !talkingPoints.length" class="loading-row">
            <div class="reasoning-spinner"></div>
            <span class="loading-text">Generating reasoning…</span>
          </div>

          <div v-else-if="!narrativeAvailable" class="no-api">
            Add <code>OPENAI_API_KEY</code> to <code>backend/.env</code> to enable reasoning.
          </div>

          <div
            v-else-if="talkingPoints.length"
            class="points-list"
            :class="{ 'points-stale': store.reasoningLoading }"
          >
            <div v-for="(point, i) in talkingPoints" :key="i" class="point-card">
              <div class="point-attribute">{{ point.attribute }}</div>
              <div class="point-text">{{ point.text }}</div>
            </div>
          </div>

          <div v-else-if="!store.reasoningLoading" class="loading-row">
            <div class="reasoning-spinner"></div>
            <span class="loading-text">Waiting for beneficiary data…</span>
          </div>

          <div class="disclaimer">
            <span class="disclaimer-icon">ⓘ</span>
            Based on plan benefit attributes only. Drug formulary coverage and provider network participation are not assessed — verify separately before recommending.
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useBeneficiaryStore } from '../stores/beneficiary'
import { searchPlans } from '../api/careEngine'

const store = useBeneficiaryStore()
const browserEl = ref(null)

// ── Reasoning (inline, from separate store state) ───────────────────────────
const talkingPoints      = computed(() => store.talkingPoints)
const narrativeAvailable = computed(() => store.narrativeAvailable)

// ── State ───────────────────────────────────────────────────────────────────
const query       = ref('')
const allPlans    = ref([])
const loading     = ref(false)
const showFilters = ref(false)

// Filters
const minStars       = ref(null)
const selectedTypes  = ref(new Set())
const selectedSnps   = ref(new Set())
const selectedCarrier = ref('')

// ── Filter options ──────────────────────────────────────────────────────────
const starOptions = [
  { value: 5,   label: '5 ★' },
  { value: 4,   label: '4+ ★' },
  { value: 3,   label: '3+ ★' },
]
const planTypeOptions = ['HMO', 'PPO', 'HMO-POS']
const snpOptions      = ['C-SNP', 'D-SNP']

const availableCarriers = computed(() => {
  const orgs = [...new Set(allPlans.value.map(p => p.parent_org).filter(Boolean))]
  return orgs.sort()
})

// ── Active filter state ─────────────────────────────────────────────────────
const activeFilterCount = computed(() => {
  let n = 0
  if (minStars.value != null)      n++
  if (selectedTypes.value.size)    n++
  if (selectedSnps.value.size)     n++
  if (selectedCarrier.value)       n++
  return n
})
const hasActiveFilters = computed(() => activeFilterCount.value > 0)

// ── Filtered plan list ──────────────────────────────────────────────────────
const filteredPlans = computed(() => {
  let plans = allPlans.value

  if (minStars.value != null) {
    plans = plans.filter(p => p.overall_star_rating != null && p.overall_star_rating >= minStars.value)
  }
  if (selectedTypes.value.size) {
    plans = plans.filter(p => selectedTypes.value.has(p.plan_type_label))
  }
  if (selectedSnps.value.size) {
    plans = plans.filter(p => selectedSnps.value.has(p.snp_type))
  }
  if (selectedCarrier.value) {
    plans = plans.filter(p => p.parent_org === selectedCarrier.value)
  }

  return plans
})

// ── Load plans ──────────────────────────────────────────────────────────────
let debounce = null

async function loadPlans(q = '') {
  if (!store.zip || store.zip.length !== 5) {
    allPlans.value = []
    return
  }
  loading.value = true
  try {
    allPlans.value = await searchPlans(q, store.zip)
  } catch {
    allPlans.value = []
  } finally {
    loading.value = false
  }
}

// Auto-load when ZIP changes
watch(() => store.zip, (zip) => {
  if (zip && zip.length === 5) {
    loadPlans(query.value)
  } else {
    allPlans.value = []
  }
}, { immediate: true })

// Scroll selected card into view when a plan is selected
watch(() => store.selectedPlan, (plan) => {
  if (plan && browserEl.value) {
    setTimeout(() => {
      const selected = browserEl.value.querySelector('.plan-card.selected')
      if (selected) selected.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }, 50)
  }
})

// Search input debounce
function onSearchInput() {
  clearTimeout(debounce)
  debounce = setTimeout(() => {
    loadPlans(query.value)
  }, 300)
}

// ── Filter helpers ──────────────────────────────────────────────────────────
function toggleType(pt) {
  const s = new Set(selectedTypes.value)
  s.has(pt) ? s.delete(pt) : s.add(pt)
  selectedTypes.value = s
}

function toggleSnp(snp) {
  const s = new Set(selectedSnps.value)
  s.has(snp) ? s.delete(snp) : s.add(snp)
  selectedSnps.value = s
}

function clearFilters() {
  minStars.value = null
  selectedTypes.value = new Set()
  selectedSnps.value = new Set()
  selectedCarrier.value = ''
}

// ── Selection ───────────────────────────────────────────────────────────────
function isSelected(plan) {
  const sp = store.selectedPlan
  return sp &&
    sp.contract_id === plan.contract_id &&
    sp.plan_id     === plan.plan_id &&
    sp.segment_id  === plan.segment_id
}

// ── Formatters ──────────────────────────────────────────────────────────────
function formatDollar(val) {
  if (val == null) return '—'
  return '$' + Number(val).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

function formatCopayRange(min, max) {
  if (min == null && max == null) return '—'
  if (min == null) return formatDollar(max)
  if (max == null || min === max) return formatDollar(min)
  return `${formatDollar(min)}–${formatDollar(max)}`
}

function snpClass(snpType) {
  if (!snpType) return ''
  const t = snpType.toUpperCase()
  if (t.startsWith('C')) return 'csnp'
  if (t.startsWith('D')) return 'dsnp'
  if (t.startsWith('I')) return 'isnp'
  return ''
}
</script>

<style scoped>
.plan-browser {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

/* ── Inline reasoning (expands inside card) ─────────────────────────── */
.inline-reasoning {
  border-top: 1px solid rgba(13,148,136,0.2);
  margin-top: 10px;
  padding-top: 12px;
}

.reasoning-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.reasoning-recalc {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-left: auto;
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

.loading-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
}

.reasoning-spinner {
  width: 12px; height: 12px;
  border: 1.5px solid var(--border-bright);
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

.points-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 10px;
  transition: opacity 0.2s ease;
}
.points-stale {
  opacity: 0.4;
  pointer-events: none;
}

.point-card {
  padding: 10px 12px;
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
  margin-bottom: 5px;
}

.point-text {
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-primary);
}

.disclaimer {
  margin-top: 8px;
  padding: 7px 10px;
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

/* ── Browser header ─────────────────────────────────────────────────── */
.browser-header {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px;
  margin-bottom: 8px;
  flex-shrink: 0;
}

.browser-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.section-label {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  color: var(--text-muted);
}

.zip-badge {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 8px;
  background: var(--teal-dim);
  color: var(--teal);
  border: 1px solid rgba(13,148,136,0.2);
  letter-spacing: 0.06em;
}

.count-badge {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 10px;
  background: var(--bg-base);
  color: var(--text-secondary);
  border: 1px solid var(--border-bright);
}

/* ── Search row ─────────────────────────────────────────────────────── */
.search-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.search-wrap {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
}

.search-input {
  width: 100%;
  padding: 8px 28px 8px 10px;
  border: 1px solid var(--border-bright);
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-family: var(--font-ui);
  background: var(--bg-surface);
  color: var(--text-primary);
  outline: none;
  transition: border-color 0.15s;
}
.search-input:focus { border-color: var(--teal); box-shadow: 0 0 0 2px var(--teal-dim); }
.search-input::placeholder { color: var(--text-muted); }

.search-spinner {
  position: absolute;
  right: 9px;
  width: 12px; height: 12px;
  border: 1.5px solid var(--border-bright);
  border-top-color: var(--teal);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.filter-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 7px 11px;
  border: 1px solid var(--border-bright);
  border-radius: var(--radius-sm);
  background: var(--bg-surface);
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s;
  flex-shrink: 0;
}
.filter-btn:hover { border-color: var(--teal); color: var(--teal); }
.filter-btn.active { border-color: var(--teal); background: var(--teal-dim); color: var(--teal); }

.filter-count {
  background: var(--teal);
  color: #fff;
  border-radius: 8px;
  font-size: 8px;
  padding: 1px 5px;
  font-weight: 700;
}

/* ── Filter bar ─────────────────────────────────────────────────────── */
.filter-bar {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.filter-label {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-muted);
  width: 52px;
  flex-shrink: 0;
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.chip {
  padding: 3px 9px;
  border: 1px solid var(--border-bright);
  border-radius: 10px;
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 600;
  background: var(--bg-base);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.12s;
  letter-spacing: 0.04em;
}
.chip:hover { border-color: var(--teal); color: var(--teal); }
.chip.active { background: var(--teal-dim); border-color: rgba(13,148,136,0.4); color: var(--teal); }

.carrier-group { align-items: center; }

.carrier-select-wrap { flex: 1; }

.carrier-select {
  width: 100%;
  max-width: 240px;
  padding: 5px 8px;
  border: 1px solid var(--border-bright);
  border-radius: var(--radius-sm);
  font-family: var(--font-ui);
  font-size: 12px;
  background: var(--bg-surface);
  color: var(--text-primary);
  outline: none;
  cursor: pointer;
}
.carrier-select:focus { border-color: var(--teal); }

.clear-filters-btn {
  align-self: flex-start;
  padding: 3px 10px;
  border: 1px solid var(--border-bright);
  border-radius: 10px;
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 600;
  background: none;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.12s;
  letter-spacing: 0.06em;
}
.clear-filters-btn:hover { color: var(--very-high); border-color: rgba(220,38,38,0.3); }

/* ── Plan list ──────────────────────────────────────────────────────── */
.plan-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-bottom: 8px;
}

/* ── Empty states ───────────────────────────────────────────────────── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px 20px;
  text-align: center;
}
.empty-icon { font-size: 28px; color: var(--border-bright); line-height: 1; }
.empty-text {
  font-size: 12px;
  color: var(--text-muted);
  max-width: 240px;
  line-height: 1.6;
  margin: 0;
}
.spinner {
  width: 20px; height: 20px;
  border: 2px solid var(--border-bright);
  border-top-color: var(--teal);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

/* ── Plan card ──────────────────────────────────────────────────────── */
.plan-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.plan-card:hover { border-color: var(--border-bright); box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.plan-card.selected {
  border-color: rgba(13,148,136,0.4);
  background: rgba(13,148,136,0.04);
  box-shadow: 0 0 0 2px var(--teal-dim);
}

/* Card header */
.card-top { margin-bottom: 10px; }

.card-name-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 6px;
  margin-bottom: 5px;
}

.card-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  line-height: 1.3;
  flex: 1;
  min-width: 0;
}

.card-stars {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--accent);
  flex-shrink: 0;
}

.card-meta-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
}

.card-org {
  font-size: 11px;
  color: var(--text-muted);
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Plan type chip */
.plan-type-chip {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--bg-base);
  color: var(--text-secondary);
  border: 1px solid var(--border-bright);
  flex-shrink: 0;
  letter-spacing: 0.05em;
}

/* SNP badges */
.snp-badge {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 10px;
  flex-shrink: 0;
  letter-spacing: 0.04em;
}
.snp-badge.csnp { background: rgba(234,88,12,0.08); color: var(--high); border: 1px solid rgba(234,88,12,0.2); }
.snp-badge.dsnp { background: var(--teal-dim); color: var(--teal); border: 1px solid rgba(13,148,136,0.2); }
.snp-badge.isnp { background: var(--low-dim); color: var(--low); border: 1px solid rgba(5,150,105,0.2); }

.dsnp-match {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 600;
  color: var(--teal);
  flex-shrink: 0;
}

/* Cost grid */
.cost-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
  margin-bottom: 10px;
  padding: 10px;
  background: var(--bg-base);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}

.cost-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.cost-label {
  font-family: var(--font-mono);
  font-size: 8px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted);
  line-height: 1;
}

.cost-value {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.2;
}

.cost-unit {
  font-size: 9px;
  font-weight: 400;
  color: var(--text-muted);
}

/* Action row */
.card-action-row { display: flex; }

.select-btn {
  width: 100%;
  padding: 8px 12px;
  background: var(--bg-surface);
  border: 1px solid var(--border-bright);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  letter-spacing: 0.06em;
  transition: all 0.15s;
}
.select-btn:hover {
  background: var(--teal-dim);
  border-color: rgba(13,148,136,0.4);
  color: var(--teal);
}

.selected-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 6px 8px;
  background: var(--teal-dim);
  border: 1px solid rgba(13,148,136,0.3);
  border-radius: var(--radius-sm);
}

.selected-label {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  color: var(--teal);
  letter-spacing: 0.06em;
}

.deselect-btn {
  background: none;
  border: none;
  font-family: var(--font-mono);
  font-size: 9px;
  color: var(--text-muted);
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 3px;
  transition: color 0.12s;
}
.deselect-btn:hover { color: var(--text-primary); }
</style>
