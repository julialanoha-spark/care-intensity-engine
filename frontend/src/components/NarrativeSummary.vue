<template>
  <div class="section" v-if="show">
    <h3 class="section-title">Agent Talking Points</h3>

    <div v-if="store.isLoading" class="loading-row">
      <div class="spinner"></div>
      <span>Generating…</span>
    </div>

    <div v-else-if="!narrativeAvailable" class="no-api">
      <p>
        Add an <code>ANTHROPIC_API_KEY</code> to <code>backend/.env</code> to enable
        AI-generated talking points.
      </p>
    </div>

    <div v-else-if="narrative" class="narrative-text">
      {{ narrative }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useBeneficiaryStore } from '../stores/beneficiary'

const store = useBeneficiaryStore()
const result = computed(() => store.scoreResult)

const narrative = computed(() => result.value?.narrative || '')
const narrativeAvailable = computed(() => result.value?.narrative_available ?? true)
const show = computed(() => !!result.value)
</script>

<style scoped>
.section {
  background: linear-gradient(135deg, #eff6ff, #f0fdf4);
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
}
.section-title {
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #1e40af;
  margin: 0 0 12px;
}
.loading-row {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #9ca3af;
  font-size: 14px;
}
.spinner {
  width: 16px; height: 16px;
  border: 2px solid #e5e7eb;
  border-top-color: #1e40af;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.narrative-text {
  font-size: 14px;
  line-height: 1.7;
  color: #1f2937;
}
.no-api {
  font-size: 13px;
  color: #6b7280;
}
.no-api code {
  background: #f3f4f6;
  padding: 1px 5px;
  border-radius: 3px;
  font-family: monospace;
  font-size: 12px;
}
</style>
