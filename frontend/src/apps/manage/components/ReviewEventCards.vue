<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { boot } from "@/shared/boot";
import EventWarningPills from "@/shared/EventWarningPills.vue";
import { formatDateShort, formatDateTimeShort, formatEventDate } from "@/shared/format";
import { publicPages } from "@/shared/legacy";
import LinkifiedText from "@/shared/LinkifiedText.vue";
import ContactLines from "./ContactLines.vue";
import ReviewProp from "./ReviewProp.vue";

type ReviewEvent = components["schemas"]["ReviewEvent"];
type ReviewEventDate = components["schemas"]["ReviewEventDate"];

const props = defineProps<{ event: ReviewEvent; dates: ReviewEventDate[] }>();

const { t } = useI18n();

const when = computed(() =>
  props.event.start
    ? formatEventDate(props.event.start, props.event.end, props.event.allday, boot.locale)
    : "",
);
const created = computed(() => formatDateTimeShort(props.event.created_at, boot.locale));
const updated = computed(() => formatDateTimeShort(props.event.updated_at, boot.locale));
const ageRange = computed(() => {
  const { age_from: from, age_to: to } = props.event;
  return from || to ? `${from ?? ""} - ${to ?? ""}` : null;
});
const withScheme = (link: string) => (/^https?:\/\//.test(link) ? link : `https://${link}`);
</script>

<template>
  <div>
    <div class="card mb-3" data-test="event-card">
      <div class="card-header">{{ t("Event") }}</div>
      <div class="card-body">
        <h5 class="card-title">
          {{ event.name }}
          <EventWarningPills :event="event" />
        </h5>

        <div>
          <i class="fa fa-fw fa-calendar me-1" :title="t('Date')"></i>
          {{ when }}
          <template v-if="dates.length > 1">
            | <a href="#event-dates">{{ t("%(count)d event dates", { count: dates.length }) }}</a>
          </template>
        </div>

        <ReviewProp v-if="event.status_label" icon="fa-info-circle" :title="t('Status')">{{
          event.status_label
        }}</ReviewProp>

        <div v-if="event.photo_url" class="my-4 text-center">
          <img :src="event.photo_url" class="img-fluid" style="max-width: 100%" alt="image" />
        </div>

        <div v-if="event.description" class="my-4" style="white-space: pre-wrap">
          <LinkifiedText :text="event.description" />
        </div>

        <div class="mt-4" data-test="event-props">
          <ReviewProp v-if="event.price_info" icon="fa-euro-sign" :title="t('Price info')">{{
            event.price_info
          }}</ReviewProp>
          <ReviewProp v-if="event.external_link" icon="fa-link" :title="t('Link')">
            <a
              :href="withScheme(event.external_link)"
              target="_blank"
              rel="noopener noreferrer"
              style="word-break: break-all"
              >{{ event.external_link }}</a
            >
          </ReviewProp>
          <ReviewProp v-if="event.ticket_link" icon="fa-link" :title="t('Link')">
            <a
              :href="withScheme(event.ticket_link)"
              target="_blank"
              rel="noopener noreferrer"
              style="word-break: break-all"
              >{{ event.ticket_link }}</a
            >
          </ReviewProp>
          <ReviewProp v-if="event.category_names.length" icon="fa-archive" :title="t('Category')">{{
            event.category_names.join(", ")
          }}</ReviewProp>
          <ReviewProp
            v-for="set in event.custom_categories"
            :key="set.label"
            icon="fa-archive"
            :title="set.label"
            >{{ set.names.join(", ") }}</ReviewProp
          >
          <ReviewProp v-if="event.tags" icon="fa-tags" :title="t('Tags')">{{
            event.tags.replaceAll(",", ", ")
          }}</ReviewProp>
          <ReviewProp v-if="event.kid_friendly" icon="fa-child" :title="t('Kid friendly')">{{
            t("Kid friendly")
          }}</ReviewProp>
          <ReviewProp
            v-if="event.accessible_for_free"
            icon="fa-door-open"
            :title="t('Accessible for free')"
            >{{ t("Accessible for free") }}</ReviewProp
          >
          <ReviewProp v-if="ageRange" icon="fa-people-arrows" :title="t('Typical Age range')">{{
            ageRange
          }}</ReviewProp>
          <ReviewProp
            v-if="event.target_group_origin_label"
            icon="fa-users"
            :title="t('Target group origin')"
            >{{ event.target_group_origin_label }}</ReviewProp
          >
          <ReviewProp
            v-if="event.attendance_mode_label"
            icon="fa-mouse-pointer"
            :title="t('Attendance mode')"
            >{{ event.attendance_mode_label }}</ReviewProp
          >
          <ReviewProp
            v-if="event.registration_required"
            icon="fa-list"
            :title="t('Registration required')"
            >{{ t("Registration required") }}</ReviewProp
          >
          <ReviewProp v-if="event.booked_up" icon="fa-square-full" :title="t('Booked up')">{{
            t("Booked up")
          }}</ReviewProp>
          <ReviewProp
            v-if="event.expected_participants"
            icon="fa-users"
            :title="t('Expected number of participants')"
            >{{ event.expected_participants }}</ReviewProp
          >
        </div>
      </div>
      <div class="card-footer small" data-test="event-audit">
        {{ t("Created at %(created_at)s.", { created_at: created }) }}
        <template v-if="updated && updated !== created">
          {{ t("Last updated at %(updated_at)s.", { updated_at: updated }) }}
        </template>
        <a :href="event.report_url" class="text-dark text-decoration-none" target="_blank" rel="noopener noreferrer">{{
          t("Report event")
        }}</a>
      </div>
    </div>

    <div class="card mb-3" data-test="place-card">
      <div class="card-header">{{ t("Place") }}</div>
      <div class="card-body">
        <template v-if="event.place">
          <h5 class="card-title">{{ event.place.name }}</h5>

          <div v-if="event.place.photo_url" class="my-4 text-center">
            <img :src="event.place.photo_url" class="img-fluid" style="max-width: 100%" alt="image" />
          </div>

          <div v-if="event.place.description" class="my-4">{{ event.place.description }}</div>

          <ContactLines class="my-4" :url="event.place.url" :address="event.place.address" />

          <p v-if="event.place.directions_url">
            <a
              :href="event.place.directions_url"
              class="btn btn-secondary"
              target="_blank"
              rel="noopener noreferrer"
              >{{ t("Show directions") }}</a
            >
          </p>

          <p v-if="event.attendance_mode === 'online'">
            {{ t("The event takes place online.") }}
          </p>
          <p v-else-if="event.attendance_mode === 'mixed'">
            {{ t("The event takes place both offline and online.") }}
          </p>
        </template>
      </div>
    </div>

    <div v-if="event.organizer" class="card mb-3" data-test="organizer-card">
      <div class="card-header">{{ t("Organizer") }}</div>
      <div class="card-body">
        <template v-for="(organizer, index) in [event.organizer, ...event.co_organizers]" :key="index">
          <div :class="{ 'mt-4': index > 0 }">
            <h5 class="card-title">{{ organizer.name }}</h5>
            <div v-if="organizer.logo_url" class="my-4">
              <img :src="organizer.logo_url" class="img-fluid" style="max-width: 120px" alt="Logo" />
            </div>
            <ContactLines
              :url="organizer.url"
              :email="organizer.email"
              :phone="organizer.phone"
              :fax="organizer.fax"
            />
          </div>
        </template>
      </div>
    </div>

    <div class="card mb-3" data-test="organization-card">
      <div class="card-header">{{ t("Organization") }}</div>
      <div class="card-body">
        <h5 class="card-title">
          {{ event.organization.name }}
          <i
            v-if="event.organization.is_verified"
            class="fa fa-check-circle text-primary"
            :title="t('Verified')"
          ></i>
        </h5>
        <div v-if="event.organization.logo_url" class="my-4">
          <img :src="event.organization.logo_url" class="img-fluid" style="max-width: 120px" alt="Logo" />
        </div>
        <ContactLines
          class="my-4"
          :url="event.organization.url"
          :email="event.organization.email"
          :phone="event.organization.phone"
          :fax="event.organization.fax"
          :address="event.organization.address"
        />
      </div>
    </div>

    <div v-if="dates.length" id="event-dates" class="card mt-4" data-test="dates-card">
      <div class="card-header">{{ t("Event Dates") }}</div>
      <div class="list-group list-group-flush" style="max-height: 30vh; overflow-y: auto">
        <a
          v-for="date in dates"
          :key="date.id"
          :href="publicPages.eventDate(date.id)"
          class="list-group-item"
          >{{ formatDateShort(date.start, boot.locale) }}</a
        >
      </div>
    </div>
  </div>
</template>
