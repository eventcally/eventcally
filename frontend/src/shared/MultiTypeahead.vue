<script setup lang="ts">
import { ref } from "vue";
import { useI18n } from "vue-i18n";
import AppTypeahead from "./AppTypeahead.vue";

interface Option {
  id: number;
  name: string;
}

const props = defineProps<{
  fetch: (keyword: string) => Promise<Option[]>;
  placeholder?: string;
  inputId?: string;
  state?: boolean | null;
}>();
const model = defineModel<Option[]>({ default: () => [] });

const { t } = useI18n();
// Remounts the typeahead after a pick so its input is empty again.
const pickCount = ref(0);

async function fetchUnselected(keyword: string) {
  const options = await props.fetch(keyword);
  return options.filter((option) => !model.value.some((item) => item.id === option.id));
}

function add(option: Option | null) {
  if (!option) return;
  pickCount.value++;
  if (model.value.some((item) => item.id === option.id)) return;
  model.value = [...model.value, option];
}

function remove(option: Option) {
  model.value = model.value.filter((item) => item.id !== option.id);
}
</script>

<template>
  <div class="multi-typeahead" :class="{ 'is-invalid': state === false }">
    <div v-if="model.length" class="d-flex flex-wrap gap-1 mb-1" data-test="selected">
      <span
        v-for="item in model"
        :key="item.id"
        class="badge text-bg-secondary d-inline-flex align-items-center fw-normal fs-6"
        data-test="chip"
      >
        {{ item.name }}
        <button
          type="button"
          class="btn-close btn-close-white ms-1"
          style="font-size: 0.6em"
          :aria-label="t('Remove')"
          data-test="remove"
          @click="remove(item)"
        ></button>
      </span>
    </div>
    <AppTypeahead
      :key="pickCount"
      :model-value="null"
      :fetch="fetchUnselected"
      :placeholder="placeholder"
      :input-id="inputId"
      @update:model-value="add"
    />
  </div>
</template>
