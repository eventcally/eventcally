<script setup lang="ts">
import { BModal } from "bootstrap-vue-next";
import { ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";
import { errorMessage } from "@/shared/apiError";
import { useNotify } from "@/shared/notify";

// The rating edit of an incoming event reference (the old update page) in a modal.
const props = defineProps<{
  organizationId: number;
  referenceId: number | null;
  rating: number | null;
  choices: { value: number; label: string }[];
}>();
const show = defineModel<boolean>({ default: false });
const emit = defineEmits<{ saved: [] }>();

const { t } = useI18n();
const notify = useNotify();

const DEFAULT_RATING = 50;
const value = ref(DEFAULT_RATING);
const busy = ref(false);
const error = ref<string | null>(null);

// Every opening starts with the current rating.
watch(show, (open) => {
  if (open) {
    value.value = props.rating ?? DEFAULT_RATING;
    error.value = null;
  }
});

async function save() {
  if (busy.value || props.referenceId === null) return;
  busy.value = true;
  error.value = null;

  const { data, error: err } = await api.PUT(
    "/bff/manage/organizations/{id}/incoming-event-references/{reference_id}",
    {
      params: { path: { id: props.organizationId, reference_id: props.referenceId } },
      body: { rating: value.value },
    },
  );
  busy.value = false;

  if (!data) {
    error.value = errorMessage(err, t("Error"));
    return;
  }

  notify.success(data.message);
  show.value = false;
  emit("saved");
}
</script>

<template>
  <BModal
    v-model="show"
    :title="t('Update %(model_display_name)s', { model_display_name: t('Incoming reference') })"
    :ok-title="t('Update reference')"
    :cancel-title="t('Cancel')"
    :ok-disabled="busy"
    @ok.prevent="save"
  >
    <div v-if="error" class="alert alert-danger" role="alert" data-test="rating-error">
      {{ error }}
    </div>
    <div class="mb-3">
      <label class="form-label" for="rating">{{ t("Rating") }}</label>
      <select id="rating" v-model="value" class="form-select">
        <option v-for="choice in choices" :key="choice.value" :value="choice.value">
          {{ choice.label }}
        </option>
      </select>
      <div class="form-text">
        {{
          t(
            "Choose how relevant the event is to your organization. The value is not visible and is used for sorting.",
          )
        }}
      </div>
    </div>
  </BModal>
</template>
