<script setup lang="ts">
import { BOverlay, BTable, type TableFieldRaw } from "bootstrap-vue-next";
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppPager from "@/shared/AppPager.vue";
import { boot } from "@/shared/boot";
import CalendarAssignModal from "@/shared/CalendarAssignModal.vue";
import ConfirmModal from "@/shared/ConfirmModal.vue";
import { formatDate } from "@/shared/format";
import { LINK_CLOSE, LINK_OPEN } from "@/shared/instruction";
import InstructionText from "@/shared/InstructionText.vue";
import { publicPages } from "@/shared/legacy";
import ManageBreadcrumb from "@/shared/ManageBreadcrumb.vue";
import RowActions, { type RowAction } from "@/shared/RowActions.vue";
import { useConfirmAction } from "@/shared/useConfirmAction";
import { useFlashNotice } from "@/shared/useFlashNotice";
import { usePagedList } from "@/shared/usePagedList";
import EventReferenceRatingModal from "../components/EventReferenceRatingModal.vue";

type Page = components["schemas"]["IncomingEventReferenceListPage"];
type Item = Page["items"][number];

const props = defineProps<{ organizationId: number }>();

const { t } = useI18n();

useFlashNotice();

const { page, loading, error, currentPage, load } = usePagedList<Page>(
  (current) =>
    api.GET("/bff/manage/organizations/{id}/incoming-event-references", {
      params: { path: { id: props.organizationId }, query: { page: current } },
    }),
  "incoming-event-references",
  t("Error"),
);

const instruction = computed(() =>
  t(
    "Here you can find events from other organizations that you referenced. To reference an event, select %(reference_open)s%(reference_title)s%(reference_close)s on an event page that you can find through the %(search_open)ssearch%(search_close)s.",
    {
      reference_open: '"',
      reference_close: '"',
      reference_title: t("Reference event"),
      search_open: LINK_OPEN,
      search_close: LINK_CLOSE,
    },
  ),
);

const modelName = computed(() => t("Incoming reference"));
const objectTitle = (item: Item | null) => (item ? `${t("Event reference")} ${item.id}` : "");

async function reload() {
  await load();
  // The deleted reference may have been the last one of the page.
  if (page.value?.items.length === 0 && currentPage.value > 1) {
    currentPage.value = currentPage.value - 1;
  }
}

const confirm = useConfirmAction<Item>({
  call: (item) =>
    api.POST("/bff/manage/organizations/{id}/incoming-event-references/{reference_id}/delete", {
      params: { path: { id: props.organizationId, reference_id: item.id } },
      body: { inline: true },
    }),
  onDone: reload,
});

const rating = ref<Item | null>(null);
const showRating = ref(false);

const fields = computed<TableFieldRaw[]>(() => [
  { key: "event_name", label: t("Event") },
  { key: "organization_name", label: t("Organization") },
  { key: "created_at", label: t("Created at") },
]);

const showCalendars = ref(false);
const calendarEventId = ref<number | null>(null);

function actions(item: Item): RowAction[] {
  const result: RowAction[] = [
    {
      title: t("View"),
      to: {
        name: "incoming-event-reference",
        params: { organizationId: props.organizationId, id: item.id },
      },
    },
  ];

  if (page.value?.can_write) {
    result.push(
      {
        title: t("Edit"),
        onClick: () => {
          rating.value = item;
          showRating.value = true;
        },
      },
      { title: t("Delete"), onClick: () => confirm.open(item) },
    );
  }

  if (page.value?.can_assign_calendars) {
    result.push({
      title: t("Calendars…"),
      onClick: () => {
        calendarEventId.value = item.event_id;
        showCalendars.value = true;
      },
    });
  }

  result.push({ title: t("View event"), href: publicPages.event(item.event_id) });
  return result;
}
</script>

<template>
  <div>
    <ManageBreadcrumb
      :organization-id="organizationId"
      :items="[{ label: t('Incoming references') }]"
    />

    <InstructionText :text="instruction" :href="publicPages.eventDatesSearch" />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <BOverlay :show="loading">
      <BTable
        v-if="page && page.items.length"
        :items="page.items"
        :fields="fields"
        thead-class="fw-bold"
        responsive
        small
        striped
        bordered
        hover
      >
        <template #cell(event_name)="{ item }">
          <RowActions :label="item.event_name" :actions="actions(item)" />
        </template>
        <template #cell(created_at)="{ item }">{{
          formatDate(item.created_at, boot.locale)
        }}</template>
      </BTable>
    </BOverlay>

    <AppPager
      v-if="page && page.total > 0"
      v-model:page="currentPage"
      :pages="page.pages"
      :total="page.total"
    />

    <CalendarAssignModal
      v-if="page?.can_assign_calendars"
      v-model="showCalendars"
      :organization-id="organizationId"
      :event-id="calendarEventId"
    />

    <ConfirmModal
      v-model="confirm.show.value"
      :title="t('Delete %(model_display_name)s', { model_display_name: modelName })"
      :confirm-title="t('Delete reference')"
      :instruction="
        t('Do you want to delete \'%(object_title)s\'?', {
          object_title: objectTitle(confirm.item.value),
        })
      "
      :busy="confirm.busy.value"
      :error="confirm.error.value"
      @submit="confirm.submit"
    />

    <EventReferenceRatingModal
      v-model="showRating"
      :organization-id="organizationId"
      :reference-id="rating?.id ?? null"
      :rating="rating?.rating ?? null"
      :choices="page?.rating_choices ?? []"
      @saved="load"
    />
  </div>
</template>
