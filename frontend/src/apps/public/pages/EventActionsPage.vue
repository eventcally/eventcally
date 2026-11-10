<script setup lang="ts">
import { BOverlay } from "bootstrap-vue-next";
import { onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import CalendarAssignModal from "@/shared/CalendarAssignModal.vue";
import { manage, publicPages } from "@/shared/legacy";
import ShareModal from "@/shared/ShareModal.vue";

type PublicEventDetail = components["schemas"]["PublicEventDetail"];

const props = defineProps<{ id: number }>();

const { t } = useI18n();

const event = ref<PublicEventDetail | null>(null);
const loading = ref(false);
const loadError = ref<string | null>(null);
const shareVisible = ref(false);
const calendarVisible = ref(false);

async function load() {
  loading.value = true;
  loadError.value = null;
  const { data, error } = await api.GET("/bff/public/events/{id}", {
    params: { path: { id: props.id } },
  });
  if (data) event.value = data;
  else loadError.value = error?.message ?? t("Error");
  loading.value = false;
}

onMounted(load);
</script>

<template>
  <div>
    <div v-if="loadError" class="alert alert-danger" role="alert">{{ loadError }}</div>

    <BOverlay :show="loading">
      <div v-if="event" class="w-normal event-actions">
        <h5 class="card-title mb-3">{{ t("Actions for event") }}</h5>

        <div>
          <i class="fa fa-fw me-1 fa-link" :title="t('Event')"></i>
          <a :href="publicPages.event(event.id)">{{ event.name }}</a>
        </div>

        <div class="list-group mt-4">
          <a
            v-if="event.rights.can_create_reference_request"
            class="list-group-item list-group-item-action"
            :href="manage.eventReferenceRequestCreate(event.organization_id, event.id)"
          >
            <p class="mb-1"><i class="fa fa-link"></i> {{ t("Request reference") }}</p>
            <small>{{ t("Ask another organization to reference your event on their calendar.") }}</small>
          </a>
          <a
            v-if="event.rights.can_reference_event"
            class="list-group-item list-group-item-action"
            :href="publicPages.eventReference(event.id)"
          >
            <p class="mb-1"><i class="fa fa-link"></i> {{ t("Reference event") }}</p>
            <small>{{ t("Reference this event on your organization's calendar.") }}</small>
          </a>
        </div>

        <div v-if="event.calendar_organization" class="list-group mt-4">
          <button
            type="button"
            class="list-group-item list-group-item-action"
            data-test="add-to-calendar"
            @click="calendarVisible = true"
          >
            <p class="mb-1"><i class="fa fa-calendar-plus"></i> {{ t("Add to calendar") }}</p>
            <small>{{ t("Put this event into calendars of your organization.") }}</small>
          </button>
        </div>

        <CalendarAssignModal
          v-if="event.calendar_organization"
          v-model="calendarVisible"
          :organization-id="event.calendar_organization.id"
          :event-id="event.id"
        />

        <div class="list-group mt-4">
          <button type="button" class="list-group-item list-group-item-action" @click="shareVisible = true">
            <i class="fa fa-share-alt"></i> {{ t("Share") }}
          </button>
        </div>

        <ShareModal v-model="shareVisible" :links="event.share_links" />

        <div class="list-group mt-4">
          <a
            v-if="event.rights.can_duplicate_event"
            class="list-group-item list-group-item-action"
            :href="manage.eventDuplicate(event.organization_id, event.id)"
            ><i class="fa fa-copy"></i> {{ t("Duplicate event") }}</a
          >
          <template v-if="event.rights.can_create_event">
            <a class="list-group-item list-group-item-action" :href="manage.eventCreate(event.organization_id)"
              ><i class="fa fa-plus"></i>
              {{ t("Create another event for %(admin_unit_name)s", { admin_unit_name: event.organization.name }) }}</a
            >
            <a class="list-group-item list-group-item-action" :href="manage.events(event.organization_id)"
              ><i class="fa fa-list"></i>
              {{ t("List all events of %(admin_unit_name)s", { admin_unit_name: event.organization.name }) }}</a
            >
          </template>
          <template v-if="event.rights.can_update_event">
            <a
              class="list-group-item list-group-item-action"
              :href="manage.eventUpdate(event.organization_id, event.id)"
              ><i class="fa fa-edit"></i> {{ t("Edit event") }}</a
            >
            <a
              class="list-group-item list-group-item-action"
              :href="manage.eventDelete(event.organization_id, event.id)"
              ><i class="fa fa-trash"></i> {{ t("Delete event") }}</a
            >
          </template>
        </div>
      </div>
    </BOverlay>
  </div>
</template>

<style>
/* Match the old (Bootstrap 4) action list. */
.event-actions .list-group-item {
  padding: 0.75rem 1.25rem;
}
.event-actions a {
  text-decoration: none;
}
</style>
