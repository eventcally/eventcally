<script setup lang="ts">
import { BButton, BFormCheckbox, BFormInput } from "bootstrap-vue-next";
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import { defaultEnd, type DateDefinitionValue } from "../eventForm";
import { describe, parse } from "../recurrenceRule";
import RecurrenceRuleModal from "./RecurrenceRuleModal.vue";

const props = defineProps<{
  organizationId: number;
  index: number;
  // More than one date: this one can be removed.
  removable: boolean;
  errors?: { start?: string; end?: string };
}>();
const model = defineModel<DateDefinitionValue>({ required: true });
const emit = defineEmits<{ remove: [] }>();

const { t, locale } = useI18n();
const showRecurrence = ref(false);

const prefix = computed(() => `date_definitions-${props.index}-`);
const summary = computed(() => {
  const rule = model.value.recurrenceRule;
  if (!rule) return null;
  const value = parse(rule);
  return value ? describe(value, t, locale.value) : rule;
});

function set<K extends keyof DateDefinitionValue>(key: K, value: DateDefinitionValue[K]) {
  model.value = { ...model.value, [key]: value };
}

function showEnd() {
  const end = defaultEnd(model.value);
  model.value = { ...model.value, endShown: true, endDate: end.date, endTime: end.time };
}

function hideEnd() {
  // Without an end the date cannot be all-day (legacy).
  model.value = { ...model.value, endShown: false, endDate: "", endTime: "", allday: false };
}

function setAllday(allday: boolean) {
  if (allday && !model.value.endShown) {
    const end = defaultEnd({ ...model.value, allday });
    model.value = { ...model.value, allday, endShown: true, endDate: end.date, endTime: end.time };
    return;
  }
  set("allday", allday);
}
</script>

<template>
  <div class="date-definition bg-light border rounded p-3 mb-3" :data-test="`${prefix}container`">
    <div class="mb-2">
      <label class="form-label mb-0" :for="`${prefix}start`">{{ t("Start") }} *</label>
      <div class="form-text mt-0 mb-1">{{ t("Indicate when the event date will start.") }}</div>
      <div class="d-flex flex-wrap gap-2">
        <BFormInput
          :id="`${prefix}start`"
          type="date"
          required
          class="w-auto"
          :state="errors?.start ? false : null"
          :model-value="model.startDate"
          @update:model-value="set('startDate', String($event))"
        />
        <BFormInput
          v-if="!model.allday"
          :id="`${prefix}start-time`"
          type="time"
          required
          class="w-auto"
          :state="errors?.start ? false : null"
          :model-value="model.startTime"
          @update:model-value="set('startTime', String($event))"
        />
      </div>
      <div v-if="errors?.start" class="invalid-feedback d-block">{{ errors.start }}</div>
    </div>

    <div class="mb-2">
      <BButton
        v-if="!model.endShown"
        variant="link"
        class="p-0 text-decoration-none"
        :data-test="`${prefix}end-show`"
        @click="showEnd"
      >
        <i class="fa fa-plus"></i> {{ t("End") }}
      </BButton>
      <template v-else>
        <div class="d-flex align-items-center">
          <label class="form-label mb-0" :for="`${prefix}end`">{{ t("End") }}</label>
          <BButton
            variant="link"
            class="p-0 ms-2 text-decoration-none"
            :title="t('Remove')"
            :data-test="`${prefix}end-hide`"
            @click="hideEnd"
          >
            <i class="fa fa-times"></i>
          </BButton>
        </div>
        <div class="form-text mt-0 mb-1">
          {{ t("Indicate when the event date will end. An event can last a maximum of 180 days.") }}
        </div>
        <div class="d-flex flex-wrap gap-2">
          <BFormInput
            :id="`${prefix}end`"
            type="date"
            class="w-auto"
            :min="model.startDate"
            :state="errors?.end ? false : null"
            :model-value="model.endDate"
            @update:model-value="set('endDate', String($event))"
          />
          <BFormInput
            v-if="!model.allday"
            :id="`${prefix}end-time`"
            type="time"
            class="w-auto"
            :state="errors?.end ? false : null"
            :model-value="model.endTime"
            @update:model-value="set('endTime', String($event))"
          />
        </div>
        <div v-if="errors?.end" class="invalid-feedback d-block">{{ errors.end }}</div>
      </template>
    </div>

    <BFormCheckbox
      :id="`${prefix}allday`"
      class="mb-2"
      :model-value="model.allday"
      @update:model-value="setAllday(Boolean($event))"
    >
      {{ t("All-day") }}
    </BFormCheckbox>

    <div v-if="summary" class="mb-2" :data-test="`${prefix}recurrence-summary`">
      <i class="fa fa-redo me-1"></i>{{ summary }}
    </div>

    <div class="d-flex flex-wrap gap-2">
      <BButton
        :id="`${prefix}recc-button`"
        size="sm"
        variant="outline-secondary"
        @click="showRecurrence = true"
      >
        <template v-if="model.recurrenceRule">
          <i class="fa fa-edit"></i> {{ t("Edit recurrence") }}
        </template>
        <template v-else><i class="fa fa-history"></i> {{ t("Recurring event") }}</template>
      </BButton>
      <BButton
        v-if="model.recurrenceRule"
        size="sm"
        variant="outline-secondary"
        :data-test="`${prefix}recc-remove`"
        @click="set('recurrenceRule', null)"
      >
        <i class="fa fa-times-circle"></i> {{ t("Remove recurrence") }}
      </BButton>
      <BButton
        v-if="removable"
        size="sm"
        variant="outline-danger"
        :data-test="`${prefix}remove`"
        @click="emit('remove')"
      >
        <i class="fa fa-trash"></i> {{ t("Remove event date") }}
      </BButton>
    </div>

    <RecurrenceRuleModal
      v-model:show="showRecurrence"
      :model-value="model.recurrenceRule"
      :organization-id="organizationId"
      :start="model.startDate"
      :id-prefix="prefix"
      @update:model-value="set('recurrenceRule', $event)"
    />
  </div>
</template>
