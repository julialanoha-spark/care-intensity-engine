<template>
  <div class="section" v-if="topics.length > 0">
    <h3 class="section-title">Plan Areas to Discuss</h3>

    <div v-for="(group, category) in grouped" :key="category" class="topic-group">
      <div class="category-header">
        <span :class="['category-icon', categoryIcon(category)]"></span>
        {{ category }}
      </div>
      <ul class="topic-list">
        <li v-for="topic in group" :key="topic.topic" class="topic-item">
          <div class="topic-name">{{ topic.topic }}</div>
          <div class="topic-reason">{{ topic.reason }}</div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useBeneficiaryStore } from '../stores/beneficiary'

const store = useBeneficiaryStore()

const topics = computed(() => store.scoreResult?.discussion_topics || [])

const grouped = computed(() => {
  const result = {}
  for (const t of topics.value) {
    if (!result[t.category]) result[t.category] = []
    result[t.category].push(t)
  }
  return result
})

function categoryIcon(category) {
  const map = {
    'Prescription Drug Coverage': 'icon-pill',
    'Provider Network': 'icon-doctor',
    'Care Management': 'icon-heart',
    'Supplemental Benefits': 'icon-star',
    'Cost Protection': 'icon-shield',
  }
  return map[category] || 'icon-default'
}
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
  margin: 0 0 14px;
}
.topic-group { margin-bottom: 14px; }
.category-header {
  font-size: 12px;
  font-weight: 700;
  color: #1e40af;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 6px;
  padding-bottom: 4px;
  border-bottom: 2px solid #dbeafe;
}
.topic-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
.topic-item { padding: 8px 10px; background: #f9fafb; border-radius: 6px; border-left: 3px solid #3b82f6; }
.topic-name { font-size: 13px; font-weight: 600; color: #111827; margin-bottom: 3px; }
.topic-reason { font-size: 12px; color: #6b7280; line-height: 1.5; }
</style>
