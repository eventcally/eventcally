<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import EventWarningPills from "@/shared/EventWarningPills.vue";
import { formatEventDate } from "@/shared/format";
import { publicPages } from "@/shared/legacy";

type EventDate = components["schemas"]["PublicEventDate"];

const props = defineProps<{ eventDate: EventDate; locale: string; busy?: boolean }>();
const emit = defineEmits<{
  "fly-to": [latitude: number, longitude: number];
  reference: [eventId: number];
  unreference: [referenceId: number];
}>();

const { t } = useI18n();

const event = computed(() => props.eventDate.event);
const photo = computed(() => event.value.photo);
const reference = computed(() => event.value.reference);
// The organizer usually carries the organization's name already.
const showOrganization = computed(() => event.value.organization.name !== event.value.organizer_name);
const coordinates = computed(() => {
  const place = event.value.place;
  return place && place.latitude != null && place.longitude != null
    ? { latitude: place.latitude, longitude: place.longitude }
    : null;
});

function flyTo() {
  if (coordinates.value) emit("fly-to", coordinates.value.latitude, coordinates.value.longitude);
}

function toggleReference() {
  const current = reference.value;
  if (current?.state === "none") emit("reference", event.value.id);
  else if (current?.state === "referenced" && current.reference_id != null)
    emit("unreference", current.reference_id);
}
</script>

<template>
  <div :id="`event_card_${eventDate.id}`" class="card mb-3 event-date-card">
    <div class="card-body">
      <div class="row flex-column-reverse flex-sm-row">
        <div class="col-sm" :class="{ 'col-sm-8': photo }">
          <h5 class="card-title">
            <a :href="publicPages.eventDate(eventDate.id)" class="text-body text-decoration-none">{{
              event.name
            }}</a>
            <span class="small align-middle ms-1"><EventWarningPills :event="event" /></span>
          </h5>
          <h6 class="card-subtitle mb-2 text-body">
            <i class="fa fa-calendar me-1"></i>
            {{ formatEventDate(eventDate.start, eventDate.end, eventDate.allday, locale) }}
          </h6>
          <p v-if="event.description_preview" class="card-text">{{ event.description_preview }}</p>
          <small v-if="event.organizer_name" class="text-muted me-2" data-test="organizer">
            <i class="fa fa-server me-1"></i>{{ event.organizer_name }}
          </small>
          <small v-if="showOrganization" class="text-muted me-2" data-test="organization">
            <i class="fa fa-database me-1"></i>{{ event.organization.name }}
          </small>
          <small v-if="event.place" class="text-muted">
            <i class="fa fa-map-marker me-1"></i>
            <a
              v-if="coordinates"
              href="#"
              class="text-secondary text-decoration-none"
              data-test="place"
              @click.prevent="flyTo"
            >
              {{ event.place.name }}
            </a>
            <template v-else>{{ event.place.name }}</template>
          </small>
        </div>
        <div v-if="photo" class="col-sm-4 mb-2 mb-sm-0 text-sm-end">
          <img
            :src="photo.url_200"
            :srcset="`${photo.url_200} 1x, ${photo.url_500} 2x`"
            :alt="t('Event image')"
            class="event-date-photo"
          />
          <div v-if="photo.copyright_text || photo.license_code" class="small text-muted" data-test="copyright">
            <template v-if="photo.copyright_text">&copy; {{ photo.copyright_text }}</template>
            <a
              v-if="photo.license_code && photo.license_url"
              :href="photo.license_url"
              target="_blank"
              rel="noopener noreferrer"
              class="ms-1"
              >{{ photo.license_code }}</a
            >
            <template v-else-if="photo.license_code"> {{ photo.license_code }}</template>
          </div>
        </div>
      </div>
    </div>
    <div v-if="reference" class="card-footer py-1">
      <button
        v-if="reference.state === 'own'"
        type="button"
        class="btn btn-link px-0 text-secondary text-decoration-none"
        disabled
        :title="t('Own events cannot be referenced')"
        data-test="reference-own"
      >
        <i class="fa fa-fw fa-link me-1"></i><span class="small">{{ t("Own event") }}</span>
      </button>
      <button
        v-else
        type="button"
        class="btn btn-link px-0 text-decoration-none"
        :class="reference.state === 'referenced' ? 'text-success' : 'text-primary'"
        :title="reference.state === 'referenced' ? t('Delete reference') : t('Reference event')"
        :disabled="busy"
        :data-test="`reference-${reference.state}`"
        @click="toggleReference"
      >
        <i class="fa fa-fw fa-link me-1"></i>
        <span class="small">{{
          reference.state === "referenced" ? t("Referenced") : t("Not referenced")
        }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.event-date-photo {
  object-fit: contain;
  width: 160px;
  height: 160px;
  max-width: 100%;
}

.event-date-card.highlight {
  animation: event-date-highlight 1.2s ease-out;
}

@keyframes event-date-highlight {
  from {
    box-shadow: 0 0 0 0.35rem var(--bs-warning);
  }
  to {
    box-shadow: 0 0 0 0 transparent;
  }
}
</style>
