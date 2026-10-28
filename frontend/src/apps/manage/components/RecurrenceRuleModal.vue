<script setup lang="ts">
import { BButton, BFormCheckbox, BFormInput, BFormRadio, BFormSelect, BModal, BSpinner } from "bootstrap-vue-next";
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";
import {
  defaultRecurrence,
  formatDate,
  fromDateTime,
  monthName,
  parse,
  serialize,
  toDateTime,
  WEEKDAY_INDEXES,
  weekdayIndexLabel,
  weekdayName,
  type Frequency,
  type RecurrenceValue,
  type Weekday,
} from "../recurrenceRule";

interface Occurrence {
  date: string;
  formatted_date: string;
  type: string;
}

const props = defineProps<{
  organizationId: number;
  // The start day of the date (`YYYY-MM-DD`): defaults and the preview.
  start: string;
  // Prefix of the input ids (one modal per date of the form).
  idPrefix: string;
}>();
// The stored rule; `null` without recurrence.
const rule = defineModel<string | null>({ default: null });
const show = defineModel<boolean>("show", { default: false });

const { t, locale } = useI18n();

// Monday first, as the legacy widget showed them.
const DISPLAY_WEEKDAYS: Weekday[] = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"];
const PREVIEW_DELAY_MS = 300;

const value = ref<RecurrenceValue>(defaultRecurrence("DAILY", props.start));
// A stored rule the editor cannot write back unchanged: shown read-only.
const raw = ref<string | null>(null);
const occurrences = ref<Occurrence[]>([]);
const hasMore = ref(false);
// The first occurrence of the last loaded batch of ten.
const batchStart = ref(0);
const previewLoading = ref(false);
const previewError = ref<string | null>(null);
const addDate = ref("");
let previewTimer: ReturnType<typeof setTimeout> | undefined;
let previewRequest = 0;

const frequencyOptions = computed(() => [
  { value: "DAILY", text: t("Daily") },
  { value: "WEEKLY", text: t("Weekly") },
  { value: "MONTHLY", text: t("Monthly") },
  { value: "YEARLY", text: t("Yearly") },
]);
const intervalUnit = computed(
  () =>
    ({
      DAILY: t("day(s)"),
      WEEKLY: t("week(s)"),
      MONTHLY: t("month(s)"),
      YEARLY: t("year(s)"),
    })[value.value.freq],
);
const dayOptions = computed(() => Array.from({ length: 31 }, (_, i) => ({ value: i + 1, text: String(i + 1) })));
const monthOptions = computed(() =>
  Array.from({ length: 12 }, (_, i) => ({ value: i + 1, text: monthName(i + 1, locale.value) })),
);
const indexOptions = computed(() =>
  WEEKDAY_INDEXES.map((index) => ({ value: index, text: weekdayIndexLabel(index, t) })),
);
const weekdayOptions = computed(() =>
  DISPLAY_WEEKDAYS.map((day) => ({ value: day, text: weekdayName(day, locale.value) })),
);
const hasDayOptions = computed(() => value.value.freq === "MONTHLY" || value.value.freq === "YEARLY");

function id(name: string) {
  return `${props.idPrefix}recc-${name}`;
}

function open() {
  addDate.value = "";
  occurrences.value = [];
  raw.value = null;

  if (!rule.value) {
    value.value = defaultRecurrence("DAILY", props.start);
    return;
  }

  const parsed = parse(rule.value);
  if (parsed) value.value = parsed;
  else raw.value = rule.value;
}

function setFrequency(freq: Frequency) {
  // The legacy widget keeps the end of the rule when the frequency changes.
  value.value = { ...defaultRecurrence(freq, props.start), end: value.value.end };
}

function toggleWeekday(day: Weekday, checked: boolean) {
  const weekdays = value.value.weekdays.filter((item) => item !== day);
  value.value = { ...value.value, weekdays: checked ? [...weekdays, day] : weekdays };
}

function setEndType(type: "never" | "count" | "until") {
  value.value = {
    ...value.value,
    end:
      type === "never"
        ? { type }
        : type === "count"
          ? { type, count: value.value.end.type === "count" ? value.value.end.count : 7 }
          : { type, until: value.value.end.type === "until" ? value.value.end.until : props.start },
  };
}

function setCount(text: string) {
  const count = Math.max(1, Math.floor(Number(text)) || 1);
  value.value = { ...value.value, end: { type: "count", count } };
}

function setInterval(text: string) {
  value.value = { ...value.value, interval: Math.max(1, Math.floor(Number(text)) || 1) };
}

function toggleOccurrence(occurrence: Occurrence) {
  const { exdates, rdates } = value.value;

  if (occurrence.type === "exdate") {
    value.value = { ...value.value, exdates: exdates.filter((date) => date !== occurrence.date) };
  } else if (occurrence.type === "rdate") {
    value.value = { ...value.value, rdates: rdates.filter((date) => date !== occurrence.date) };
  } else {
    value.value = { ...value.value, exdates: [...exdates, occurrence.date] };
  }
}

