<template>
  <div class="score-card">

    <!-- Loading (first load only — no prior result) -->
    <div v-if="store.isLoading && !result" class="state-center">
      <div class="spinner"></div>
      <span class="state-label">Calculating…</span>
    </div>

    <!-- Empty -->
    <div v-else-if="!result" class="state-center empty-state">
      <div class="empty-icon">◎</div>
      <p class="empty-text">Select conditions, providers, or medications to generate a score.</p>
    </div>

    <!-- Result (shown even while recalculating) -->
    <template v-else>

      <!-- Card header -->
      <div class="card-header">
        <span class="card-label">Care Intensity Score</span>
        <div v-if="store.isLoading" class="recalc-row">
          <div class="micro-spinner"></div>
          <span class="recalc-label">Updating…</span>
        </div>
      </div>

      <!-- Intensity band — 4 segments, active one lit -->
      <div class="intensity-band">
        <div
          v-for="band in BANDS"
          :key="band.key"
          :class="['band-seg', { active: band.key === intensityKey }]"
          :style="band.key === intensityKey
            ? { background: band.color, color: '#fff', borderColor: band.color }
            : {}"
        >
          <span class="band-label">{{ band.label }}</span>
          <span class="band-range">{{ band.range }}</span>
        </div>
      </div>

      <!-- Interactions -->
      <div v-if="result.interactions_triggered?.length > 0" class="interactions">
        <span
          v-for="pair in result.interactions_triggered"
          :key="pair"
          class="interaction-tag"
        >⚡ {{ pair }}</span>
      </div>

      <!-- Inputs considered -->
      <div class="subsection">
        <div class="subsection-label">What was considered</div>
        <div class="inputs-list">
          <div v-for="input in inputRows" :key="input.key" class="input-row">
            <span :class="['input-dot', { filled: input.filled }]"></span>
            <span class="input-name">{{ input.name }}</span>
            <span :class="['input-detail', { empty: !input.filled }]">{{ input.detail }}</span>
          </div>
        </div>
      </div>

      <!-- Score reasoning -->
      <div v-if="reasoning" class="subsection">
        <div class="subsection-label">Why this score</div>
        <p class="reasoning-text">{{ reasoning }}</p>
      </div>

      <!-- Flags -->
      <div v-if="result.flags?.demographic_data_missing" class="flag-row">
        <span class="flag-icon">▲</span>
        Age/sex unknown — demographic data incomplete
      </div>
      <div v-if="result.flags?.medication_data_missing" class="flag-row">
        <span class="flag-icon">▲</span>
        No medications entered — medication complexity not assessed
      </div>

    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useBeneficiaryStore } from '../stores/beneficiary'

const store = useBeneficiaryStore()
const result = computed(() => store.scoreResult)

// ── Intensity bands ────────────────────────────────────────────────────────
const BANDS = [
  { key: 'low',       label: 'Low',       range: '0–24',   color: '#059669' },
  { key: 'moderate',  label: 'Moderate',  range: '25–49',  color: '#d97706' },
  { key: 'high',      label: 'High',      range: '50–74',  color: '#ea580c' },
  { key: 'very-high', label: 'Very High', range: '75–100', color: '#dc2626' },
]

const intensityKey = computed(() => {
  if (!result.value) return ''
  return result.value.intensity_level.toLowerCase().replace(' ', '-')
})

// ── Age band display labels ────────────────────────────────────────────────
const AGE_LABELS = {
  'under_65': 'Under 65',
  '65_70':    '65–70',
  '70_75':    '70–75',
  '75_80':    '75–80',
  '80_plus':  '80+',
  'unknown':  null,
}

const SEX_LABELS = {
  'female':  'Female',
  'male':    'Male',
  'unknown': null,
}

// ── Inputs considered rows ─────────────────────────────────────────────────
const inputRows = computed(() => {
  if (!result.value) return []
  const r = result.value
  const c = r.completeness || {}
  const flags = r.flags || {}

  // Conditions
  const condDetail = r.condition_names?.length
    ? r.condition_names.join(', ')
    : 'Not entered'

  // Providers — specialty_tiers now includes all entered specialties (scored + base tier)
  let provDetail = 'Not entered'
  if (c.providers) {
    provDetail = r.specialty_tiers?.length
      ? r.specialty_tiers.map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(', ')
      : 'Provider entered'
  }

  // Medications
  let medDetail = 'Not entered'
  if (c.medications) {
    medDetail = r.med_count > 0
      ? `${r.med_count} medication${r.med_count > 1 ? 's' : ''}${r.has_specialty_drug ? ' (incl. specialty)' : ''}`
      : 'None recorded'
  }

  // Demographics
  const agePart  = AGE_LABELS[r.age_band] || null
  const sexPart  = SEX_LABELS[r.sex]      || null
  let demoDetail = 'Not entered'
  if (agePart || sexPart) {
    demoDetail = [sexPart, agePart ? `age ${agePart}` : null].filter(Boolean).join(', ')
  }
  if (r.medicaid_dual) demoDetail += ' · Medicaid dual'

  return [
    { key: 'conditions',   name: 'Conditions',   filled: c.conditions,   detail: condDetail },
    { key: 'providers',    name: 'Providers',     filled: c.providers,    detail: provDetail },
    { key: 'medications',  name: 'Medications',   filled: c.medications,  detail: medDetail  },
    { key: 'demographics', name: 'Demographics',  filled: c.demographics, detail: demoDetail },
  ]
})

