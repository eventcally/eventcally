<script setup lang="ts">
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { boot } from "@/shared/boot";
import AuditLine from "@/shared/AuditLine.vue";
import EventWarningPills from "@/shared/EventWarningPills.vue";
import { ensureLinkScheme, formatEventDate } from "@/shared/format";
import { manage, publicPages } from "@/shared/legacy";
import LinkifiedText from "@/shared/LinkifiedText.vue";
import ShareModal from "@/shared/ShareModal.vue";
import CalendarExportModal from "./CalendarExportModal.vue";
import EventContact from "./EventContact.vue";
import EventMenu from "./EventMenu.vue";
import EventProp from "./EventProp.vue";
import ImageFigure from "./ImageFigure.vue";

type PublicEventDetail = components["schemas"]["PublicEventDetail"];

// The body of the event and the event date page; `start`/`end`/`allday` are the shown date.
const props = defineProps<{
  event: PublicEventDetail;
  start: string;
  end?: string | null;
  allday: boolean;
}>();

const { t } = useI18n();

const shareVisible = ref(false);
const calendarVisible = ref(false);

const dateLine = computed(() => formatEventDate(props.start, props.end, props.allday, boot.locale));
const placeLine = computed(() => {
  const place = props.event.place;
  return place.city ? `${place.name}, ${place.city}` : place.name;
});
const links = computed(() => [props.event.external_link, props.event.ticket_link].filter((l): l is string => !!l));
const rating = computed(() => (props.event.rating ? `${Math.trunc(props.event.rating / 10)}/10` : null));
const tags = (value: string) => value.replace(/,/g, ", ");
const hasAgeRange = computed(() => props.event.age_from || props.event.age_to);
const online = computed(() => props.event.attendance_mode === "online");
const mixed = computed(() => props.event.attendance_mode === "mixed");
const directionsUrl = computed(
  () => `http://www.google.com/maps?q=${encodeURIComponent(props.event.place.directions_query)}`,
);
const showReferencedBy = computed(
  () => props.event.rights.can_reference_event || props.event.references.length > 0,
);
const requestPill = (status: string | null | undefined) =>
  status === "inbox" ? "text-bg-info" : status === "verified" ? "text-bg-success" : "text-bg-danger";
</script>

