<script setup lang="ts">
import { BFormInput, BFormSelect, BOverlay, BSpinner } from "bootstrap-vue-next";
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRoute } from "vue-router";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import { boot } from "@/shared/boot";
import type { SearchSettings } from "@/shared/customWidget";
import EventWarningPills from "@/shared/EventWarningPills.vue";
import AppPager from "@/shared/AppPager.vue";
import { publicPages } from "@/shared/legacy";
import { scrollToTop, trackAnalytics, usePageViewTracking, useWidgetSettings } from "../bridge";
import { apiParams, pageUrl, parseLegacyQuery, searchUrl, type LegacyQuery } from "../legacyQuery";
import { searchWidgetCss } from "../widgetStyle";

// The iframe page customers embed with `/organizations/<id>/widget/eventdates`. The URL, its query
// string and the analytics messages are kept as the server-rendered page had them; see
// legacyQuery.ts. It reads through /bff/public/widget/organizations/<id>/event-dates.
type EventDate = components["schemas"]["WidgetEventDate"];

const MOBILE_PREVIEW_LENGTH = 100;

const { t } = useI18n();
const route = useRoute();
const organizationId = Number(route.params.id);
// Preset by the shell; this page never waits for the embedding page.
const settings = useWidgetSettings<SearchSettings>();
// The URL as it was loaded (the loader's `…/eventdates?`), before the router tidies it.
usePageViewTracking(() => window.__eventcallyWidget?.initialHref ?? document.location.href);

const query = ref<LegacyQuery>(parseLegacyQuery(location.search));
const form = ref(formOf(query.value));
const rows = ref<EventDate[]>([]);
const page = ref({ page: 1, pages: 0, total: 0 });
const loading = ref(false);
const error = ref<string | null>(null);
const categories = ref<{ value: number; text: string }[]>([{ value: 0, text: "" }]);

// Only the newest request may write its result.
let request = 0;

const css = computed(() => (settings.value ? searchWidgetCss(settings.value) : ""));

function formOf(q: LegacyQuery) {
  return {
    dateFrom: q.dateFrom,
    dateTo: q.dateTo,
    categoryId: q.categoryId,
    keyword: q.keyword,
  };
}

async function loadData() {
  const mine = ++request;
  loading.value = true;
  const { data, error: err } = await api.GET("/bff/public/widget/organizations/{id}/event-dates", {
    params: {
      path: { id: organizationId },
      query: apiParams(location.search),
    },
  });
  if (mine !== request) return;
  loading.value = false;
  if (data) {
    error.value = null;
    rows.value = data.items;
    page.value = { page: data.page, pages: data.pages, total: data.total };
  } else {
    rows.value = [];
    page.value = { page: 1, pages: 0, total: 0 };
    error.value = err?.message ?? t("Error");
  }
}

async function loadCategories() {
  const { data } = await api.GET("/bff/public/widget/categories");
  if (data) {
    categories.value = [
      { value: 0, text: "" },
      ...data.items.map((c) => ({ value: c.id, text: c.name })),
    ];
  }
}

/** A search or a page change: the legacy page loaded a new document, so it counts a page view. */
function navigate(url: string) {
  history.pushState(null, "", url);
  showLocation();
}

function showLocation() {
  query.value = parseLegacyQuery(location.search);
  form.value = formOf(query.value);
  loadData();
  scrollToTop();
  trackAnalytics({ event: "pageView", url: document.location.href });
}

function search() {
  navigate(searchUrl(location.pathname, form.value, query.value));
}

function goToPage(target: number) {
  navigate(pageUrl(location.pathname, location.search, target));
}

onMounted(() => {
  window.addEventListener("popstate", showLocation);
  loadData();
  loadCategories();
});
onBeforeUnmount(() => window.removeEventListener("popstate", showLocation));

const eventDateUrl = (d: EventDate) => `${location.origin}${publicPages.eventDate(d.id)}`;

/** `09.04.2040 18:00`, like the old `render_event_date_instance`: the start only, no time for all-day. */
function startText(d: EventDate): string {
  // The server sends UTC; the old page showed Berlin time whatever the visitor's time zone.
  const timeZone = "Europe/Berlin";
  const start = new Date(d.start);
  const day = new Intl.DateTimeFormat(boot.locale, { dateStyle: "medium", timeZone }).format(start);
  if (d.allday) return day;
  const time = new Intl.DateTimeFormat(boot.locale, { timeStyle: "short", timeZone }).format(start);
  return `${day} ${time}`;
}

function shorten(text: string | null | undefined, length: number): string {
  if (!text || text.length <= length) return text ?? "";
  const cut = text.slice(0, length - 1);
  const boundary = cut.lastIndexOf(" ");
  return `${boundary > 0 ? cut.slice(0, boundary) : cut}…`;
}

const ownEvent = (d: EventDate) => d.event.organization_id === organizationId;

function trackLinkClick(d: EventDate) {
  trackAnalytics({ event: "linkClick", url: eventDateUrl(d) });
}

function printPage() {
  window.print();
}
</script>

