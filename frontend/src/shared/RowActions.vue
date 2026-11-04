<script setup lang="ts">
import { BDropdown, BDropdownItem } from "bootstrap-vue-next";
import type { RouteLocationRaw } from "vue-router";

// The dropdown on the main column of a list row (`get_all_list_actions`): links for pages,
// callbacks for the confirm / edit modals.
export interface RowAction {
  title: string;
  to?: RouteLocationRaw;
  href?: string;
  onClick?: () => void;
}

defineProps<{ label: string; actions: RowAction[] }>();

// The caret stays with the last word of a wrapping name.
const head = (name: string) => name.slice(0, name.lastIndexOf(" ") + 1);
const tail = (name: string) => name.slice(name.lastIndexOf(" ") + 1);
</script>

<template>
  <BDropdown
    variant="link"
    no-caret
    toggle-class="p-0 border-0 text-start align-baseline"
    class="row-actions"
    teleport-to="body"
  >
    <template #button-content>
      {{ head(label) }}<span class="text-nowrap">{{ tail(label) }}<i class="fa fa-caret-down ms-1"></i></span>
    </template>
    <BDropdownItem
      v-for="action in actions"
      :key="action.title"
      :to="action.to"
      :href="action.href"
      @click="action.onClick?.()"
    >
      {{ action.title }}
    </BDropdownItem>
  </BDropdown>
</template>
