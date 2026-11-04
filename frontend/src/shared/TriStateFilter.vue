<script setup lang="ts">
import { useI18n } from "vue-i18n";

// The old boolean list filter: All / Yes / No as radio buttons. The value is "" (all),
// "1" or "0", the form the list URLs always used.
defineProps<{ id: string; label: string }>();
const value = defineModel<"" | "1" | "0">({ default: "" });

const { t } = useI18n();
</script>

<template>
  <fieldset class="mb-3 px-0" :data-test="`${id}-filter`">
    <legend class="col-form-label pt-0">{{ label }}</legend>
    <div class="form-check form-check-inline">
      <input :id="`${id}-all`" v-model="value" class="form-check-input" type="radio" value="" />
      <label class="form-check-label" :for="`${id}-all`">{{ t("All") }}</label>
    </div>
    <div class="form-check form-check-inline">
      <input :id="`${id}-yes`" v-model="value" class="form-check-input" type="radio" value="1" />
      <label class="form-check-label" :for="`${id}-yes`">{{ t("Yes") }}</label>
    </div>
    <div class="form-check form-check-inline">
      <input :id="`${id}-no`" v-model="value" class="form-check-input" type="radio" value="0" />
      <label class="form-check-label" :for="`${id}-no`">{{ t("No") }}</label>
    </div>
  </fieldset>
</template>
