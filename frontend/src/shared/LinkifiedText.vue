<script setup lang="ts">
import { computed } from "vue";
import { linkify } from "./linkify";

const props = defineProps<{ text: string }>();

const parts = computed(() => linkify(props.text));
</script>

<template>
  <!-- Text nodes and anchors only, never `v-html`: markup in the text stays text. -->
  <span
    ><template v-for="(part, index) in parts" :key="index"
      ><a
        v-if="'href' in part"
        :href="part.href"
        target="_blank"
        rel="nofollow noopener noreferrer"
        >{{ part.text }}</a
      ><template v-else>{{ part.text }}</template></template
    ></span
  >
</template>
