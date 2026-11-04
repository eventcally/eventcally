<script setup lang="ts">
import { BCollapse } from "bootstrap-vue-next";
import { ref } from "vue";
import { useI18n } from "vue-i18n";

// The "Filters" toggle of the old list pages: a collapse that is open when a filter is set.
const props = defineProps<{ active: boolean }>();
const emit = defineEmits<{ submit: []; reset: [] }>();

const { t } = useI18n();
const open = ref(props.active);
</script>

<template>
  <div class="mb-3">
    <button
      type="button"
      class="btn btn-outline-primary"
      data-test="filters-toggle"
      :aria-expanded="open"
      @click="open = !open"
    >
      <i class="fa fa-filter"></i> {{ t("Filters") }}
    </button>
    <BCollapse v-model="open" class="mt-3">
      <form data-test="filters-form" @submit.prevent="emit('submit')">
        <slot />
        <button type="submit" class="btn btn-primary me-2">{{ t("Refresh") }}</button>
        <button
          v-if="active"
          type="button"
          class="btn btn-outline-secondary"
          data-test="filters-reset"
          @click="emit('reset')"
        >
          {{ t("Reset") }}
        </button>
      </form>
    </BCollapse>
  </div>
</template>
