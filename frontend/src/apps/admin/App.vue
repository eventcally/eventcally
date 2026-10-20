<script setup lang="ts">
import { BOrchestrator } from "bootstrap-vue-next";
import { RouterView } from "vue-router";
</script>

<template>
  <RouterView />
  <!-- Toasts live outside the routed page so they survive router.push. -->
  <BOrchestrator />
</template>
