<template>
  <div class="flex items-center gap-2">
    <span class="text-xs text-gray-500">Model:</span>
    <div class="flex rounded-lg border border-gray-200 overflow-hidden text-xs font-medium">
      <button
        v-for="p in providers"
        :key="p.value"
        @click="$emit('update:modelValue', p.value)"
        :class="[
          'px-3 py-1.5 transition-colors',
          modelValue === p.value
            ? 'bg-indigo-600 text-white'
            : 'bg-white text-gray-600 hover:bg-gray-50',
        ]"
      >
        {{ p.label }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Provider } from '../types'

defineProps<{ modelValue: Provider }>()
defineEmits<{ 'update:modelValue': [value: Provider] }>()

const providers = [
  { value: 'claude' as Provider, label: 'Claude' },
  { value: 'openai' as Provider, label: 'GPT-4o mini' },
]
</script>
