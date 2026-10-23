<script setup lang="ts">
import {
  BDropdown,
  BDropdownDivider,
  BDropdownItem,
  BOverlay,
  BTable,
  type TableFieldRaw,
} from "bootstrap-vue-next";
import { computed, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { useRoute, useRouter } from "vue-router";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";
import AppPager from "@/shared/AppPager.vue";
import { boot } from "@/shared/boot";
import { formatDate, formatStart } from "@/shared/format";
import { manage, publicPages } from "@/shared/legacy";
import { useNotify } from "@/shared/notify";
import { takeFlash } from "../flash";
import ManageEventSearchForm from "../components/ManageEventSearchForm.vue";
import {
  type ManageEventFilter,
  fromRouteQuery,
  toBffParams,
  toRouteQuery,
} from "../manageEventQuery";

type Options = components["schemas"]["ManageEventListOptions"];
type Page = components["schemas"]["ManageEventPage"];

const props = defineProps<{ organizationId: number }>();

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const notify = useNotify();

const options = ref<Options | null>(null);
const page = ref<Page | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);

const defaults = computed(() => ({ date_from: options.value?.default_date_from ?? "" }));
const filter = computed<ManageEventFilter | null>(() =>
  options.value ? fromRouteQuery(route.query, defaults.value) : null,
);

const fields = computed<TableFieldRaw[]>(() => [
  { key: "start", label: t("Start") },
  { key: "is_recurring", label: t("Recurring event") },
  { key: "number_of_dates", label: t("Event dates") },
  { key: "name", label: t("Name") },
  { key: "organizer_name", label: t("Organizer") },
  { key: "place_label", label: t("Place") },
  { key: "category_names", label: t("Categories") },
  { key: "tags", label: t("Tags") },
  { key: "internal_tags", label: t("Internal tags") },
  { key: "status", label: t("Status") },
  { key: "public_status", label: t("Public status") },
  { key: "has_photo", label: t("Photo") },
  { key: "number_of_references", label: t("References") },
  { key: "number_of_reference_requests", label: t("Reference requests") },
  { key: "last_modified_at", label: t("Last modified at") },
]);

// The caret stays with the last word of a wrapping name.
const nameHead = (name: string) => name.slice(0, name.lastIndexOf(" ") + 1);
const nameTail = (name: string) => name.slice(name.lastIndexOf(" ") + 1);

const publicStatusVariant: Record<string, string> = {
  draft: "light",
  published: "success",
  planned: "secondary",
};
const statusVariant = (name: string) =>
  name === "scheduled" ? "success" : name === "cancelled" ? "danger" : "warning";

function statusLabel(list: { name: string; label: string }[] | undefined, name: string) {
  return list?.find((s) => s.name === name)?.label ?? name;
}

async function loadOptions() {
  const { data, error: err } = await api.GET("/bff/manage/organizations/{id}/events/options", {
    params: { path: { id: props.organizationId } },
  });
  if (data) options.value = data;
  else error.value = err?.message ?? t("Error");
  return Boolean(data);
}

async function search() {
  if (!filter.value) return;
  loading.value = true;
  error.value = null;
  const { data, error: err } = await api.GET("/bff/manage/organizations/{id}/events", {
    params: { path: { id: props.organizationId }, query: toBffParams(filter.value) },
  });
  if (data) page.value = data;
  else {
    page.value = null;
    error.value = err?.message ?? t("Error");
  }
  loading.value = false;
}

function onSearch(next: ManageEventFilter) {
  const query = toRouteQuery(next, defaults.value);
  const same =
    JSON.stringify(query) ===
    JSON.stringify(toRouteQuery(filter.value ?? next, defaults.value));
  // An unchanged filter does not change the route, so search directly.
  if (same) search();
  else router.push({ name: "manage-events", query });
}

const currentPage = computed({
  get: () => filter.value?.page ?? 1,
  set: (value: number) => {
    if (filter.value) onSearch({ ...filter.value, page: value });
  },
});

watch(
  () => route.query,
  () => {
    if (options.value) search();
  },
);