<template>
  <div class="event-detail">
    <div class="w-normal mx-auto">
      <div v-if="event.photo" class="d-flex">
        <ImageFigure :image="event.photo" img-class="mx-auto" />
      </div>

      <div class="p-3 clearfix">
        <div class="float-sm-end">
          <EventMenu :event-id="event.id" :organization-id="event.organization_id" :rights="event.rights" />
        </div>

        <div class="fw-bold text-uppercase">
          {{ dateLine }}
          <template v-if="event.dates.length > 1">
            | <a href="#event-dates">{{ t("%(count)d event dates", { count: event.dates.length }) }}</a>
          </template>
        </div>

        <h1 class="fw-bold my-1">
          {{ event.name }}
          <EventWarningPills :event="event" />
        </h1>
        <div class="text-muted">{{ placeLine }}</div>
      </div>
    </div>

    <div class="d-flex bg-light p-3">
      <div class="mx-auto" style="width: 40rem; max-width: 100%">
        <div class="card mb-3">
          <div class="card-body">
            <h2 class="mt-0">{{ t("Event") }}</h2>

            <EventProp v-if="event.status_label" icon="fa-info-circle" :title="t('Status')">{{
              event.status_label
            }}</EventProp>
            <EventProp v-if="rating" icon="fa-adjust" :title="t('Rating')">{{ rating }}</EventProp>

            <div>
              <EventProp v-if="event.price_info" icon="fa-euro-sign" :title="t('Price info')">{{
                event.price_info
              }}</EventProp>
              <template v-for="link in links" :key="link">
                <EventProp icon="fa-link" :title="t('Link')">
                  <a
                    :href="ensureLinkScheme(link)"
                    target="_blank"
                    rel="noopener noreferrer"
                    style="word-break: break-all"
                    >{{ link }}</a
                  >
                </EventProp>
              </template>
              <EventProp
                v-for="group in event.categories"
                :key="group.label"
                icon="fa-archive"
                :title="group.label"
                >{{ group.names.join(", ") }}</EventProp
              >
              <EventProp v-if="event.tags" icon="fa-tags" :title="t('Tags')">{{ tags(event.tags) }}</EventProp>
              <EventProp v-if="event.kid_friendly" icon="fa-child" :title="t('Kid friendly')">{{
                t("Kid friendly")
              }}</EventProp>
              <EventProp v-if="event.accessible_for_free" icon="fa-door-open" :title="t('Accessible for free')">{{
                t("Accessible for free")
              }}</EventProp>
              <EventProp v-if="hasAgeRange" icon="fa-people-arrows" :title="t('Typical Age range')"
                >{{ event.age_from }} - {{ event.age_to }}</EventProp
              >
              <EventProp
                v-if="event.target_group_origin_label"
                icon="fa-users"
                :title="t('Target group origin')"
                >{{ event.target_group_origin_label }}</EventProp
              >
              <EventProp v-if="event.attendance_mode_label" icon="fa-mouse-pointer" :title="t('Attendance mode')">{{
                event.attendance_mode_label
              }}</EventProp>
              <EventProp v-if="event.registration_required" icon="fa-list" :title="t('Registration required')">{{
                t("Registration required")
              }}</EventProp>
              <EventProp v-if="event.booked_up" icon="fa-square-full" :title="t('Booked up')">{{
                t("Booked up")
              }}</EventProp>
              <EventProp
                v-if="event.expected_participants"
                icon="fa-users"
                :title="t('Expected number of participants')"
                >{{ event.expected_participants }}</EventProp
              >
              <EventProp v-if="event.internal_tags" icon="fa-tags" :title="t('Internal tags')">{{
                tags(event.internal_tags)
              }}</EventProp>
            </div>

            <div v-if="event.description" class="mt-4" style="white-space: pre-wrap">
              <LinkifiedText :text="event.description" />
            </div>

            <div class="mt-4">
              <button type="button" class="btn btn-outline-secondary me-1 mb-1" @click="shareVisible = true">
                <i class="fa fa-share-alt"></i> {{ t("Share") }}
              </button>
              <button type="button" class="btn btn-outline-secondary me-1 mb-1" @click="calendarVisible = true">
                <i class="fa fa-calendar"></i> {{ t("Add to calendar") }}
              </button>
              <a
                v-if="event.rights.can_update_event"
                :href="manage.eventUpdate(event.organization_id, event.id)"
                class="btn btn-outline-secondary mb-1"
                ><i class="fa fa-edit"></i> {{ t("Edit") }}</a
              >
            </div>

            <div class="small mt-2">
              <AuditLine :audit="event.audit" inline />{{ " " }}
              <a :href="publicPages.eventReport(event.id)" class="text-dark">{{ t("Report event") }}</a>
            </div>
          </div>
        </div>

        <div class="card mb-3">
          <div class="card-body">
            <h2 class="mt-0">{{ t("Place") }}</h2>

            <div class="row">
              <div v-if="event.place.photo" class="col-12 col-sm-auto order-sm-last">
                <ImageFigure :image="event.place.photo" img-class="img-thumbnail" />
              </div>

              <div class="col-12 col-sm">
                <div class="fw-bold">{{ event.place.name }}</div>

                <div v-if="event.place.description" class="my-4">{{ event.place.description }}</div>

                <EventContact :url="event.place.url" :address="event.place.address" />

                <div v-if="online" class="mt-2">{{ t("The event takes place online.") }}</div>
                <div v-else-if="mixed" class="mt-2">{{ t("The event takes place both offline and online.") }}</div>

                <div v-if="(event.attendance_mode && !online) || event.rights.can_update_event" class="mt-2">
                  <a
                    v-if="event.attendance_mode && !online"
                    :href="directionsUrl"
                    class="btn btn-outline-secondary me-1"
                    target="_blank"
                    rel="noopener noreferrer"
                    ><i class="fa fa-directions"></i> {{ t("Show directions") }}</a
                  >
                  <a
                    v-if="event.rights.can_update_event"
                    :href="manage.eventPlaceUpdate(event.place.organization_id, event.place.id)"
                    class="btn btn-outline-secondary"
                    ><i class="fa fa-edit"></i> {{ t("Edit") }}</a
                  >
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="card mb-3">
          <div class="card-body">
            <h2 class="mt-0">{{ t("Organizer") }}</h2>

            <div
              v-for="(organizer, index) in [event.organizer, ...event.co_organizers]"
              :key="organizer.id"
              :class="{ 'mt-4': index > 0 }"
            >
              <div class="row">
                <div v-if="organizer.logo" class="col-12 col-sm-auto order-sm-last">
                  <ImageFigure :image="organizer.logo" max-width="120px" alt="Logo" />
                </div>

                <div class="col-12 col-sm">
                  <div class="fw-bold">
                    <a :href="publicPages.organizer(organizer.id)">{{ organizer.name }}</a>
                  </div>
                  <EventContact :url="organizer.url" :email="organizer.email" :phone="organizer.phone" :fax="organizer.fax" />
                </div>
              </div>
              <div v-if="event.rights.can_update_event" class="mt-2">
                <a
                  :href="manage.eventOrganizerUpdate(event.organization_id, organizer.id)"
                  class="btn btn-outline-secondary"
                  ><i class="fa fa-edit"></i> {{ t("Edit") }}</a
                >
              </div>
            </div>
          </div>
        </div>

        <div class="card mb-3">
          <div class="card-body">
            <h2 class="mt-0">{{ t("Organization") }}</h2>

            <div class="row">
              <div v-if="event.organization.logo" class="col-12 col-sm-auto order-sm-last">
                <ImageFigure :image="event.organization.logo" max-width="120px" alt="Logo" />
              </div>

              <div class="col-12 col-sm">
                <div class="fw-bold">
                  <a :href="publicPages.organization(event.organization.id)">{{ event.organization.name }}</a>
                  <i
                    v-if="event.organization.is_verified"
                    class="fa fa-check-circle text-primary ms-1"
                    :title="t('Verified')"
                  ></i>
                </div>
                <EventContact
                  :url="event.organization.url"
                  :email="event.organization.email"
                  :phone="event.organization.phone"
                  :fax="event.organization.fax"
                  :address="event.organization.address"
                />
              </div>
            </div>
          </div>
        </div>

        <div v-if="showReferencedBy" class="card mb-3" data-test="references">
          <div class="card-body pb-0">
            <h2 class="mt-0">{{ t("Referenced by") }}</h2>
          </div>
          <div class="list-group list-group-flush mb-4" style="max-height: 30vh; overflow-y: auto">
            <span v-for="reference in event.references" :key="reference.id" class="list-group-item">
              <a :href="publicPages.organization(reference.organization.id)">{{ reference.organization.name }}</a>
              <i
                v-if="reference.organization.is_verified"
                class="fa fa-check-circle text-primary ms-1"
                :title="t('Verified')"
              ></i>
            </span>
          </div>
          <div v-if="event.rights.can_reference_event" class="ms-3 mb-3">
            <a :href="publicPages.eventReference(event.id)" class="btn btn-outline-secondary"
              ><i class="fa fa-link"></i> {{ t("Reference event") }}</a
            >
          </div>
        </div>

        <div v-if="event.rights.can_create_reference_request" class="card mb-3" data-test="reference-requests">
          <div class="card-body pb-0">
            <h2 class="mt-0">{{ t("Reference requests") }}</h2>
          </div>
          <div class="list-group list-group-flush mb-4" style="max-height: 30vh; overflow-y: auto">
            <span v-for="request in event.reference_requests" :key="request.id" class="list-group-item">
              <a :href="manage.outgoingEventReferenceRequest(event.organization_id, request.id)">{{
                request.organization.name
              }}</a>
              <span
                v-if="request.review_status"
                :class="['badge', 'rounded-pill', 'ms-1', requestPill(request.review_status)]"
                >{{ request.review_status_label }}</span
              >
            </span>
          </div>
          <div class="ms-3 mb-3">
            <a
              :href="manage.eventReferenceRequestCreate(event.organization_id, event.id)"
              class="btn btn-outline-secondary"
              ><i class="fa fa-link"></i> {{ t("Request reference") }}</a
            >
          </div>
        </div>

        <div v-if="event.dates.length > 0" id="event-dates" class="card mb-3" data-test="dates">
          <div class="card-body pb-0">
            <h2 class="mt-0">{{ t("Event Dates") }}</h2>
          </div>
          <div class="list-group list-group-flush mb-4" style="max-height: 30vh; overflow-y: auto">
            <a
              v-for="date in event.dates"
              :key="date.id"
              :href="publicPages.eventDate(date.id)"
              class="list-group-item text-primary"
              >{{ formatEventDate(date.start, date.end, date.allday, boot.locale) }}</a
            >
          </div>
        </div>
      </div>
    </div>

    <ShareModal v-model="shareVisible" :links="event.share_links" />
    <CalendarExportModal v-model="calendarVisible" :links="event.calendar_links" />
  </div>
</template>

<style>
/* The old pages (Bootstrap 4) did not underline links. */
.event-detail a:not(.btn):not(.dropdown-item) {
  text-decoration: none;
}

.event-detail .card-body {
  padding: 1.25rem;
}
</style>
