<script setup lang="ts">
import { BModal, BOverlay } from "bootstrap-vue-next";
import { ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";
import { toFieldErrors } from "@/shared/fieldErrors";
import {
  EVENT_ORGANIZER_FORM_FIELDS,
  eventOrganizerSaveBody,
  type EventOrganizerFormValue,
} from "../eventOrganizerForm";
import { emptyLocation } from "../eventPlaceForm";
import EventOrganizerFormFields from "./EventOrganizerFormFields.vue";

const props = defineProps<{ organizationId: number }>();
const show = defineModel<boolean>({ default: false });
const emit = defineEmits<{ created: [organizer: { id: number; name: string }] }>();

const { t } = useI18n();

const loading = ref(false);
const saving = ref(false);
const error = ref<string | null>(null);
const licenses = ref<{ id: number; name: string }[] | null>(null);
const form = ref<EventOrganizerFormValue>(emptyForm());
const logoPreview = ref<string | null>(null);
const errors = ref<Record<string, string>>({});

function emptyForm(): EventOrganizerFormValue {
  return {
    name: "",
    url: "",
    email: "",
    phone: "",
    fax: "",
    location: emptyLocation(),
    logo: null,
  };
}

function reset() {
  form.value = emptyForm();
  logoPreview.value = null;
  errors.value = {};
  error.value = null;
  saving.value = false;
}

async function load() {
  if (licenses.value) return;
  loading.value = true;
  const { data, error: err } = await api.GET(
    "/bff/manage/organizations/{id}/event-organizers/create-form",
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

  const { data, error: err } = await api.POST("/bff/manage/organizations/{id}/event-organizers", {
    params: { path: { id: props.organizationId } },
    body: eventOrganizerSaveBody(form.value, true),
  });
  saving.value = false;

  if (data) {
    emit("created", { id: data.id, name: form.value.name.trim() });
    show.value = false;
    return;
  }

  if (err && "errors" in err) {
    const mapped = toFieldErrors(err.errors, EVENT_ORGANIZER_FORM_FIELDS);
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
    :title="t('Create organizer')"
    size="lg"
    lazy
    unmount-lazy
    :ok-title="t('Create organizer')"
    :ok-disabled="saving || !licenses"
    :cancel-title="t('Cancel')"
    data-test="event-organizer-create-modal"
    @ok.prevent="save"
  >
    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>
    <BOverlay :show="loading">
      <form v-if="licenses" @submit.prevent="save">
        <EventOrganizerFormFields
          v-model="form"
          v-model:errors="errors"
          v-model:logo-preview="logoPreview"
          :organization-id="organizationId"
          :licenses="licenses"
          id-prefix="new_organizer-"
        />
      </form>
    </BOverlay>
  </BModal>
</template>
