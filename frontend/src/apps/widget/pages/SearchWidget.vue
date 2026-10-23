<script setup lang="ts">
import { BFormInput, BFormSelect, BOverlay, BPagination, BSpinner } from "bootstrap-vue-next";
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import { boot } from "@/shared/boot";
import type { SearchSettings } from "@/shared/customWidget";
import EventWarningPills from "@/shared/EventWarningPills.vue";
import { formatEventDate } from "@/shared/format";
import { publicPages } from "@/shared/legacy";
import { scrollToTop, trackAnalytics, usePageViewTracking, useWidgetSettings } from "../bridge";
import { searchWidgetCss } from "../widgetStyle";

type EventDate = components["schemas"]["WidgetEventDate"];

const MAX_PER_PAGE = 50;
const MOBILE_PREVIEW_LENGTH = 100;

const { t } = useI18n();
const settings = useWidgetSettings<SearchSettings>();
usePageViewTracking();

const today = () => new Date().toLocaleDateString("sv"); // YYYY-MM-DD
const form = ref({ dateFrom: today(), dateTo: "", categoryId: 0, keyword: "" });
const rows = ref<EventDate[]>([]);
const total = ref(0);
const currentPage = ref(1);
const loading = ref(false);
const error = ref<string | null>(null);
const categories = ref<{ value: number; text: string }[] | null>(null);
const initialLoaded = ref(false);

// Only the newest request may write its result.
let request = 0;

const css = computed(() => (settings.value ? searchWidgetCss(settings.value) : ""));
const perPage = computed(() =>
  settings.value ? Math.min(MAX_PER_PAGE, Number(settings.value.eventsPerPage) || 10) : 10,
);

function searchParams() {
  const params: Record<string, string | number> = {
    page: currentPage.value,
    per_page: perPage.value,
    date_from: form.value.dateFrom,
  };
  if (settings.value?.organizationId) params.organization_id = settings.value.organizationId;
  if (form.value.dateTo) params.date_to = form.value.dateTo;
  if (form.value.keyword) params.keyword = form.value.keyword;
  if (form.value.categoryId > 0) params.category_id = form.value.categoryId;
  return params;
}

async function loadData() {
  if (!settings.value) return;
  const mine = ++request;
  loading.value = true;
  const needsScroll = rows.value.length > 0;
  const { data, error: err } = await api.GET("/bff/public/widget/event-dates", {
    params: { query: searchParams() as never },
  });
  if (mine !== request) return;
  loading.value = false;
  if (data) {
    error.value = null;
    rows.value = data.items;
    total.value = data.total;
    initialLoaded.value = true;
  } else {
    rows.value = [];
    total.value = 0;
    error.value = err?.message ?? t("Error");
  }
  if (needsScroll) scrollToTop();
}

async function loadCategories() {
  if (!settings.value?.showFilter || categories.value != null) return;
  const { data } = await api.GET("/bff/public/widget/categories");
  if (data) {
    categories.value = [
      { value: 0, text: "" },
      ...data.items.map((c) => ({ value: c.id, text: c.name })),
    ];
  }
}

function search() {
  if (currentPage.value !== 1) currentPage.value = 1;
  else loadData();
}

const hasSettings = computed(() => settings.value != null);
watch(
  hasSettings,
  (has) => {
    if (!has) return;
    loadData();
    loadCategories();
  },
  { immediate: true },
);
watch(currentPage, loadData);
watch(
  () => settings.value?.organizationId,
  () => initialLoaded.value && loadData(),
);
watch(
  () => settings.value?.eventsPerPage,
  () => {
    if (!initialLoaded.value) return;
    search();
  },
);
watch(() => settings.value?.showFilter, loadCategories);

const fullDate = (d: EventDate) => formatEventDate(d.start, d.end, d.allday, boot.locale);
const shortDate = (d: EventDate) =>
  new Intl.DateTimeFormat(boot.locale, {
    dateStyle: "short",
    ...(d.allday ? {} : { timeStyle: "short" as const }),
  }).format(new Date(d.start));

function shorten(text: string | null | undefined, length: number): string {
  if (!text || text.length <= length) return text ?? "";
  const cut = text.slice(0, length - 1);
  const boundary = cut.lastIndexOf(" ");
  return `${boundary > 0 ? cut.slice(0, boundary) : cut}…`;
}

function openEventDate(d: EventDate) {
  const url = `${location.origin}${publicPages.eventDate(d.id)}`;
  trackAnalytics({ event: "linkClick", url });
  window.open(url);
}

function printPage() {
  window.print();
}

function openSearch() {
  const params = new URLSearchParams(
    Object.entries(searchParams()).map(([k, v]) => [k, String(v)]),
  );
  window.open(`${location.origin}/eventdates?${params}`);
}
</script>