function addRdate() {
  if (!addDate.value) return;
  const date = toDateTime(addDate.value);
  if (!value.value.rdates.includes(date)) {
    value.value = { ...value.value, rdates: [...value.value.rdates, date] };
  }
  addDate.value = "";
}

async function loadPreview(start: number) {
  const current = ++previewRequest;
  previewLoading.value = true;
  previewError.value = null;

  const { data, error } = await api.POST("/bff/manage/organizations/{id}/events/occurrences", {
    params: { path: { id: props.organizationId } },
    body: { start: `${props.start}T00:00`, rrule: serialize(value.value), batch_start: start },
  });
  // A newer preview (or a closed modal) has superseded this one.
  if (current !== previewRequest) return;
  previewLoading.value = false;

  if (!data) {
    previewError.value = error?.message ?? t("Error");
    return;
  }
  occurrences.value = start ? [...occurrences.value, ...data.items] : data.items;
  batchStart.value = start;
  hasMore.value = data.has_more;
}

function schedulePreview() {
  clearTimeout(previewTimer);
  previewTimer = setTimeout(() => loadPreview(0), PREVIEW_DELAY_MS);
}

function apply() {
  if (raw.value === null) rule.value = serialize(value.value);
  show.value = false;
}

function remove() {
  rule.value = null;
  show.value = false;
}

watch(show, (visible) => {
  if (visible) {
    open();
    if (raw.value === null) schedulePreview();
  } else {
    clearTimeout(previewTimer);
    previewRequest++;
  }
});
watch(value, () => show.value && raw.value === null && schedulePreview(), { deep: true });

onBeforeUnmount(() => clearTimeout(previewTimer));
</script>

