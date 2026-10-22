<script setup lang="ts">
import { BModal } from "bootstrap-vue-next";
import { ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { emptyFilter, type PlanningFilter } from "../planning";
import LocationFilter from "./LocationFilter.vue";

const props = defineProps<{
  categories: { id: number; name: string }[];
  distances: { value: number; label: string }[];
  filter: PlanningFilter;
}>();
const visible = defineModel<boolean>({ default: false });
const emit = defineEmits<{ apply: [filter: PlanningFilter] }>();

const { t } = useI18n();
// Edits happen on a copy; they only take effect on "Refresh".
const draft = ref<PlanningFilter>(emptyFilter());

watch(
  visible,
  (open) => {
    if (open) draft.value = { ...props.filter, category_id: [...props.filter.category_id] };
  },
  { immediate: true },
);

function refresh() {
  emit("apply", { ...draft.value, category_id: [...draft.value.category_id] });
  visible.value = false;
}
</script>

<template>
  <BModal v-model="visible" :title="t('Filter')" size="lg">
    <div class="mb-3">
      <label class="form-label">{{ t("Categories") }}</label>
      <div>
        <div v-for="category in categories" :key="category.id" class="form-check form-check-inline">
          <input
            :id="`planning-category-${category.id}`"
            v-model="draft.category_id"
            class="form-check-input"
            type="checkbox"
            :value="category.id"
          />
          <label class="form-check-label" :for="`planning-category-${category.id}`">{{
            category.name
          }}</label>
        </div>
      </div>
    </div>

    <div class="mb-3">
      <label class="form-label" for="planning-postal-code">{{ t("Postal code") }}</label>
      <input
        id="planning-postal-code"
        v-model="draft.postal_code"
        type="text"
        class="form-control"
        maxlength="255"
      />
    </div>

    <div class="mb-3">
      <label class="form-label">{{ t("Location") }}</label>
      <LocationFilter
        v-model:coordinate="draft.coordinate"
        v-model:name="draft.location_name"
        v-model:distance="draft.distance"
        :distances="distances"
      />
    </div>

    <div class="mb-3">
      <label class="form-label" for="planning-participants">{{
        t("Min. expected number of participants")
      }}</label>
      <input
        id="planning-participants"
        v-model.number="draft.expected_participants_min"
        type="number"
        min="0"
        class="form-control"
      />
    </div>

    <div class="form-check">
      <input
        id="planning-exclude-recurring"
        v-model="draft.exclude_recurring"
        class="form-check-input"
        type="checkbox"
      />
      <label class="form-check-label" for="planning-exclude-recurring">{{
        t("Exclude recurring events")
      }}</label>
    </div>

    <template #footer>
      <button type="button" class="btn btn-outline-secondary" @click="visible = false">
        {{ t("Close") }}
      </button>
      <button type="button" class="btn btn-primary" data-test="refresh" @click="refresh">
        {{ t("Refresh") }}
      </button>
    </template>
  </BModal>
</template>
