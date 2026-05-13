<template>
  <div class="mt-3 border-t border-gray-100 pt-3">
    <button
      @click="open = !open"
      class="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-700 transition-colors"
    >
      <svg
        :class="['w-3 h-3 transition-transform', open ? 'rotate-90' : '']"
        fill="none" stroke="currentColor" viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
      </svg>
      {{ citations.length }} source{{ citations.length !== 1 ? 's' : '' }}
    </button>

    <div v-if="open" class="mt-2 space-y-2">
      <div
        v-for="(c, i) in citations"
        :key="i"
        class="bg-gray-50 rounded-lg p-3 text-xs"
      >
        <div class="flex items-center justify-between mb-1">
          <span class="font-semibold text-indigo-700">{{ c.source }}</span>
          <a
            v-if="c.url"
            :href="c.url"
            target="_blank"
            rel="noopener"
            class="text-gray-400 hover:text-indigo-600 transition-colors"
          >↗</a>
        </div>
        <p class="text-gray-600 italic leading-relaxed">"{{ c.excerpt }}"</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { Citation } from '../types'

defineProps<{ citations: Citation[] }>()
const open = ref(false)
</script>