<template>
  <BModal
    v-model="show"
    :title="t('Recurring event')"
    lazy
    unmount-lazy
    scrollable
    :data-test="`${idPrefix}recurrence-modal`"
  >
    <template v-if="raw !== null">
      <div class="alert alert-warning" role="alert" data-test="raw-hint">
        {{ t("This recurrence can only be edited in the previous form.") }}
      </div>
      <pre class="bg-light border rounded p-2 small" data-test="raw-rule">{{ raw }}</pre>
    </template>

    <template v-else>
      <div class="row g-2 mb-3">
        <div class="col-sm-6">
          <label class="form-label" :for="id('freq')">{{ t("Repeats") }}</label>
          <BFormSelect
            :id="id('freq')"
            :model-value="value.freq"
            :options="frequencyOptions"
            @update:model-value="setFrequency($event as Frequency)"
          />
        </div>
        <div class="col-sm-6">
          <label class="form-label" :for="id('interval')">{{ t("Repeats every") }}</label>
          <div class="input-group">
            <BFormInput
              :id="id('interval')"
              type="number"
              min="1"
              :model-value="value.interval"
              @update:model-value="setInterval(String($event))"
            />
            <span class="input-group-text">{{ intervalUnit }}</span>
          </div>
        </div>
      </div>

      <div v-if="value.freq === 'WEEKLY'" class="mb-3" data-test="weekdays">
        <div class="form-label">{{ t("Repeats on") }}</div>
        <BFormCheckbox
          v-for="day in weekdayOptions"
          :id="id(`weekday-${day.value}`)"
          :key="day.value"
          inline
          :model-value="value.weekdays.includes(day.value)"
          @update:model-value="toggleWeekday(day.value, Boolean($event))"
        >
          {{ day.text }}
        </BFormCheckbox>
      </div>

      <div v-if="hasDayOptions" class="mb-3" data-test="day-options">
        <div class="d-flex flex-wrap align-items-center gap-2 mb-2">
          <BFormRadio
            :id="id('dayofmonth')"
            :model-value="value.monthlyType"
            value="DAYOFMONTH"
            :name="id('monthlytype')"
            @update:model-value="value = { ...value, monthlyType: 'DAYOFMONTH' }"
          >
            {{ t("Day of month") }}
          </BFormRadio>
          <BFormSelect
            :id="id('monthday')"
            v-model.number="value.monthDay"
            :options="dayOptions"
            size="sm"
            class="w-auto"
            :disabled="value.monthlyType !== 'DAYOFMONTH'"
          />
          <BFormSelect
            v-if="value.freq === 'YEARLY'"
            :id="id('dayofmonth-month')"
            v-model.number="value.month"
            :options="monthOptions"
            size="sm"
            class="w-auto"
            :disabled="value.monthlyType !== 'DAYOFMONTH'"
          />
        </div>
        <div class="d-flex flex-wrap align-items-center gap-2">
          <BFormRadio
            :id="id('weekdayofmonth')"
            :model-value="value.monthlyType"
            value="WEEKDAYOFMONTH"
            :name="id('monthlytype')"
            @update:model-value="value = { ...value, monthlyType: 'WEEKDAYOFMONTH' }"
          >
            {{ t("Weekday of month") }}
          </BFormRadio>
          <BFormSelect
            :id="id('weekdayindex')"
            v-model="value.weekdayIndex"
            :options="indexOptions"
            size="sm"
            class="w-auto"
            :disabled="value.monthlyType !== 'WEEKDAYOFMONTH'"
          />
          <BFormSelect
            :id="id('weekday')"
            v-model="value.weekday"
            :options="weekdayOptions"
            size="sm"
            class="w-auto"
            :disabled="value.monthlyType !== 'WEEKDAYOFMONTH'"
          />
          <BFormSelect
            v-if="value.freq === 'YEARLY'"
            :id="id('weekdayofmonth-month')"
            v-model.number="value.month"
            :options="monthOptions"
            size="sm"
            class="w-auto"
            :disabled="value.monthlyType !== 'WEEKDAYOFMONTH'"
          />
        </div>
      </div>

      <fieldset class="mb-3" data-test="end">
        <legend class="form-label fs-6">{{ t("End of recurrence") }}</legend>
        <div class="d-flex align-items-center gap-2 mb-2">
          <BFormRadio
            :id="id('end-until')"
            :model-value="value.end.type"
            value="until"
            :name="id('end')"
            @update:model-value="setEndType('until')"
          >
            {{ t("Until") }}
          </BFormRadio>
          <BFormInput
            :id="id('until')"
            type="date"
            size="sm"
            class="w-auto"
            :disabled="value.end.type !== 'until'"
            :model-value="value.end.type === 'until' ? value.end.until : ''"
            @update:model-value="$event && (value = { ...value, end: { type: 'until', until: String($event) } })"
          />
        </div>
        <div class="d-flex align-items-center gap-2 mb-2">
          <BFormRadio
            :id="id('end-count')"
            :model-value="value.end.type"
            value="count"
            :name="id('end')"
            @update:model-value="setEndType('count')"
          >
            {{ t("Ends after") }}
          </BFormRadio>
          <div class="input-group input-group-sm w-auto">
            <BFormInput
              :id="id('count')"
              type="number"
              min="1"
              style="max-width: 6rem"
              :disabled="value.end.type !== 'count'"
              :model-value="value.end.type === 'count' ? value.end.count : ''"
              @update:model-value="setCount(String($event))"
            />
            <span class="input-group-text">{{ t("occurrence(s)") }}</span>
          </div>
        </div>
        <BFormRadio
          :id="id('end-never')"
          :model-value="value.end.type"
          value="never"
          :name="id('end')"
          @update:model-value="setEndType('never')"
        >
          {{ t("Never") }}
        </BFormRadio>
      </fieldset>

      <div data-test="occurrences">
        <div class="form-label d-flex align-items-center gap-2">
          {{ t("Selected dates") }}
          <BSpinner v-if="previewLoading" small />
        </div>
        <div v-if="previewError" class="text-danger small mb-2" role="alert">{{ previewError }}</div>
        <ul class="list-group list-group-flush mb-2">
          <li
            v-for="occurrence in occurrences"
            :key="`${occurrence.type}-${occurrence.date}`"
            class="list-group-item d-flex justify-content-between align-items-center px-0 py-1"
            :class="{ 'text-decoration-line-through text-secondary': occurrence.type === 'exdate' }"
            data-test="occurrence"
          >
            <span>
              {{ formatDate(fromDateTime(occurrence.date), locale) }}
              <span v-if="occurrence.type === 'rdate'" class="badge text-bg-info ms-1">{{ t("Added") }}</span>
            </span>
            <BButton
              v-if="occurrence.type !== 'start'"
              size="sm"
              variant="link"
              class="p-0"
              data-test="toggle"
              @click="toggleOccurrence(occurrence)"
            >
              {{
                occurrence.type === "exdate"
                  ? t("Include")
                  : occurrence.type === "rdate"
                    ? t("Remove")
                    : t("Exclude")
              }}
            </BButton>
          </li>
        </ul>
        <BButton
          v-if="hasMore"
          size="sm"
          variant="outline-secondary"
          class="mb-2"
          data-test="more"
          @click="loadPreview(batchStart + 10)"
        >
          {{ t("More") }}
        </BButton>
        <div class="input-group input-group-sm w-auto">
          <BFormInput :id="id('add-date')" v-model="addDate" type="date" style="max-width: 12rem" />
          <BButton variant="outline-secondary" :disabled="!addDate" data-test="add-date" @click="addRdate">
            <i class="fa fa-calendar-plus"></i> {{ t("Add date") }}
          </BButton>
        </div>
      </div>
    </template>

    <template #footer>
      <BButton
        v-if="rule"
        variant="outline-danger"
        class="me-auto"
        data-test="remove-recurrence"
        @click="remove"
      >
        {{ t("Remove recurrence") }}
      </BButton>
      <BButton variant="secondary" data-test="cancel" @click="show = false">{{ t("Cancel") }}</BButton>
      <BButton v-if="raw === null" variant="primary" data-test="apply" @click="apply">{{ t("Save") }}</BButton>
    </template>
  </BModal>
</template>
