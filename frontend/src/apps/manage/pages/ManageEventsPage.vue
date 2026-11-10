<script setup lang="ts">
import {
  BButtonGroup,
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
import CalendarAssignModal from "@/shared/CalendarAssignModal.vue";
import ConfirmModal from "@/shared/ConfirmModal.vue";
import { formatDate, formatStart } from "@/shared/format";
import { manage, publicPages } from "@/shared/legacy";
import { useNotify } from "@/shared/notify";
import { takeFlash } from "@/shared/flash";
import { useConfirmAction } from "@/shared/useConfirmAction";
import EventDeleteModal from "../components/EventDeleteModal.vue";
import ManageEventCalendar from "../components/ManageEventCalendar.vue";
import type { CalendarView } from "../components/PlanningCalendar.vue";
import ManageEventSearchForm from "../components/ManageEventSearchForm.vue";
import {
  publicStatusVariant,
  statusLabel,
  statusVariant,
  type ReferenceTarget,
} from "../manageEventCalendar";
import {
  type ManageEventFilter,
  type ManageEventView,
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

const deleting = ref<number | null>(null);
const showDelete = ref(false);
const calendar = ref<InstanceType<typeof ManageEventCalendar> | null>(null);

const deleteReference = useConfirmAction<ReferenceTarget>({
  call: (target) =>
    api.POST("/bff/manage/organizations/{id}/incoming-event-references/{reference_id}/delete", {
      params: { path: { id: props.organizationId, reference_id: target.referenceId } },
      body: { inline: true },
    }),
  onDone: () => reload(),
});

const assigning = ref<number | null>(null);
const showCalendars = ref(false);

function askCalendars(id: number) {
  assigning.value = id;
  showCalendars.value = true;
}

function askDelete(id: number) {
  deleting.value = id;
  showDelete.value = true;
}

async function onDeleted(answer: { message: string }) {
  notify.success(answer.message);
  showDelete.value = false;
  await reload();
}

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

const isCalendar = computed(() => filter.value?.view === "calendar");

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

/** Reloads what the current view shows. */
async function reload() {
  if (isCalendar.value) await calendar.value?.reload();
  else await search();
}

function onSearch(next: ManageEventFilter) {
  const query = toRouteQuery(next, defaults.value);
  const same =
    JSON.stringify(query) ===
    JSON.stringify(toRouteQuery(filter.value ?? next, defaults.value));
  // An unchanged filter does not change the route, so reload directly.
  if (same) reload();
  else router.push({ name: "manage-events", query });
}

function setView(view: ManageEventView) {
  if (!filter.value || filter.value.view === view) return;
  // The calendar opens at the list's start date; the list keeps its own date range.
  onSearch({
    ...filter.value,
    view,
    page: 1,
    calendar_view: "dayGridMonth",
    calendar_date: view === "calendar" ? filter.value.date_from : "",
  });
}

/** The calendar moved: keep its position in the URL without a history entry. */
function onPosition(position: { view: CalendarView; date: string }) {
  if (!filter.value) return;
  const query = toRouteQuery(
    { ...filter.value, calendar_view: position.view, calendar_date: position.date },
    defaults.value,
  );
  if (JSON.stringify(query) === JSON.stringify(toRouteQuery(filter.value, defaults.value))) return;
  router.replace({ name: "manage-events", query });
}

const currentPage = computed({
  get: () => filter.value?.page ?? 1,
  set: (value: number) => {
    if (filter.value) onSearch({ ...filter.value, page: value });
  },
});

// The calendar loads by itself (on its range and on filter changes).
watch(
  () => route.query,
  () => {
    if (options.value && !isCalendar.value) search();
  },
);

onMounted(async () => {
  const message = takeFlash();
  if (message) notify.success(message);
  if ((await loadOptions()) && !isCalendar.value) await search();
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

    <div v-if="filter" class="d-flex justify-content-end mb-3">
      <BButtonGroup :aria-label="t('View')">
        <button
          type="button"
          class="btn btn-outline-secondary"
          :class="{ active: !isCalendar }"
          :aria-pressed="!isCalendar"
          data-test="view-list"
          @click="setView('list')"
        >
          <i class="fa fa-list me-1"></i>{{ t("List") }}
        </button>
        <button
          type="button"
          class="btn btn-outline-secondary"
          :class="{ active: isCalendar }"
          :aria-pressed="isCalendar"
          data-test="view-calendar"
          @click="setView('calendar')"
        >
          <i class="fa fa-calendar-alt me-1"></i>{{ t("Calendar") }}
        </button>
      </BButtonGroup>
    </div>

    <ManageEventCalendar
      v-if="isCalendar && filter && options"
      ref="calendar"
      :organization-id="organizationId"
      :filter="filter"
      :options="options"
      @position="onPosition"
      @delete="askDelete"
      @delete-reference="deleteReference.open"
    />

    <template v-else>
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
              <template v-if="item.is_reference && item.reference_id">
                <BDropdownItem
                  :to="{
                    name: 'incoming-event-reference',
                    params: { organizationId, id: item.reference_id },
                  }"
                  data-test="view-reference"
                >
                  {{ t("View reference") }}
                </BDropdownItem>
                <BDropdownItem
                  v-if="options?.can_write_references"
                  data-test="delete-reference"
                  @click="deleteReference.open({ referenceId: item.reference_id, name: item.name })"
                >
                  {{ t("Delete reference") }}
                </BDropdownItem>
              </template>
              <template v-else-if="item.is_own !== false">
                <BDropdownItem :href="manage.eventUpdate(organizationId, item.id)">
                  {{ t("Edit") }}
                </BDropdownItem>
                <BDropdownItem @click="askDelete(item.id)">
                  {{ t("Delete") }}
                </BDropdownItem>
                <BDropdownItem
                  v-if="options?.can_request_reference"
                  :href="manage.eventReferenceRequestCreate(organizationId, item.id)"
                >
                  {{ t("Request reference") }}
                </BDropdownItem>
              </template>
              <BDropdownItem
                v-if="options?.can_write_calendars"
                data-test="assign-calendars"
                @click="askCalendars(item.id)"
              >
                {{ t("Calendars…") }}
              </BDropdownItem>
              <BDropdownDivider />
              <BDropdownItem :href="publicPages.eventActions(item.id)">{{ t("More") }}</BDropdownItem>
            </BDropdown>
            <div v-if="item.is_reference" class="small" data-test="reference">
              <span class="badge text-bg-info me-1">{{ t("Reference") }}</span>
              <span class="text-body-secondary">{{ item.organization_name }}</span>
            </div>
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
        v-if="page && page.total > 0"
        v-model:page="currentPage"
        :pages="page.pages"
        :total="page.total"
      />
    </template>

    <ConfirmModal
      v-model="deleteReference.show.value"
      :title="t('Delete %(model_display_name)s', { model_display_name: t('Incoming reference') })"
      :confirm-title="t('Delete reference')"
      :instruction="
        t('Do you want to delete \'%(object_title)s\'?', {
          object_title: deleteReference.item.value?.name ?? '',
        })
      "
      :busy="deleteReference.busy.value"
      :error="deleteReference.error.value"
      @submit="deleteReference.submit"
    />

    <CalendarAssignModal
      v-model="showCalendars"
      :organization-id="organizationId"
      :event-id="assigning"
      @saved="reload"
    />

    <EventDeleteModal
      v-model="showDelete"
      :organization-id="organizationId"
      :event-id="deleting"
      @deleted="onDeleted"
    />
  </div>
</template>