<template>
  <div class="event-dates-widget p-3">
    <component :is="'style'">{{ css }}</component>

    <form class="row g-2 mb-4" autocomplete="off" @submit.prevent="search">
      <div class="col-12 col-sm-auto">
        <div class="input-group">
          <span class="input-group-text">{{ t("From") }}</span>
          <BFormInput v-model="form.dateFrom" type="date" :aria-label="t('From')" />
        </div>
      </div>
      <div class="col-12 col-sm-auto">
        <div class="input-group">
          <span class="input-group-text">{{ t("to") }}</span>
          <BFormInput
            v-model="form.dateTo"
            type="date"
            :min="form.dateFrom"
            :aria-label="t('to')"
          />
        </div>
      </div>
      <div class="col-12 col-sm-auto">
        <div class="input-group">
          <span class="input-group-text">{{ t("Category") }}</span>
          <BFormSelect
            v-model="form.categoryId"
            :options="categories"
            :aria-label="t('Category')"
          />
        </div>
      </div>
      <div class="col-12 col-sm-auto">
        <div class="input-group">
          <span class="input-group-text">{{ t("Keyword") }}</span>
          <BFormInput v-model="form.keyword" :aria-label="t('Keyword')" />
        </div>
      </div>
      <div class="col-12 col-sm-auto">
        <button type="submit" class="btn btn-primary" :disabled="loading">
          <BSpinner v-if="loading" small />
          {{ t("Find") }}
        </button>
      </div>
    </form>

    <BOverlay :show="loading" variant="transparent">
      <div v-if="error" class="mb-4">
        <div class="alert alert-danger" role="alert">{{ error }}</div>
        <button
          type="button"
          class="btn btn-outline-secondary"
          :aria-label="t('Retry')"
          @click="loadData"
        >
          <i class="fa fa-sync-alt"></i>
        </button>
      </div>

      <div v-for="date in rows" :key="date.id" data-test="event-card">
        <!-- Desktop -->
        <div class="card mb-3 d-none d-sm-block">
          <div class="card-body">
            <div class="row">
              <div class="col-sm-8">
                <h5 class="card-title">
                  {{ date.event.name }}
                  <EventWarningPills :event="date.event" />
                </h5>
                <h6 class="card-subtitle mb-2 text-body">
                  <i class="fa fa-calendar"></i> {{ startText(date) }}
                </h6>
                <p v-if="date.event.description_preview" class="card-text">
                  {{ date.event.description_preview }}
                </p>
                <small v-if="ownEvent(date)" class="text-muted me-2">
                  <i class="fa fa-server"></i> {{ date.event.organizer_name }}
                </small>
                <small v-else class="text-muted me-2">
                  <i class="fa fa-database"></i>
                  {{ date.event.organization_name }}
                </small>
                <small class="text-muted">
                  <i class="fa fa-map-marker"></i> {{ date.event.place_name }}
                </small>
                <a
                  :href="eventDateUrl(date)"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="stretched-link"
                  :aria-label="date.event.name"
                  @click="trackLinkClick(date)"
                ></a>
              </div>
              <div class="col-sm-4 text-end">
                <div v-if="date.event.photo" class="position-relative">
                  <img
                    :src="date.event.photo.url_200"
                    alt=""
                    style="object-fit: cover; width: 200px"
                  />
                  <div
                    v-if="date.event.photo.copyright_text || date.event.photo.license_code"
                    class="small px-1 text-muted"
                  >
                    <span v-if="date.event.photo.copyright_text">
                      &copy; {{ date.event.photo.copyright_text }}
                    </span>
                    <a
                      v-if="date.event.photo.license_code"
                      :href="date.event.photo.license_url ?? undefined"
                      target="_blank"
                      rel="noopener noreferrer"
                      >{{ date.event.photo.license_code }}</a
                    >
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Mobile -->
        <div class="card mb-3 d-sm-none">
          <div v-if="date.event.photo" class="position-relative">
            <img
              :src="date.event.photo.url_500"
              alt=""
              class="card-img-top"
              style="object-fit: cover; height: 40vw"
            />
            <div
              v-if="date.event.photo.copyright_text || date.event.photo.license_code"
              class="small px-1 text-muted"
            >
              <span v-if="date.event.photo.copyright_text">
                &copy; {{ date.event.photo.copyright_text }}
              </span>
              <a
                v-if="date.event.photo.license_code"
                :href="date.event.photo.license_url ?? undefined"
                target="_blank"
                rel="noopener noreferrer"
                >{{ date.event.photo.license_code }}</a
              >
            </div>
          </div>
          <div class="card-body">
            <h5 class="card-title">
              {{ date.event.name }} <EventWarningPills :event="date.event" />
            </h5>
            <h6 class="card-subtitle mb-2 text-body">
              <i class="fa fa-calendar"></i> {{ startText(date) }}
            </h6>
            <p v-if="date.event.description_preview" class="card-text">
              {{ shorten(date.event.description_preview, MOBILE_PREVIEW_LENGTH) }}
            </p>
            <small v-if="ownEvent(date)" class="text-muted me-2">
              <i class="fa fa-server"></i> {{ date.event.organizer_name }}
            </small>
            <small v-else class="text-muted me-2">
              <i class="fa fa-database"></i> {{ date.event.organization_name }}
            </small>
            <small class="text-muted">
              <i class="fa fa-map-marker"></i> {{ date.event.place_name }}
            </small>
            <a
              :href="eventDateUrl(date)"
              target="_blank"
              rel="noopener noreferrer"
              class="stretched-link"
              :aria-label="date.event.name"
              @click="trackLinkClick(date)"
            ></a>
          </div>
        </div>
      </div>

      <AppPager
        v-if="settings?.showPagination !== false"
        :page="page.page"
        :pages="page.pages"
        :total="page.total"
        @update:page="goToPage"
      />

      <button
        type="button"
        class="btn btn-outline-secondary d-print-none btn-print"
        @click="printPage"
      >
        <i class="fa fa-print"></i> {{ t("Print") }}
      </button>
    </BOverlay>
  </div>
</template>

<style>
/* The old page hid "Page x of y" on phones: only the four buttons stay. */
@media (max-width: 575.98px) {
  .event-dates-widget .pagination .page-item:nth-child(3) {
    display: none;
  }
}
</style>
