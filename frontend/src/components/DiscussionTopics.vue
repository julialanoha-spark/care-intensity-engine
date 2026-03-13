<template>
  <div class="section" v-if="topics.length > 0">
    <div class="section-header">
      <span class="section-label">Plan Areas to Discuss</span>
      <span class="count-chip">{{ topics.length }}</span>
    </div>

    <div v-for="(group, category) in grouped" :key="category" class="topic-group">
      <div :class="['category-header', `cat-${categoryKey(category)}`]">
        <span class="cat-accent"></span>
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

const CATEGORY_KEYS = {
  'Prescription Drug Coverage': 'drug',
  'Provider Network':           'network',
  'Care Management':            'care',
  'Supplemental Benefits':      'supp',
  'Cost Protection':            'cost',
}
function categoryKey(cat) { return CATEGORY_KEYS[cat] || 'default' }
</script>

<style scoped>
.section {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  margin-bottom: 10px;
}

.section-header { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; }
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

.topic-group { margin-bottom: 14px; }
.topic-group:last-child { margin-bottom: 0; }

.category-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding-bottom: 6px;
  margin-bottom: 6px;
  border-bottom: 1px solid var(--border);
  font-family: var(--font-mono);
}

.cat-accent {
  display: inline-block;
  width: 3px;
  height: 12px;
  border-radius: 2px;
  flex-shrink: 0;
}

/* Category accent colors */
.cat-drug     { color: #c084fc; }
.cat-drug     .cat-accent { background: #c084fc; }
.cat-network  { color: #60a5fa; }
.cat-network  .cat-accent { background: #60a5fa; }
.cat-care     { color: #34d399; }
.cat-care     .cat-accent { background: #34d399; }
.cat-supp     { color: #fbbf24; }
.cat-supp     .cat-accent { background: #fbbf24; }
.cat-cost     { color: #fb923c; }
.cat-cost     .cat-accent { background: #fb923c; }
.cat-default  { color: var(--teal); }
.cat-default  .cat-accent { background: var(--teal); }

.topic-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 6px; }
.topic-item {
  padding: 9px 12px;
  background: var(--bg-surface);
  border-radius: var(--radius-sm);
  border-left: 2px solid var(--border-bright);
  transition: border-color 0.15s;
}
.topic-item:hover { border-left-color: var(--teal); }
.topic-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 3px;
}
.topic-reason {
  font-size: 11px;
  color: var(--text-muted);
  line-height: 1.5;
}
</style>
