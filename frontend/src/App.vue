<template>
  <div class="flex flex-col h-full bg-gray-50">

    <!-- Header -->
    <header class="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h1 class="text-lg font-semibold text-gray-900">DocuMind</h1>
        <p class="text-xs text-gray-400 mt-0.5">
          Q&amp;A over Anthropic · LangChain · Pydantic AI docs
          <span v-if="chunks" class="ml-2 text-indigo-500">· {{ chunks.toLocaleString() }} chunks indexed</span>
        </p>
      </div>
      <ProviderToggle v-model="provider" />
    </header>

    <!-- Messages -->
    <main ref="scrollEl" class="flex-1 overflow-y-auto px-6 py-6 space-y-4">
      <!-- Empty state -->
      <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full text-center gap-3">
        <div class="text-4xl">📚</div>
        <h2 class="text-gray-700 font-medium">Ask anything about AI tooling</h2>
        <p class="text-gray-400 text-sm max-w-sm">
          Try: "How does RAG work in LangChain?", "What Claude models are available?",
          or "How do I define tools in Pydantic AI?"
        </p>
        <div class="flex flex-wrap gap-2 justify-center mt-2">
          <button
            v-for="q in suggestions"
            :key="q"
            @click="sendSuggestion(q)"
            class="text-xs bg-white border border-gray-200 rounded-full px-3 py-1.5 text-gray-600 hover:border-indigo-400 hover:text-indigo-600 transition-colors"
          >
            {{ q }}
          </button>
        </div>
      </div>

      <MessageBubble v-for="m in messages" :key="m.id" :message="m" />
    </main>

    <!-- Input -->
    <footer class="bg-white border-t border-gray-200 px-6 py-4">
      <form @submit.prevent="send" class="flex gap-3">
        <input
          v-model="input"
          :disabled="loading"
          type="text"
          placeholder="Ask a question about AI tooling docs…"
          class="flex-1 rounded-xl border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:opacity-50"
        />
        <button
          type="submit"
          :disabled="loading || !input.trim()"
          class="bg-indigo-600 text-white rounded-xl px-5 py-2.5 text-sm font-medium hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          Ask
        </button>
      </form>
      <p class="text-xs text-gray-400 mt-2 text-center">
        Answers grounded in docs · citations shown · cost tracked per query
      </p>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import type { Message, Provider } from './types'
import { askQuestion, getHealth } from './api/query'
import MessageBubble from './components/MessageBubble.vue'
import ProviderToggle from './components/ProviderToggle.vue'

const messages = ref<Message[]>([])
const input = ref('')
const loading = ref(false)
const provider = ref<Provider>('claude')
const scrollEl = ref<HTMLElement | null>(null)
const chunks = ref<number | null>(null)

let nextId = 1

const suggestions = [
  'What is chain-of-thought prompting?',
  'How does RAG work in LangChain?',
  'How do I define tools in Pydantic AI?',
  'What Claude models are available?',
  'How does LangGraph handle state?',
]

onMounted(async () => {
  try {
    const h = await getHealth()
    chunks.value = h.chunks_indexed
  } catch {}
})

async function scrollBottom() {
  await nextTick()
  if (scrollEl.value) {
    scrollEl.value.scrollTop = scrollEl.value.scrollHeight
  }
}

async function send() {
  const question = input.value.trim()
  if (!question || loading.value) return

  input.value = ''
  loading.value = true

  messages.value.push({ id: nextId++, role: 'user', content: question })
  messages.value.push({ id: nextId++, role: 'assistant', content: '', loading: true })
  const idx = messages.value.length - 1
  await scrollBottom()

  try {
    const response = await askQuestion(question, provider.value)
    messages.value[idx].loading = false
    messages.value[idx].response = response
  } catch (e: unknown) {
    messages.value[idx].loading = false
    messages.value[idx].error = e instanceof Error ? e.message : 'Something went wrong'
  } finally {
    loading.value = false
    await scrollBottom()
  }
}

function sendSuggestion(q: string) {
  input.value = q
  send()
}
</script>
