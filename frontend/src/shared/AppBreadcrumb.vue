<script setup lang="ts">
import type { RouteLocationRaw } from "vue-router";

defineProps<{ items: { label: string; to?: RouteLocationRaw; href?: string }[] }>();
</script>

<template>
  <!-- Looks like the Bootstrap 4 breadcrumb of the Jinja pages (grey bar). -->
  <nav aria-label="breadcrumb">
    <ol class="breadcrumb bg-body-secondary rounded px-3 py-3">
      <li
        v-for="(item, index) in items"
        :key="index"
        class="breadcrumb-item"
        :class="{ active: !item.to && !item.href }"
        :aria-current="item.to || item.href ? undefined : 'page'"
      >
        <router-link v-if="item.to" :to="item.to">{{ item.label }}</router-link>
        <!-- A server-rendered page (a full page load, no router). -->
        <a v-else-if="item.href" :href="item.href">{{ item.label }}</a>
        <template v-else>{{ item.label }}</template>
      </li>
    </ol>
  </nav>
</template>
