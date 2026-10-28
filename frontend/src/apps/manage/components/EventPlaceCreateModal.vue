<script setup lang="ts">
import { BModal, BOverlay } from "bootstrap-vue-next";
import { ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";
import { toFieldErrors } from "@/shared/fieldErrors";
import {
  EVENT_PLACE_FORM_FIELDS,
  emptyLocation,
  eventPlaceLabel,
  eventPlaceSaveBody,
  type EventPlaceFormValue,
} from "../eventPlaceForm";
import EventPlaceFormFields from "./EventPlaceFormFields.vue";

const props = defineProps<{ organizationId: number }>();
const show = defineModel<boolean>({ default: false });
const emit = defineEmits<{ created: [place: { id: number; name: string }] }>();

const { t } = useI18n();

const loading = ref(false);
const saving = ref(false);
const error = ref<string | null>(null);
const licenses = ref<{ id: number; name: string }[] | null>(null);
const form = ref<EventPlaceFormValue>(emptyForm());
const photoPreview = ref<string | null>(null);
const errors = ref<Record<string, string>>({});

function emptyForm(): EventPlaceFormValue {
  return { name: "", url: "", description: "", location: emptyLocation(), photo: null };
}

function reset() {
  form.value = emptyForm();
  photoPreview.value = null;
  errors.value = {};
  error.value = null;
  saving.value = false;
}

async function load() {
  if (licenses.value) return;
  loading.value = true;
  const { data, error: err } = await api.GET(
    "/bff/manage/organizations/{id}/event-places/create-form",
    { params: { path: { id: props.organizationId } } },
  );
  loading.value = false;
  if (!data) {
    error.value = err?.message ?? t("Error");
    return;
  }
  licenses.value = data.licenses;
}

async function save() {
  if (saving.value || !licenses.value) return;

  saving.value = true;
  error.value = null;
  errors.value = {};

  const { data, error: err } = await api.POST("/bff/manage/organizations/{id}/event-places", {
    params: { path: { id: props.organizationId } },
    body: eventPlaceSaveBody(form.value, true),
  });
  saving.value = false;

  if (data) {
    emit("created", { id: data.id, name: eventPlaceLabel(form.value) });
    show.value = false;
    return;
  }

  if (err && "errors" in err) {
    const mapped = toFieldErrors(err.errors, EVENT_PLACE_FORM_FIELDS);
    errors.value = mapped.byKey;
    if (mapped.unmatched.length) error.value = mapped.unmatched.join(" ");
  } else {
    error.value = err?.message ?? t("Error");
  }
}

watch(show, (value) => {
  if (value) load();
  else reset();
});
</script>

<template>
  <BModal
    v-model="show"
    :title="t('Create place')"
    size="lg"
    lazy
    unmount-lazy
    :ok-title="t('Create place')"
    :ok-disabled="saving || !licenses"
    :cancel-title="t('Cancel')"
    data-test="event-place-create-modal"
    @ok.prevent="save"
  >
    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>
    <BOverlay :show="loading">
      <form v-if="licenses" @submit.prevent="save">
        <EventPlaceFormFields
          v-model="form"
          v-model:errors="errors"
          v-model:photo-preview="photoPreview"
          :organization-id="organizationId"
          :licenses="licenses"
          id-prefix="new_event_place-"
        />
      </form>
    </BOverlay>
  </BModal>
</template>
