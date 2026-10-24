<script setup lang="ts">
import { BModal } from "bootstrap-vue-next";
import { ref, watch } from "vue";
import { useI18n } from "vue-i18n";

defineProps<{
  acceptLabel: string;
  rejectLabel: string;
  rejectionReasons: { value: number; label: string }[];
  busy: boolean;
  error: string | null;
}>();

const emit = defineEmits<{
  accept: [];
  reject: [reason: number | null];
  reset: [];
}>();

const { t } = useI18n();

const acceptOpen = ref(false);
const rejectOpen = ref(false);
// 0 is "no reason".
const rejectionReason = ref(0);

// A server error belongs to the attempt that caused it, not to the next one.
watch([acceptOpen, rejectOpen], () => emit("reset"));

function reject() {
  emit("reject", rejectionReason.value || null);
}
</script>

<template>
  <div>
    <div class="d-flex justify-content-between my-4" data-test="decision">
      <button type="button" class="btn btn-success m-1" data-test="accept" @click="acceptOpen = true">
        <i class="fa fa-check"></i> {{ acceptLabel }}&hellip;
      </button>
      <button type="button" class="btn btn-danger m-1" data-test="reject" @click="rejectOpen = true">
        <i class="fa fa-ban"></i> {{ rejectLabel }}&hellip;
      </button>
    </div>

    <BModal
      v-model="acceptOpen"
      centered
      :title="acceptLabel"
      :no-close-on-backdrop="busy"
      data-test="accept-modal"
    >
      <div v-if="error && acceptOpen" class="alert alert-danger" role="alert" data-test="accept-error">
        {{ error }}
      </div>
      <slot name="accept-fields" />
      <template #footer>
        <button type="button" class="btn btn-secondary" :disabled="busy" @click="acceptOpen = false">
          {{ t("Cancel") }}
        </button>
        <button
          type="button"
          class="btn btn-success"
          data-test="accept-confirm"
          :disabled="busy"
          @click="emit('accept')"
        >
          {{ acceptLabel }}
        </button>
      </template>
    </BModal>

    <BModal
      v-model="rejectOpen"
      centered
      :title="rejectLabel"
      :no-close-on-backdrop="busy"
      data-test="reject-modal"
    >
      <div v-if="error && rejectOpen" class="alert alert-danger" role="alert" data-test="reject-error">
        {{ error }}
      </div>
      <div class="mb-3">
        <label class="form-label" for="rejection_reason">{{ t("Rejection reason") }}</label>
        <div class="text-body-secondary mb-1">{{ t("Choose why you rejected the request.") }}</div>
        <select id="rejection_reason" v-model.number="rejectionReason" class="form-select">
          <option v-for="reason in rejectionReasons" :key="reason.value" :value="reason.value">
            {{ reason.label }}
          </option>
        </select>
      </div>
      <template #footer>
        <button type="button" class="btn btn-secondary" :disabled="busy" @click="rejectOpen = false">
          {{ t("Cancel") }}
        </button>
        <button
          type="button"
          class="btn btn-danger"
          data-test="reject-confirm"
          :disabled="busy"
          @click="reject"
        >
          {{ rejectLabel }}
        </button>
      </template>
    </BModal>
  </div>
</template>
