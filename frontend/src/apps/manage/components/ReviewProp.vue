<script setup lang="ts">
defineProps<{ icon: string; title: string }>();
</script>

<template>
  <div>
    <i class="fa fa-fw me-1" :class="icon" :title="title"></i>
    <slot />
  </div>
</template>
