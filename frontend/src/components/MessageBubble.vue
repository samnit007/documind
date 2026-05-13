<template>
  <div :class="['flex', message.role === 'user' ? 'justify-end' : 'justify-start']">
    <div :class="[
      'max-w-2xl rounded-2xl px-4 py-3 text-sm leading-relaxed',
      message.role === 'user'
        ? 'bg-indigo-600 text-white rounded-br-sm'
        : 'bg-white border border-gray-200 text-gray-800 rounded-bl-sm shadow-sm',
    ]">

      <!-- User message -->
      <p v-if="message.role === 'user'">{{ message.content }}</p>

      <!-- Loading -->
      <div v-else-if="message.loading" class="flex items-center gap-2 text-gray-400">
        <span class="flex gap-1">
          <span class="w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce" style="animation-delay: 0ms" />
          <span class="w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce" style="animation-delay: 150ms" />
          <span class="w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce" style="animation-delay: 300ms" />
        </span>
        <span class="text-xs">Thinking…</span>
      </div>

      <!-- Error -->
      <p v-else-if="message.error" class="text-red-500">{{ message.error }}</p>

      <!-- Answer -->
      <div v-else-if="message.response">
        <p class="whitespace-pre-wrap">{{ message.response.answer }}</p>

        <CitationPanel
          v-if="message.response.citations.length"
          :citations="message.response.citations"
        />

        <!-- Metadata footer -->
        <div class="mt-2 flex items-center gap-3 text-xs text-gray-400">
          <span
            :class="[
              'px-1.5 py-0.5 rounded font-medium',
              message.response.confidence >= 0.7 ? 'bg-green-100 text-green-700' :
              message.response.confidence >= 0.4 ? 'bg-yellow-100 text-yellow-700' :
              'bg-red-100 text-red-600'
            ]"
          >
            {{ Math.round(message.response.confidence * 100) }}% confidence
          </span>
          <span>${{ message.response.token_cost_usd.toFixed(5) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Message } from '../types'
import CitationPanel from './CitationPanel.vue'

defineProps<{ message: Message }>()
</script>
