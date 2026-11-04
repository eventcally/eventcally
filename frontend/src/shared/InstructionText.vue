<script setup lang="ts">
import { computed } from "vue";
import type { RouteLocationRaw } from "vue-router";

import { LINK_CLOSE, LINK_OPEN } from "./instruction";

// The instruction line of a list page; the link sits between the two markers.

const props = defineProps<{
  text: string;
  to?: RouteLocationRaw;
  href?: string;
}>();

const parts = computed(() => {
  const [before, rest = ""] = props.text.split(LINK_OPEN);
  const [label, after = ""] = rest.split(LINK_CLOSE);
  return { before, label, after, hasLink: props.text.includes(LINK_OPEN) };
});
</script>

<template>
  <!-- No whitespace around the link: the text carries its own. -->
  <p data-test="instruction">
    {{ parts.before
    }}<template v-if="parts.hasLink"
      ><router-link v-if="to" :to="to">{{ parts.label }}</router-link
      ><a v-else :href="href">{{ parts.label }}</a></template
    >{{ parts.after }}
  </p>
</template>
