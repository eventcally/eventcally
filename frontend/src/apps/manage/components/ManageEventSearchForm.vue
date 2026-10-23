<script setup lang="ts">
import { ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppTypeahead from "@/shared/AppTypeahead.vue";
import LocationFilter from "@/shared/LocationFilter.vue";
import { type ManageEventFilter, emptyFilter, hasExtendedFilter } from "../manageEventQuery";

type Options = components["schemas"]["ManageEventListOptions"];
type Ref = { id: number; name: string };

const props = defineProps<{
  organizationId: number;
  filter: ManageEventFilter;
  options: Options;
  /** The names of a preselected organizer / place (echoed by the list). */
  organizer: Ref | null;
  eventPlace: Ref | null;
}>();
const emit = defineEmits<{ search: [filter: ManageEventFilter] }>();

const { t } = useI18n();

// Edits happen on a copy; they only take effect on "Find events".
const draft = ref<ManageEventFilter>({ ...props.filter });
const organizer = ref<Ref | null>(null);
const eventPlace = ref<Ref | null>(null);
const extended = ref(hasExtendedFilter(props.filter));

watch(
  () => [props.filter, props.organizer, props.eventPlace] as const,
  () => {
    draft.value = { ...props.filter };
    organizer.value = props.organizer?.id === props.filter.organizer_id ? props.organizer : null;
    eventPlace.value =
      props.eventPlace?.id === props.filter.event_place_id ? props.eventPlace : null;
  },
  { immediate: true },
);

watch(
  () => hasExtendedFilter(props.filter),
  (value) => {
    if (value) extended.value = true;
  },
);

function setOrganizer(value: Ref | null) {
  organizer.value = value;
  draft.value.organizer_id = value?.id ?? null;
}

function setEventPlace(value: Ref | null) {
  eventPlace.value = value;
  draft.value.event_place_id = value?.id ?? null;
}

async function fetchOrganizers(keyword: string): Promise<Ref[]> {
  const { data } = await api.GET("/bff/manage/organizations/{id}/event-organizers", {
    params: { path: { id: props.organizationId }, query: { keyword } },
  });
  return data?.items ?? [];
}

async function fetchEventPlaces(keyword: string): Promise<Ref[]> {
  const { data } = await api.GET("/bff/manage/organizations/{id}/event-places", {
    params: { path: { id: props.organizationId }, query: { keyword } },
  });
  return data?.items ?? [];
}

function submit() {
  emit("search", { ...draft.value, page: 1 });
}

function reset() {
  emit("search", emptyFilter({ date_from: props.options.default_date_from }));
}
</script>

<template>
  <form class="my-4" autocomplete="off" @submit.prevent="submit">
    <div class="row g-2 mb-3">
      <label class="col-sm-2 col-form-label" for="keyword">{{ t("Keyword") }}</label>
      <div class="col-sm-10">
        <input
          id="keyword"
          v-model="draft.keyword"
          type="text"
          class="form-control"
          maxlength="255"
        />
      </div>
    </div>

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
      <label class="col-sm-2 col-form-label" for="sort">{{ t("Sort") }}</label>
      <div class="col-sm-10">
        <select id="sort" v-model="draft.sort" class="form-select">
          <option value="min_start">{{ t("Earliest start first") }}</option>
          <option value="-last_modified_at">{{ t("Last modified first") }}</option>
          <option value="-created_at">{{ t("Newest first") }}</option>
        </select>
      </div>
    </div>

    <div v-show="extended" id="extended_search_form" data-test="extended">
      <div class="row g-2 mb-3">
        <label class="col-sm-2 col-form-label" for="category_id">{{ t("Categories") }}</label>
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
        <label class="col-sm-2 col-form-label" for="internal_tag">{{ t("Internal tags") }}</label>
        <div class="col-sm-10">
          <input
            id="internal_tag"
            v-model="draft.internal_tag"
            type="text"
            class="form-control"
            maxlength="255"
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
            :placeholder="t('Enter organizer')"
            @update:model-value="setOrganizer"
          />
        </div>
      </div>

      <div class="row g-2 mb-3">
        <label class="col-sm-2 col-form-label" for="event_place_id">{{ t("Place") }}</label>
        <div class="col-sm-10">
          <AppTypeahead
            :model-value="eventPlace"
            input-id="event_place_id"
            :fetch="fetchEventPlaces"
            :placeholder="t('Place')"
            @update:model-value="setEventPlace"
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
            v-model:coordinate="draft.radius_coordinate"
            v-model:name="draft.radius_location_name"
            v-model:distance="draft.radius_distance"
            :distances="options.distances"
            scope="manage"
          />
        </div>
      </div>

      <div class="row g-2 mb-3">
        <label class="col-sm-2 col-form-label" for="status">{{ t("Status") }}</label>
        <div class="col-sm-10">
          <select id="status" v-model="draft.status" class="form-select">
            <option :value="null">{{ t("All") }}</option>
            <option v-for="s in options.statuses" :key="s.value" :value="s.value">
              {{ s.label }}
            </option>
          </select>
        </div>
      </div>

      <div class="row g-2 mb-3">
        <label class="col-sm-2 col-form-label" for="public_status">{{ t("Public status") }}</label>
        <div class="col-sm-10">
          <select id="public_status" v-model="draft.public_status" class="form-select">
            <option :value="null">{{ t("All") }}</option>
            <option v-for="s in options.public_statuses" :key="s.value" :value="s.value">
              {{ s.label }}
            </option>
          </select>
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
        <label class="col-sm-2 col-form-label" for="is_recurring">{{ t("Recurring event") }}</label>
        <div class="col-sm-10">
          <select id="is_recurring" v-model="draft.is_recurring" class="form-select">
            <option value="">{{ t("All") }}</option>
            <option value="1">{{ t("Yes") }}</option>
            <option value="0">{{ t("No") }}</option>
          </select>
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
      <button type="button" class="btn btn-outline-secondary mt-1 me-1" data-test="reset" @click="reset">
        {{ t("Reset") }}
      </button>
    </p>
  </form>
</template>
