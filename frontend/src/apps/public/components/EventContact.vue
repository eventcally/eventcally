<script setup lang="ts">
import { useI18n } from "vue-i18n";
import EventProp from "./EventProp.vue";
import { ensureLinkScheme } from "@/shared/format";

// Link, e-mail, phone, fax and address lines of an organizer, an organization or a place.
defineProps<{
  url?: string | null;
  email?: string | null;
  phone?: string | null;
  fax?: string | null;
  address?: string | null;
}>();

const { t } = useI18n();
</script>

<template>
  <EventProp v-if="url" icon="fa-link" :title="t('Link')"
    ><a :href="ensureLinkScheme(url)" target="_blank" rel="noopener" style="word-break: break-all">{{
      url
    }}</a></EventProp
  >
  <EventProp v-if="email" icon="fa-envelope" :title="t('Email')"
    ><a :href="`mailto:${email}`">{{ email }}</a></EventProp
  >
  <EventProp v-if="phone" icon="fa-phone" :title="t('Phone')"
    ><a :href="`tel:${phone}`">{{ phone }}</a></EventProp
  >
  <EventProp v-if="fax" icon="fa-fax" :title="t('Fax')">{{ fax }}</EventProp>
  <EventProp v-if="address" icon="fa-map-marker" :title="t('Location')">{{ address }}</EventProp>
</template>