<template>
  <div v-if="settings" class="search-widget">
    <component :is="'style'">{{ css }}</component>

    <form
      v-if="settings.showFilter"
      class="row g-2 mb-4"
      autocomplete="off"
      @submit.prevent="search"
    >
      <div class="col-auto">
        <div class="input-group">
          <span class="input-group-text">{{ t("From") }}</span>
          <BFormInput v-model="form.dateFrom" type="date" :aria-label="t('From')" />
        </div>
      </div>
      <div class="col-auto">
        <div class="input-group">
          <span class="input-group-text">{{ t("To") }}</span>
          <BFormInput
            v-model="form.dateTo"
            type="date"
            :min="form.dateFrom"
            :aria-label="t('To')"
          />
        </div>
      </div>
      <div class="col-auto">
        <div class="input-group">
          <span class="input-group-text">{{ t("Category") }}</span>
          <BFormSelect
            v-model="form.categoryId"
            :options="categories ?? []"
            :aria-label="t('Category')"
          />
        </div>
      </div>
      <div class="col-auto">
        <div class="input-group">
          <span class="input-group-text">{{ t("Keyword") }}</span>
          <BFormInput v-model="form.keyword" :aria-label="t('Keyword')" />
        </div>
      </div>
      <div class="col-auto">
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

      <template v-if="settings.layout === 'card'">
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
                    <i class="fa fa-calendar"></i> {{ fullDate(date) }}
                  </h6>
                  <p v-if="date.event.description_preview" class="card-text">
                    {{ date.event.description_preview }}
                  </p>
                  <small class="text-muted me-2">
                    <i class="fa fa-database"></i>
                    {{ date.event.organization_name }}
                  </small>
                  <small
                    v-if="
                      date.event.organizer_name &&
                      date.event.organizer_name !== date.event.organization_name
                    "
                    class="text-muted me-2"
                  >
                    <i class="fa fa-server"></i> {{ date.event.organizer_name }}
                  </small>
                  <small v-if="date.event.place_name" class="text-muted">
                    <i class="fa fa-map-marker"></i> {{ date.event.place_name }}
                  </small>
                  <a
                    href="#"
                    class="stretched-link"
                    :aria-label="date.event.name"
                    @click.stop.prevent="openEventDate(date)"
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
                      class="px-1 text-muted"
                    >
                      <small v-if="date.event.photo.copyright_text">
                        &copy; {{ date.event.photo.copyright_text }}
                      </small>
                      <small v-if="date.event.photo.license_code">
                        <a
                          :href="date.event.photo.license_url ?? undefined"
                          target="_blank"
                          rel="noopener noreferrer"
                          >{{ date.event.photo.license_code }}</a
                        >
                      </small>
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
                class="px-1 text-muted"
              >
                <small v-if="date.event.photo.copyright_text">
                  &copy; {{ date.event.photo.copyright_text }}
                </small>
                <small v-if="date.event.photo.license_code">
                  <a
                    :href="date.event.photo.license_url ?? undefined"
                    target="_blank"
                    rel="noopener noreferrer"
                    >{{ date.event.photo.license_code }}</a
                  >
                </small>
              </div>
            </div>
            <div class="card-body">
              <h5 class="card-title">
                {{ date.event.name }} <EventWarningPills :event="date.event" />
              </h5>
              <h6 class="card-subtitle mb-2 text-body">
                <i class="fa fa-calendar"></i> {{ fullDate(date) }}
              </h6>
              <p v-if="date.event.description_preview" class="card-text">
                {{ shorten(date.event.description_preview, MOBILE_PREVIEW_LENGTH) }}
              </p>
              <small class="text-muted me-2">
                <i class="fa fa-database"></i>
                {{ date.event.organization_name }}
              </small>
              <small
                v-if="
                  date.event.organizer_name &&
                  date.event.organizer_name !== date.event.organization_name
                "
                class="text-muted me-2"
              >
                <i class="fa fa-server"></i> {{ date.event.organizer_name }}
              </small>
              <small v-if="date.event.place_name" class="text-muted">
                <i class="fa fa-map-marker"></i> {{ date.event.place_name }}
              </small>
              <a
                href="#"
                class="stretched-link"
                :aria-label="date.event.name"
                @click.stop.prevent="openEventDate(date)"
              ></a>
            </div>
          </div>
        </div>
      </template>

      <div v-else-if="settings.layout === 'text'" class="mb-3">
        <div v-for="date in rows" :key="date.id" data-test="event-line">
          {{ shortDate(date) }}
          <a href="#" @click.stop.prevent="openEventDate(date)">{{ date.event.name }}</a>
          <EventWarningPills :event="date.event" />
        </div>
      </div>

      <BPagination
        v-if="settings.showPagination && total > perPage"
        v-model="currentPage"
        :total-rows="total"
        :per-page="perPage"
      />

      <div class="d-print-none">
        <div v-if="settings.showEventCallyLink" class="mb-2">
          <a href="#" class="underlined" @click.stop.prevent="openSearch">{{ t("Open search") }}</a>
        </div>
        <div v-if="settings.showPrintButton && total > 0">
          <button type="button" class="btn btn-secondary btn-print" @click="printPage">
            <i class="fa fa-print"></i> {{ t("Print") }}
          </button>
        </div>
      </div>
    </BOverlay>
  </div>
</template>
