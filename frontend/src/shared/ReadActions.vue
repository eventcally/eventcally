<script setup lang="ts">
import { BDropdown, BDropdownItem } from "bootstrap-vue-next";
import { useI18n } from "vue-i18n";
import type { RowAction } from "./RowActions.vue";

// The "Actions" dropdown of a read page (`get_read_actions`).
defineProps<{ actions: RowAction[] }>();

const { t } = useI18n();
</script>

<template>
  <div v-if="actions.length" class="my-4">
    <BDropdown :text="t('Actions')" variant="outline-secondary" teleport-to="body">
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
  </div>
</template>
