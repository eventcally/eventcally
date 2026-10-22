<script setup lang="ts">
import { BModal } from "bootstrap-vue-next";
import { ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import type { PlanningExternalCalendar } from "../planning";

const props = defineProps<{ calendars: PlanningExternalCalendar[] }>();
const visible = defineModel<boolean>({ default: false });
const emit = defineEmits<{ apply: [active: string[]] }>();

const { t } = useI18n();
const active = ref<string[]>([]);

watch(
  visible,
  (open) => {
    if (open) active.value = props.calendars.filter((c) => c.active).map((c) => c.url);
  },
  { immediate: true },
);

function close() {
  emit("apply", active.value);
  visible.value = false;
}
</script>

<template>
  <BModal v-model="visible" :title="t('External calendars')" size="lg" @hide="emit('apply', active)">
    <div v-for="calendar in calendars" :key="calendar.url" class="form-check">
      <input
        :id="`external-calendar-${calendar.url}`"
        v-model="active"
        class="form-check-input"
        type="checkbox"
        :value="calendar.url"
      />
      <label class="form-check-label" :for="`external-calendar-${calendar.url}`">
        {{ calendar.title }}
        <small v-if="calendar.title !== calendar.url" class="text-body-secondary d-block">{{
          calendar.url
        }}</small>
      </label>
    </div>
    <template #footer>
      <button
        type="button"
        class="btn btn-outline-secondary"
        data-test="external-close"
        @click="close"
      >
        {{ t("Close") }}
      </button>
    </template>
  </BModal>
</template>
