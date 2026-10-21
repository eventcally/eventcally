<script setup lang="ts">
import {
  BFormGroup,
  BFormInput,
  BFormTextarea,
  BOverlay,
  BSpinner,
} from "bootstrap-vue-next";
import { onMounted, reactive, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import { publicPages } from "@/shared/legacy";
import { useNotify } from "@/shared/notify";

type EventReportForm = components["schemas"]["EventReportForm"];

const props = defineProps<{ id: number }>();

const { t } = useI18n();
const notify = useNotify();

const form = ref<EventReportForm | null>(null);
const loading = ref(false);
const loadError = ref<string | null>(null);

const values = reactive({ contact_name: "", contact_email: "", message: "" });
const fieldErrors = reactive<Record<string, string | undefined>>({});
const sending = ref(false);
const sendError = ref<string | null>(null);
const submitted = ref(false);

async function load() {
  loading.value = true;
  loadError.value = null;
  const { data, error } = await api.GET("/bff/public/events/{id}/report-form", {
    params: { path: { id: props.id } },
  });
  if (data) form.value = data;
  else loadError.value = error?.message ?? t("Error");
  loading.value = false;
}

async function submit() {
  if (sending.value) return;

  sending.value = true;
  sendError.value = null;
  for (const key of Object.keys(fieldErrors)) delete fieldErrors[key];

  const { error, response } = await api.POST("/bff/public/events/{id}/reports", {
    params: { path: { id: props.id } },
    body: { ...values },
  });
  sending.value = false;

  if (!error && response.ok) {
    notify.success(t("Event successfully reported"));
    submitted.value = true;
    return;
  }

  if (error && "errors" in error) {
    const unmatched: string[] = [];
    for (const e of error.errors) {
      if (e.loc[0] in values) fieldErrors[e.loc[0]] = e.msg;
      else unmatched.push(e.msg);
    }
    if (unmatched.length) sendError.value = unmatched.join(" ");
  } else {
    sendError.value = error?.message ?? t("Error");
  }
}

onMounted(load);
</script>

<template>
  <div>
    <h1 class="h3 mb-3">{{ t("Report event") }}</h1>

    <div v-if="loadError" class="alert alert-danger" role="alert">{{ loadError }}</div>

    <BOverlay :show="loading">
      <div v-if="form">
        <p>
          <a :href="publicPages.event(form.event_id)">{{ form.event_name }}</a>
        </p>

        <div v-if="submitted" class="alert alert-success" role="alert">
          {{ t("Event successfully reported") }}
        </div>

        <form v-else @submit.prevent="submit">
          <div v-if="sendError" class="alert alert-danger" role="alert">{{ sendError }}</div>

          <BFormGroup
            class="mb-3"
            :label="`${t('Name')} *`"
            label-for="report-contact-name"
            :description="t('First and last name')"
            :state="fieldErrors.contact_name ? false : null"
            :invalid-feedback="fieldErrors.contact_name ?? ''"
          >
            <BFormInput
              id="report-contact-name"
              v-model="values.contact_name"
              name="contactName"
              required
              minlength="5"
              maxlength="255"
              :state="fieldErrors.contact_name ? false : null"
            />
          </BFormGroup>

          <BFormGroup
            class="mb-3"
            :label="`${t('Email address')} *`"
            label-for="report-contact-email"
            :state="fieldErrors.contact_email ? false : null"
            :invalid-feedback="fieldErrors.contact_email ?? ''"
          >
            <BFormInput
              id="report-contact-email"
              v-model="values.contact_email"
              name="contactEmail"
              type="email"
              required
              maxlength="255"
              :state="fieldErrors.contact_email ? false : null"
            />
          </BFormGroup>

          <BFormGroup
            class="mb-3"
            :label="`${t('Message')} *`"
            label-for="report-message"
            :description="t('Briefly describe in your words why the event is objectionable.')"
            :state="fieldErrors.message ? false : null"
            :invalid-feedback="fieldErrors.message ?? ''"
          >
            <BFormTextarea
              id="report-message"
              v-model="values.message"
              name="message"
              rows="4"
              required
              minlength="20"
              maxlength="1000"
              :state="fieldErrors.message ? false : null"
            />
          </BFormGroup>

          <button type="submit" class="btn btn-primary" :disabled="sending">
            <BSpinner v-if="sending" small class="me-1" />
            {{ t("Submit") }}
          </button>
        </form>
      </div>
    </BOverlay>
  </div>
</template>
