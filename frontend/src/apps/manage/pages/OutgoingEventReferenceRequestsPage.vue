<script setup lang="ts">
import EventReferenceRequestsList from "../components/EventReferenceRequestsList.vue";

defineProps<{ organizationId: number }>();
</script>

<template>
  <EventReferenceRequestsList :organization-id="organizationId" :incoming="false" />
</template>
