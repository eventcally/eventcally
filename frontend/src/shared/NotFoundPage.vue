<script setup lang="ts">
import { useI18n } from "vue-i18n";

const { t } = useI18n();
</script>

<template>
  <div class="alert alert-warning" role="alert">
    {{ t("The requested resource was not found") }}
  </div>
</template>
