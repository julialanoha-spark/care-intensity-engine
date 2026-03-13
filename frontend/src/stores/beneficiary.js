import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { postScore, postReasoning } from '../api/careEngine'

export const useBeneficiaryStore = defineStore('beneficiary', () => {
  // Profile inputs
  const ageBand    = ref('unknown')
  const sex        = ref('unknown')
  const medicaidDual = ref(false)
  const zip        = ref('')           // 5-digit ZIP for plan filtering (does not affect score)
  const selectedPlan = ref(null)       // full plan object from PlanSelector

  const selectedConditionIds = ref([])
  const cancerSeverity       = ref('unspecified')
  const selectedProviderIds  = ref([])

  // Each entry: { id, drugName, dosageName, quantity, frequency, isSpecialty }
  const medicationEntries = ref([])

  // Derived list of IDs for the score API
  const selectedMedicationIds = computed(() =>
    medicationEntries.value.map(e => e.id)
  )

  // ── Score result (fast — deterministic only, no LLM) ──────────────────────
  const scoreResult = ref(null)
  const isLoading   = ref(false)
  const error       = ref(null)

  // ── Reasoning result (slow — LLM, only when plan selected) ───────────────
  const talkingPoints      = ref([])
  const narrativeAvailable = ref(true)
  const reasoningLoading   = ref(false)

  // Debounce timers + in-flight request controllers
  let debounceTimer          = null
  let _abortController       = null
  let reasoningDebounceTimer = null
  let _reasoningAbortController = null

  // Internal: cancer condition ID set by ConditionSelector on load
  const _cancerConditionId = ref(null)
  function setCancerConditionId(id) {
    _cancerConditionId.value = id
  }

  const hasCancer = computed(() =>
    _cancerConditionId.value !== null &&
    selectedConditionIds.value.includes(_cancerConditionId.value)
  )

  // ── Condition helpers ─────────────────────────────────────────────────────
  function toggleCondition(id) {
    const idx = selectedConditionIds.value.indexOf(id)
    if (idx === -1) {
      selectedConditionIds.value.push(id)
    } else {
      selectedConditionIds.value.splice(idx, 1)
      if (id === _cancerConditionId.value) cancerSeverity.value = 'unspecified'
    }
  }

  // ── Provider helpers ──────────────────────────────────────────────────────
  function toggleProvider(id) {
    const idx = selectedProviderIds.value.indexOf(id)
    if (idx === -1) selectedProviderIds.value.push(id)
    else selectedProviderIds.value.splice(idx, 1)
  }

  // ── Medication helpers ────────────────────────────────────────────────────
  function addMedication(entry) {
    // Prevent duplicate (same medication ID already in list)
    if (!medicationEntries.value.find(e => e.id === entry.id)) {
      medicationEntries.value.push(entry)
    }
  }

  function removeMedication(index) {
    medicationEntries.value.splice(index, 1)
  }

  // ── Plan helpers ──────────────────────────────────────────────────────────
  function selectPlan(plan) {
    selectedPlan.value = plan
    talkingPoints.value = []   // clear stale points immediately
    requestScore()
    requestReasoning()
  }

  function clearPlan() {
    selectedPlan.value = null
    talkingPoints.value = []
    narrativeAvailable.value = true
    reasoningLoading.value = false
    _reasoningAbortController?.abort()
    requestScore()
  }

  // ── Score (fast, deterministic) ───────────────────────────────────────────
  async function _fetchScore() {
    // Cancel any previous in-flight score request
    _abortController?.abort()
    _abortController = new AbortController()
    const { signal } = _abortController

    isLoading.value = true
    error.value = null
    try {
      const payload = {
        age_band:        ageBand.value,
        sex:             sex.value,
        medicaid_dual:   medicaidDual.value,
        condition_ids:   selectedConditionIds.value,
        cancer_severity: cancerSeverity.value,
        provider_ids:    selectedProviderIds.value,
        medication_ids:  selectedMedicationIds.value,
      }
      scoreResult.value = await postScore(payload, signal)
    } catch (e) {
      if (e.name === 'AbortError') return
      error.value = e.message
    } finally {
      if (!signal.aborted) isLoading.value = false
    }
  }

  function requestScore() {
    clearTimeout(debounceTimer)
    debounceTimer = setTimeout(_fetchScore, 400)
  }

  // ── Reasoning (slow, LLM — only when plan is selected) ───────────────────
  async function _fetchReasoning() {
    if (!selectedPlan.value) return

    _reasoningAbortController?.abort()
    _reasoningAbortController = new AbortController()
    const { signal } = _reasoningAbortController

    reasoningLoading.value = true
    try {
      const payload = {
        age_band:         ageBand.value,
        sex:              sex.value,
        medicaid_dual:    medicaidDual.value,
        condition_ids:    selectedConditionIds.value,
        cancer_severity:  cancerSeverity.value,
        provider_ids:     selectedProviderIds.value,
        medication_ids:   selectedMedicationIds.value,
        plan_contract_id: selectedPlan.value.contract_id,
        plan_plan_id:     selectedPlan.value.plan_id,
        plan_segment_id:  selectedPlan.value.segment_id,
      }
      const result = await postReasoning(payload, signal)
      talkingPoints.value      = result.talking_points ?? []
      narrativeAvailable.value = result.narrative_available ?? true
    } catch (e) {
      if (e.name === 'AbortError') return
      talkingPoints.value = []
    } finally {
      if (!signal.aborted) reasoningLoading.value = false
    }
  }

  function requestReasoning() {
    clearTimeout(reasoningDebounceTimer)
    reasoningDebounceTimer = setTimeout(_fetchReasoning, 400)
  }

  // Watch all profile inputs — score updates immediately; reasoning re-runs
  // only if a plan is already selected (so the agent sees fresh talking points)
  watch(
    [ageBand, sex, medicaidDual, selectedConditionIds, cancerSeverity,
     selectedProviderIds, medicationEntries],
    () => {
      requestScore()
      if (selectedPlan.value) requestReasoning()
    },
    { deep: true }
  )

  return {
    ageBand, sex, medicaidDual,
    zip, selectedPlan,
    selectedConditionIds, cancerSeverity,
    selectedProviderIds,
    medicationEntries, selectedMedicationIds,
    scoreResult, isLoading, error,
    talkingPoints, narrativeAvailable, reasoningLoading,
    hasCancer,
    setCancerConditionId,
    toggleCondition, toggleProvider,
    addMedication, removeMedication,
    selectPlan, clearPlan,
    requestScore, requestReasoning,
  }
})
