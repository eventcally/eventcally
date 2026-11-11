<script setup lang="ts">
import { BOverlay } from "bootstrap-vue-next";
import { computed, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppPager from "@/shared/AppPager.vue";
import { boot } from "@/shared/boot";
import CalendarAssignModal from "@/shared/CalendarAssignModal.vue";
import IcalExportModal from "@/shared/IcalExportModal.vue";
import LinkifiedText from "@/shared/LinkifiedText.vue";
import { publicPages } from "@/shared/legacy";
import EventDateCard from "../components/EventDateCard.vue";

type PublicCalendar = components["schemas"]["PublicCalendar"];
type Page = components["schemas"]["PublicEventDatePage"];

const props = defineProps<{ id: number }>();

const { t } = useI18n();

const calendar = ref<PublicCalendar | null>(null);
const page = ref<Page | null>(null);
const currentPage = ref(1);
const loading = ref(false);
const loadError = ref<string | null>(null);
const icalVisible = ref(false);
const calendarOrganizationId = computed(() => calendar.value?.calendar_organization?.id ?? null);
const calendarEventId = ref<number | null>(null);
const showCalendars = ref(false);

function assignCalendars(eventId: number) {
  calendarEventId.value = eventId;
  showCalendars.value = true;
}

const searchUrl = computed(() => `${publicPages.eventDatesSearch}?calendar_id=${props.id}`);

async function loadCalendar() {
  loading.value = true;
  loadError.value = null;
  const { data, error } = await api.GET("/bff/public/calendars/{id}", {
    params: { path: { id: props.id } },
  });
  if (data) calendar.value = data;
  else loadError.value = error?.message ?? t("Error");
  loading.value = false;
}

async function loadDates() {
  const { data, error } = await api.GET("/bff/public/event-dates", {
    params: { query: { calendar_id: [props.id], page: currentPage.value } },
  });
  if (data) page.value = data;
  else loadError.value = error?.message ?? t("Error");
}

watch(currentPage, loadDates);

onMounted(async () => {
  await loadCalendar();
  if (calendar.value) await loadDates();
});
</script>

<template>
  <div>
    <div v-if="loadError" class="alert alert-danger" role="alert">{{ loadError }}</div>

    <BOverlay :show="loading">
      <div v-if="calendar">
        <div class="mb-4">
          <h1 class="my-0">
            {{ calendar.name }}
            <span v-if="calendar.private" class="badge text-bg-secondary fs-6 align-middle" data-test="private">{{
              t("Private")
            }}</span>
          </h1>
          <div class="text-muted mb-3">
            <a
              class="text-decoration-none"
              :href="publicPages.organization(calendar.organization.id)"
              data-test="organization"
              >{{ calendar.organization.name }}</a
            >
          </div>

          <p v-if="calendar.private" class="text-warning" data-test="private-notice">
            {{ t("This calendar is private.") }}
          </p>

          <div v-if="calendar.description" class="mb-3" style="white-space: pre-wrap" data-test="description">
            <LinkifiedText :text="calendar.description" />
          </div>

          <div class="d-flex flex-wrap gap-2">
            <button
              v-if="!calendar.private"
              type="button"
              class="btn btn-outline-secondary"
              data-test="subscribe"
              @click="icalVisible = true"
            >
              <i class="fa fa-fw me-1 fa-calendar"></i>{{ t("Subscribe") }}
            </button>
            <a class="btn btn-outline-secondary" :href="searchUrl" data-test="search">
              <i class="fa fa-fw me-1 fa-search"></i>{{ t("Search events") }}
            </a>
            <a
              v-if="calendar.manage_url"
              class="btn btn-outline-secondary"
              :href="calendar.manage_url"
              data-test="manage"
            >
              <i class="fa fa-fw me-1 fa-edit"></i>{{ t("Manage") }}
            </a>
          </div>

          <IcalExportModal v-if="!calendar.private" v-model="icalVisible" :url="calendar.ical_url" />
        </div>

        <div data-test="dates">
          <EventDateCard
            v-for="eventDate in page?.items ?? []"
            :key="eventDate.id"
            :event-date="eventDate"
            :locale="boot.locale"
            :can-assign-calendar="calendarOrganizationId !== null"
            @assign-calendar="assignCalendars"
          />
          <p
            v-if="page && page.items.length === 0"
            class="text-center text-secondary"
            data-test="empty"
          >
            {{ t("No upcoming events in this calendar") }}
          </p>
        </div>
        <AppPager
          v-if="page && page.total > 0"
          v-model:page="currentPage"
          :pages="page.pages"
          :total="page.total"
        />
        <CalendarAssignModal
          v-if="calendarOrganizationId !== null"
          v-model="showCalendars"
          :organization-id="calendarOrganizationId"
          :event-id="calendarEventId"
        />
      </div>
    </BOverlay>
  </div>
</template>