onMounted(async () => {
  const message = takeFlash();
  if (message) notify.success(message);
  if (await loadOptions()) await search();
});
</script>

<template>
  <div>
    <AppBreadcrumb :items="[{ label: t('Events') }]" />

    <div v-if="options?.can_write" class="my-4">
      <a :href="manage.eventCreate(organizationId)" class="btn btn-outline-secondary">
        <i class="fa fa-plus"></i> {{ t("Create event") }}
      </a>
    </div>

    <ManageEventSearchForm
      v-if="filter && options"
      :organization-id="organizationId"
      :filter="filter"
      :options="options"
      :organizer="page?.organizer ?? null"
      :event-place="page?.event_place ?? null"
      @search="onSearch"
    />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <BOverlay :show="loading">
      <BTable
        :items="page?.items ?? []"
        :fields="fields"
        show-empty
        :empty-text="t('No events found')"
        responsive
        stacked="sm"
        striped
        bordered
      >
        <template #head(is_recurring)><i class="fas fa-history" :title="t('Recurring event')"></i></template>
        <template #head(number_of_dates)><i class="fa fa-calendar-alt" :title="t('Event dates')"></i></template>
        <template #head(has_photo)><i class="fa fa-image" :title="t('Photo')"></i></template>
        <template #head(number_of_references)><i class="fa fa-share" :title="t('References')"></i></template>
        <template #head(number_of_reference_requests)><i class="fa fa-question" :title="t('Reference requests')"></i></template>
        <template #head(last_modified_at)><i class="fa fa-save" :title="t('Last modified at')"></i></template>

        <template #cell(start)="{ item }"
          ><span class="text-nowrap">{{
            formatStart(item.start, item.allday, boot.locale)
          }}</span></template
        >
        <template #cell(is_recurring)="{ item }">
          <i v-if="item.is_recurring" class="fa fa-check-circle" :title="t('Recurring event')"></i>
        </template>
        <template #cell(name)="{ item }">
          <BDropdown
            variant="link"
            no-caret
            toggle-class="p-0 border-0 text-start align-baseline"
            class="event-actions"
            teleport-to="body"
          >
            <template #button-content>
              {{ nameHead(item.name) }}<span class="text-nowrap">{{ nameTail(item.name) }}<i class="fa fa-caret-down ms-1"></i></span>
            </template>
            <BDropdownItem :href="publicPages.event(item.id)">{{ t("View") }}</BDropdownItem>
            <BDropdownItem :href="manage.eventUpdate(organizationId, item.id)">
              {{ t("Edit") }}
            </BDropdownItem>
            <BDropdownItem :href="manage.eventDelete(organizationId, item.id)">
              {{ t("Delete") }}
            </BDropdownItem>
            <BDropdownItem
              v-if="options?.can_request_reference"
              :href="manage.eventReferenceRequestCreate(organizationId, item.id)"
            >
              {{ t("Request reference") }}
            </BDropdownItem>
            <BDropdownDivider />
            <BDropdownItem :href="publicPages.eventActions(item.id)">{{ t("More") }}</BDropdownItem>
          </BDropdown>
        </template>
        <template #cell(category_names)="{ item }">{{ item.category_names.join(", ") }}</template>
        <template #cell(status)="{ item }">
          <span v-if="item.status" class="badge" :class="`text-bg-${statusVariant(item.status)}`">{{
            statusLabel(options?.statuses, item.status)
          }}</span>
        </template>
        <template #cell(public_status)="{ item }">
          <span class="badge" :class="`text-bg-${publicStatusVariant[item.public_status] ?? 'light'}`">{{
            statusLabel(options?.public_statuses, item.public_status)
          }}</span>
        </template>
        <template #cell(has_photo)="{ item }">
          <i v-if="item.has_photo" class="fa fa-check-circle" :title="t('Photo')"></i>
        </template>
        <template #cell(last_modified_at)="{ item }">{{ formatDate(item.last_modified_at, boot.locale) }}</template>
      </BTable>
    </BOverlay>

    <AppPager
      v-if="page && page.pages > 1"
      v-model:page="currentPage"
      :pages="page.pages"
      :total="page.total"
    />
  </div>
</template>