// ── Rule-based score reasoning ─────────────────────────────────────────────
const reasoning = computed(() => {
  if (!result.value) return ''
  const r          = result.value
  const conditions = r.condition_names   || []
  const specialties= r.specialty_tiers  || []
  const medCount   = r.med_count        || 0
  const hasSpecial = r.has_specialty_drug|| false
  const interact   = r.interactions_triggered || []
  const flags      = r.flags            || {}
  const c          = r.completeness     || {}

  const parts = []

  // Conditions
  if (conditions.length === 1) {
    parts.push(`${conditions[0]} is the primary driver of this assessment.`)
  } else if (conditions.length > 1) {
    parts.push(`${conditions.join(', ')} are all factored into this assessment.`)
  }

  // Interactions
  if (interact.length > 0) {
    const label = interact.length === 1 ? 'A comorbidity interaction' : 'Comorbidity interactions'
    parts.push(`${label} was identified: ${interact.join('; ')}.`)
  }

  // Providers
  if (specialties.length > 0) {
    const spec = specialties.map(s => s.charAt(0).toUpperCase() + s.slice(1))
    parts.push(`${spec.join(', ')} specialist involvement adds care coordination complexity.`)
  }

  // Medications
  if (c.medications && medCount > 0) {
    const specNote = hasSpecial ? ' including specialty drugs' : ''
    parts.push(`${medCount} medication${medCount > 1 ? 's' : ''}${specNote} contribute to medication burden.`)
  }

  // What's missing
  const missing = []
  if (!c.conditions)   missing.push('conditions')
  if (!c.providers)    missing.push('providers')
  if (flags.medication_data_missing) missing.push('medications')
  if (!c.demographics) missing.push('demographics')

  if (missing.length > 0 && conditions.length > 0) {
    parts.push(`Adding ${missing.join(' and ')} data may shift this assessment.`)
  }

  return parts.join(' ')
})
</script>

<style scoped>
.score-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  margin-bottom: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  min-height: 340px;
}

/* Header */
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.card-label {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  color: var(--text-muted);
}
.recalc-row {
  display: flex;
  align-items: center;
  gap: 6px;
}
.micro-spinner {
  width: 10px; height: 10px;
  border: 1.5px solid var(--border-bright);
  border-top-color: var(--teal);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}
.recalc-label {
  font-family: var(--font-mono);
  font-size: 9px;
  color: var(--text-muted);
  letter-spacing: 0.06em;
}

/* Empty / loading */
.state-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 32px 16px;
}
.state-label { font-size: 12px; color: var(--text-muted); font-family: var(--font-mono); }
.spinner {
  width: 20px; height: 20px;
  border: 2px solid var(--border-bright);
  border-top-color: var(--teal);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.empty-icon { font-size: 28px; color: var(--border-bright); line-height: 1; }
.empty-text {
  font-size: 12px;
  color: var(--text-muted);
  text-align: center;
  max-width: 210px;
  line-height: 1.6;
  margin: 0;
}

/* ── Intensity band ─────────────────────────────────────────────────── */
.intensity-band {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 4px;
  margin-bottom: 14px;
}
.band-seg {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 8px 4px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: var(--bg-base);
  transition: all 0.2s;
}
.band-seg.active {
  box-shadow: 0 2px 8px rgba(0,0,0,0.12);
}
.band-label {
  font-family: var(--font-display);
  font-size: 13px;
  letter-spacing: 0.06em;
  line-height: 1;
}
.band-seg:not(.active) .band-label { color: var(--text-muted); }
.band-range {
  font-family: var(--font-mono);
  font-size: 8px;
  letter-spacing: 0.04em;
}
.band-seg:not(.active) .band-range { color: var(--border-bright); }
.band-seg.active .band-range { color: rgba(255,255,255,0.75); }

/* ── Interactions ───────────────────────────────────────────────────── */
.interactions {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-bottom: 14px;
}
.interaction-tag {
  font-family: var(--font-mono);
  font-size: 10px;
  padding: 3px 9px;
  background: var(--high-dim);
  color: var(--high);
  border: 1px solid rgba(234,88,12,0.2);
  border-radius: 10px;
}

/* ── Subsections ────────────────────────────────────────────────────── */
.subsection {
  margin-bottom: 14px;
}
.subsection-label {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--text-muted);
  margin-bottom: 8px;
  padding-bottom: 5px;
  border-bottom: 1px solid var(--border);
}

/* ── Inputs list ────────────────────────────────────────────────────── */
.inputs-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.input-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
}
.input-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--border-bright);
  position: relative;
  top: 1px;
}
.input-dot.filled { background: var(--teal); }

.input-name {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--text-secondary);
  width: 88px;
  flex-shrink: 0;
}
.input-detail {
  font-size: 12px;
  color: var(--text-primary);
  line-height: 1.4;
}
.input-detail.empty {
  color: var(--text-muted);
  font-style: italic;
}

/* ── Reasoning ──────────────────────────────────────────────────────── */
.reasoning-text {
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-secondary);
}

/* ── Flags ──────────────────────────────────────────────────────────── */
.flag-row {
  margin-top: 6px;
  padding: 6px 10px;
  background: var(--accent-dim);
  border: 1px solid rgba(217,119,6,0.2);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--accent);
  display: flex;
  align-items: center;
  gap: 7px;
}
.flag-icon { font-size: 9px; }
</style>
