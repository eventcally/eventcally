<script setup lang="ts">
import { BDropdown, BDropdownDivider, BDropdownItem } from "bootstrap-vue-next";
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { manage, publicPages } from "@/shared/legacy";

type Rights = components["schemas"]["PublicEventRights"];

const props = defineProps<{ eventId: number; organizationId: number; rights: Rights }>();

const { t } = useI18n();

// The gear shows as soon as the user may do anything with the event.
const visible = computed(() => Object.values(props.rights).some(Boolean));
</script>

<template>
  <BDropdown v-if="visible" variant="outline-secondary" end teleport-to="body" data-test="event-menu">
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
    <BDropdownDivider />
    <BDropdownItem :href="publicPages.eventActions(eventId)">{{ t("More") }}&hellip;</BDropdownItem>
  </BDropdown>
</template>
