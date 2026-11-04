<script setup lang="ts">
import { computed } from "vue";
import type { RouteLocationRaw } from "vue-router";
import AppBreadcrumb from "./AppBreadcrumb.vue";
import { manage } from "./legacy";

// The breadcrumb of the manage pages: [organization] > section > page, where the last item
// is the current page (no link) like `view.get_breadcrumbs()` of the old modular views.
const props = defineProps<{
  organizationId: number;
  organizationName?: string;
  docsUrl?: string | null;
  items: { label: string; to?: RouteLocationRaw; href?: string }[];
}>();

const all = computed(() =>
  props.organizationName
    ? [
        { label: props.organizationName, href: manage.organization(props.organizationId) },
        ...props.items,
      ]
    : props.items,
);
</script>

<template>
  <AppBreadcrumb :items="all" :docs-url="docsUrl" />
</template>
