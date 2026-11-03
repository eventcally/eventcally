<script setup lang="ts">
import { useI18n } from "vue-i18n";
import type { RouteLocationRaw } from "vue-router";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";

// "Profile" › ...: the trail of the old user views (`UserChildViewHandler`). The last item
// is the current page, the ones before link to their list.
defineProps<{ items: { label: string; to?: RouteLocationRaw }[] }>();

const { t } = useI18n();
</script>

<template>
  <AppBreadcrumb :items="[{ label: t('Profile'), to: { name: 'profile' } }, ...items]" />
</template>
