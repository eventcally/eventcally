<script setup lang="ts">
import { useI18n } from "vue-i18n";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";

const { t } = useI18n();
</script>

<template>
  <div>
    <AppBreadcrumb :items="[{ label: t('Admin'), to: { name: 'home' } }]" />
    <div class="alert alert-warning" role="alert">
      {{ t("The requested resource was not found") }}
    </div>
  </div>
</template>
