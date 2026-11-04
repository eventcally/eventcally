<script setup lang="ts">
// The review status pill of the reference request lists / read page (`inbox` 1,
// `verified` 2, `rejected` 3).
defineProps<{ status: number; label: string }>();

const VARIANTS: Record<number, string> = { 1: "info", 2: "success", 3: "danger" };
</script>

<template>
  <span class="badge rounded-pill" :class="`text-bg-${VARIANTS[status] ?? 'secondary'}`">{{
    label
  }}</span>
</template>
