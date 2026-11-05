<script setup lang="ts">
// One line of the event property list: icon (with its meaning as title) and content.
defineProps<{ icon: string; title: string }>();
</script>

<template>
  <div>
    <i :class="['fa', 'fa-fw', 'me-2', icon]" :title="title"></i><slot />
  </div>
</template>
