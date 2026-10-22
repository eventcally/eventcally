<script setup lang="ts">
import {
  BFormCheckbox,
  BFormGroup,
  BFormInput,
  BFormSelect,
  BTab,
  BTabs,
} from "bootstrap-vue-next";
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import {
  fieldsFor,
  type FieldDescriptor,
  type Settings,
  type WidgetType,
} from "@/shared/customWidget";

const props = defineProps<{ type: WidgetType }>();
const settings = defineModel<Settings>("settings", { required: true });

const { t } = useI18n();

type Row = FieldDescriptor<Record<string, unknown>>;

const fields = computed(() => fieldsFor(props.type) as unknown as Row[]);
const visible = (tab: "settings" | "styles") =>
  fields.value.filter(
    (f) =>
      f.tab === tab &&
      (!f.visibleIf || f.visibleIf(settings.value as unknown as Record<string, unknown>)),
  );

const options: Record<string, () => { value: string; text: string }[]> = {
  layout: () => [
    { value: "card", text: t("Cards") },
    { value: "text", text: t("Text") },
  ],
  calendarType: () => [
    { value: "week", text: t("Week") },
    { value: "month", text: t("Month") },
  ],
};

const value = (key: string) => (settings.value as unknown as Record<string, unknown>)[key];

function set(field: Row, raw: unknown) {
  const next = field.kind === "number" && raw !== "" && raw != null ? Number(raw) : raw;
  settings.value = { ...settings.value, [field.key]: next } as Settings;
}
</script>

<template>
  <BTabs card>
    <BTab v-for="tab in ['settings', 'styles'] as const" :key="tab" :active="tab === 'settings'">
      <template #title>{{ tab === "settings" ? t("Settings") : t("Styles") }}</template>
      <template v-for="field in visible(tab)" :key="field.key">
        <BFormCheckbox
          v-if="field.kind === 'checkbox'"
          :model-value="Boolean(value(field.key))"
          :value="true"
          :unchecked-value="false"
          class="mb-2"
          @update:model-value="set(field, $event)"
        >
          {{ field.label(t) }}
        </BFormCheckbox>
        <BFormGroup v-else :label="field.label(t)" :label-for="`field-${field.key}`" class="mb-3">
          <BFormSelect
            v-if="field.kind === 'select'"
            :id="`field-${field.key}`"
            :model-value="value(field.key) as string"
            :options="options[field.key]?.() ?? []"
            @update:model-value="set(field, $event)"
          />
          <BFormInput
            v-else
            :id="`field-${field.key}`"
            :type="field.kind === 'text' ? 'text' : field.kind"
            :model-value="value(field.key) as string | number"
            :debounce="field.debounce ? 500 : 0"
            @update:model-value="set(field, $event)"
          />
        </BFormGroup>
      </template>
    </BTab>
  </BTabs>
</template>
