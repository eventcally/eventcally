<script setup lang="ts">
import { ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppTypeahead from "@/shared/AppTypeahead.vue";
import LocationFilter from "@/shared/LocationFilter.vue";
import { type EventDateFilter, hasExtendedFilter } from "../eventDateQuery";

type Options = components["schemas"]["EventDateSearchOptions"];
type Ref = { id: number; name: string };

const props = defineProps<{ filter: EventDateFilter; options: Options }>();
const emit = defineEmits<{ search: [filter: EventDateFilter]; "toggle-map": [] }>();

const { t } = useI18n();

// Edits happen on a copy; they only take effect on "Find events".
const draft = ref<EventDateFilter>({ ...props.filter });
const organization = ref<Ref | null>(null);
const organizer = ref<Ref | null>(null);
const extended = ref(hasExtendedFilter(props.filter));

function syncRefs() {
  organization.value =
    props.options.organization && props.options.organization.id === props.filter.admin_unit_id
      ? props.options.organization
      : null;
  organizer.value =
    props.options.organizer && props.options.organizer.id === props.filter.organizer_id
      ? props.options.organizer
      : null;
}

watch(
  () => [props.filter, props.options] as const,
  () => {
    draft.value = { ...props.filter };
    syncRefs();
  },
  { immediate: true },
);

watch(
  () => hasExtendedFilter(props.filter),
  (value) => {
    if (value) extended.value = true;
  },
);

function setOrganization(value: Ref | null) {
  organization.value = value;
  draft.value.admin_unit_id = value?.id ?? null;
  // An organizer belongs to one organization.
  setOrganizer(null);
}

function setOrganizer(value: Ref | null) {
  organizer.value = value;
  draft.value.organizer_id = value?.id ?? null;
}

async function fetchOrganizations(keyword: string): Promise<Ref[]> {
  const { data } = await api.GET("/bff/public/organizations", {
    params: { query: { keyword, per_page: 5 } },
  });
  return (data?.items ?? []).map((o) => ({ id: o.id, name: o.name }));
}

async function fetchOrganizers(keyword: string): Promise<Ref[]> {
  if (!organization.value) return [];
  const { data } = await api.GET("/bff/public/organizations/{id}/organizers", {
    params: { path: { id: organization.value.id }, query: { keyword, per_page: 5 } },
  });
  return (data?.items ?? []).map((o) => ({ id: o.id, name: o.name }));
}

function submit() {
  emit("search", { ...draft.value, page: 1 });
}
</script>

<template>
  <form class="my-4" autocomplete="off" @submit.prevent="submit">
    <div class="row g-2 mb-3">
      <label class="col-sm-2 col-form-label" for="date_from">{{ t("Date") }}</label>
      <div class="col-sm-5">
        <div class="input-group">
          <label class="input-group-text" for="date_from">{{ t("From") }}</label>
          <input id="date_from" v-model="draft.date_from" type="date" class="form-control" />
        </div>
      </div>
      <div class="col-sm-5">
        <div class="input-group">
          <label class="input-group-text" for="date_to">{{ t("to") }}</label>
          <input id="date_to" v-model="draft.date_to" type="date" class="form-control" />
        </div>
      </div>
    </div>

    <div class="row g-2 mb-3">
      <label class="col-sm-2 col-form-label" for="keyword">{{ t("Keyword") }}</label>
      <div class="col-sm-10">
        <input id="keyword" v-model="draft.keyword" type="text" class="form-control" maxlength="255" />
      </div>
    </div>

    <div v-show="extended" id="extended_search_form" data-test="extended">
      <div class="row g-2 mb-3">
        <label class="col-sm-2 col-form-label" for="category_id">{{ t("Category") }}</label>
        <div class="col-sm-10">
          <select id="category_id" v-model="draft.category_id" class="form-select">
            <option :value="null"></option>
            <option v-for="c in options.categories" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
      </div>

      <div class="row g-2 mb-3">
        <label class="col-sm-2 col-form-label" for="tag">{{ t("Tags") }}</label>
        <div class="col-sm-10">
          <input id="tag" v-model="draft.tag" type="text" class="form-control" maxlength="255" />
        </div>
      </div>

      <div class="row g-2 mb-3">
        <label class="col-sm-2 col-form-label" for="admin_unit_id">{{ t("Organization") }}</label>
        <div class="col-sm-10">
          <AppTypeahead
            :model-value="organization"
            input-id="admin_unit_id"
            :fetch="fetchOrganizations"
            @update:model-value="setOrganization"
            :placeholder="t('Enter organization')"
          />
        </div>
      </div>

      <div class="row g-2 mb-3">
        <label class="col-sm-2 col-form-label" for="organizer_id">{{ t("Organizer") }}</label>
        <div class="col-sm-10">
          <AppTypeahead
            :model-value="organizer"
            input-id="organizer_id"
            :fetch="fetchOrganizers"
            @update:model-value="setOrganizer"
            :disabled="!organization"
            :placeholder="t('Enter organizer')"
          />
        </div>
      </div>

      <div class="row g-2 mb-3">
        <label class="col-sm-2 col-form-label" for="postal_code">{{ t("Postal code") }}</label>
        <div class="col-sm-10">
          <input
            id="postal_code"
            v-model="draft.postal_code"
            type="text"
            class="form-control"
            maxlength="255"
          />
        </div>
      </div>

      <div class="row g-2 mb-3">
        <span class="col-sm-2 col-form-label">{{ t("Radius") }}</span>
        <div class="col-sm-10">
          <LocationFilter
            v-model:coordinate="draft.coordinate"
            v-model:name="draft.location"
            v-model:distance="draft.distance"
            :distances="options.distances"
            scope="public"
          />
        </div>
      </div>

      <div class="row g-2 mb-3">
        <label class="col-sm-2 col-form-label" for="created_at_from">{{ t("Created at") }}</label>
        <div class="col-sm-5">
          <div class="input-group">
            <label class="input-group-text" for="created_at_from">{{ t("From") }}</label>
            <input
              id="created_at_from"
              v-model="draft.created_at_from"
              type="date"
              class="form-control"
            />
          </div>
        </div>
        <div class="col-sm-5">
          <div class="input-group">
            <label class="input-group-text" for="created_at_to">{{ t("to") }}</label>
            <input
              id="created_at_to"
              v-model="draft.created_at_to"
              type="date"
              class="form-control"
            />
          </div>
        </div>
      </div>

      <div class="row g-2 mb-3">
        <label class="col-sm-2 col-form-label" for="sort">{{ t("Sort") }}</label>
        <div class="col-sm-10">
          <select id="sort" v-model="draft.sort" class="form-select">
            <option v-for="s in options.sorts" :key="s.value" :value="s.value">
              {{ t(s.label) }}
            </option>
          </select>
        </div>
      </div>

      <div class="row g-2 mb-3">
        <div class="col-sm-10 offset-sm-2">
          <div class="form-check">
            <input
              id="exclude_recurring"
              v-model="draft.exclude_recurring"
              type="checkbox"
              class="form-check-input"
            />
            <label class="form-check-label" for="exclude_recurring">{{
              t("Exclude recurring events")
            }}</label>
          </div>
        </div>
      </div>

      <div v-if="options.referencing_organization" class="row g-2 mb-3">
        <div class="col-sm-10 offset-sm-2">
          <div class="form-check">
            <input
              id="not_referenced"
              v-model="draft.not_referenced"
              type="checkbox"
              class="form-check-input"
              data-test="not-referenced"
            />
            <label class="form-check-label" for="not_referenced">{{
              t("Show unreferenced events only")
            }}</label>
          </div>
        </div>
      </div>
    </div>

    <p class="mb-0">
      <button type="submit" class="btn btn-primary mt-1 me-1">{{ t("Find events") }}</button>
      <button
        id="toggle-search-btn"
        type="button"
        class="btn btn-secondary mt-1 me-1"
        :aria-expanded="extended"
        aria-controls="extended_search_form"
        @click="extended = !extended"
      >
        {{ t("More filters") }}
      </button>
      <button
        id="toggle-map-btn"
        type="button"
        class="btn btn-outline-secondary mt-1 me-1"
        @click="emit('toggle-map')"
      >
        <i class="fa fa-map"></i> {{ t("Map view") }}
      </button>
    </p>
  </form>
</template>
