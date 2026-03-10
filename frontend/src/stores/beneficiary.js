import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { postScore } from '../api/careEngine'

export const useBeneficiaryStore = defineStore('beneficiary', () => {
  // Profile inputs
  const ageBand = ref('unknown')
  const sex = ref('unknown')
  const medicaidDual = ref(false)
  const selectedConditionIds = ref([])
  const cancerSeverity = ref('unspecified')
  const selectedProviderIds = ref([])
  const selectedMedicationIds = ref([])

  // Score result
  const scoreResult = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  // Debounce timer
  let debounceTimer = null

  const hasCancer = computed(() =>
    // Will be set from conditions list; check via store flag
    _cancerConditionId.value !== null && selectedConditionIds.value.includes(_cancerConditionId.value)
  )

  // Internal: cancer condition ID, set by App when conditions load
  const _cancerConditionId = ref(null)
  function setCancerConditionId(id) {
    _cancerConditionId.value = id
  }

  function toggleCondition(id) {
    const idx = selectedConditionIds.value.indexOf(id)
    if (idx === -1) {
      selectedConditionIds.value.push(id)
    } else {
      selectedConditionIds.value.splice(idx, 1)
      // Reset cancer severity if cancer deselected
      if (id === _cancerConditionId.value) {
        cancerSeverity.value = 'unspecified'
      }
    }
  }

  function toggleProvider(id) {
    const idx = selectedProviderIds.value.indexOf(id)
    if (idx === -1) selectedProviderIds.value.push(id)
    else selectedProviderIds.value.splice(idx, 1)
  }

  function toggleMedication(id) {
    const idx = selectedMedicationIds.value.indexOf(id)
    if (idx === -1) selectedMedicationIds.value.push(id)
    else selectedMedicationIds.value.splice(idx, 1)
  }

  async function _fetchScore() {
    isLoading.value = true
    error.value = null
    try {
      scoreResult.value = await postScore({
        age_band: ageBand.value,
        sex: sex.value,
        medicaid_dual: medicaidDual.value,
        condition_ids: selectedConditionIds.value,
        cancer_severity: cancerSeverity.value,
        provider_ids: selectedProviderIds.value,
        medication_ids: selectedMedicationIds.value,
      })
    } catch (e) {
      error.value = e.message
    } finally {
      isLoading.value = false
    }
  }

  function requestScore() {
    clearTimeout(debounceTimer)
    debounceTimer = setTimeout(_fetchScore, 400)
  }

  // Watch all profile inputs and auto-score
  watch(
    [ageBand, sex, medicaidDual, selectedConditionIds, cancerSeverity, selectedProviderIds, selectedMedicationIds],
    requestScore,
    { deep: true }
  )

  return {
    ageBand, sex, medicaidDual,
    selectedConditionIds, cancerSeverity,
    selectedProviderIds, selectedMedicationIds,
    scoreResult, isLoading, error,
    hasCancer,
    setCancerConditionId,
    toggleCondition, toggleProvider, toggleMedication,
    requestScore,
  }
})
