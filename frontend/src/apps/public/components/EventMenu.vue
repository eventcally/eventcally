<script setup lang="ts">
import { BDropdown, BDropdownDivider, BDropdownItem } from "bootstrap-vue-next";
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import CalendarAssignModal from "@/shared/CalendarAssignModal.vue";
import { manage, publicPages } from "@/shared/legacy";

type Rights = components["schemas"]["PublicEventRights"];

const props = defineProps<{
  eventId: number;
  organizationId: number;
  rights: Rights;
  // The session's organization when it may put events into its calendars.
  calendarOrganizationId?: number | null;
}>();

const { t } = useI18n();

// The gear shows as soon as the user may do anything with the event.
const visible = computed(
  () => Object.values(props.rights).some(Boolean) || props.calendarOrganizationId != null,
);
const showCalendars = ref(false);
</script>

<template>
  <div v-if="visible" class="d-inline-block">
  <BDropdown variant="outline-secondary" end teleport-to="body" data-test="event-menu">
    <template #button-content><i class="fa fa-cog"></i></template>
    <template v-if="rights.can_update_event">
      <BDropdownItem :href="manage.eventUpdate(organizationId, eventId)"
        ><i class="fa fa-fw me-2 fa-edit"></i>{{ t("Edit event") }}</BDropdownItem
      >
      <BDropdownItem :href="manage.eventDelete(organizationId, eventId)"
        ><i class="fa fa-fw me-2 fa-trash"></i>{{ t("Delete event") }}&hellip;</BDropdownItem
      >
    </template>
    <BDropdownItem v-if="rights.can_duplicate_event" :href="manage.eventDuplicate(organizationId, eventId)"
      ><i class="fa fa-fw me-2 fa-copy"></i>{{ t("Duplicate event") }}</BDropdownItem
    >
    <BDropdownDivider />
    <BDropdownItem
      v-if="rights.can_create_reference_request"
      :href="manage.eventReferenceRequestCreate(organizationId, eventId)"
      ><i class="fa fa-fw me-2 fa-link"></i>{{ t("Request reference") }}</BDropdownItem
    >
    <BDropdownItem v-if="rights.can_reference_event" :href="publicPages.eventReference(eventId)"
      ><i class="fa fa-fw me-2 fa-link"></i>{{ t("Reference event") }}</BDropdownItem
    >
    <BDropdownItem v-if="calendarOrganizationId != null" data-test="add-to-calendar" @click="showCalendars = true"
      ><i class="fa fa-fw me-2 fa-calendar-plus"></i>{{ t("Add to calendar") }}</BDropdownItem
    >
    <BDropdownDivider />
    <BDropdownItem :href="publicPages.eventActions(eventId)">{{ t("More") }}&hellip;</BDropdownItem>
  </BDropdown>
  <CalendarAssignModal
    v-if="calendarOrganizationId != null"
    v-model="showCalendars"
    :organization-id="calendarOrganizationId"
    :event-id="eventId"
  />
  </div>
</template>
