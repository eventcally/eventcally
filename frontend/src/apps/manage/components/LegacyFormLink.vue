<script setup lang="ts">
import { useI18n } from "vue-i18n";

defineProps<{ href: string }>();

const { t } = useI18n();
</script>

<template>
  <div class="alert alert-secondary py-2 small d-flex flex-wrap gap-1" data-test="legacy-form-link">
    <span>{{ t("This is the new form.") }}</span>
    <a :href="href">{{ t("Open the previous form") }}</a>
  </div>
</template>
