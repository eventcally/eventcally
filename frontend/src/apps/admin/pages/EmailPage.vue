<script setup lang="ts">
import { BFormGroup, BFormInput, BOverlay } from "bootstrap-vue-next";
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";
import { useNotify } from "@/shared/notify";
import MailJobProgress from "../components/MailJobProgress.vue";
import { useMailJob } from "../composables/useMailJob";

type MailConfig = components["schemas"]["AdminMailConfig"];

const { t } = useI18n();
const notify = useNotify();
const { job, track, reset } = useMailJob();

const config = ref<MailConfig | null>(null);
const loading = ref(false);
const loadError = ref<string | null>(null);

const recipient = ref("");
const sending = ref(false);
const sendError = ref<string | null>(null);
const recipientError = ref<string | null>(null);

const busy = computed(() => sending.value || job.state === "running");

const yesNo = (value: boolean) => (value ? t("Yes") : t("No"));
const orNotSpecified = (value: string | number | null) =>
  value === null || value === "" ? t("Not specified") : String(value);

const rows = computed(() => {
  const c = config.value;
  if (!c) return [];
  return [
    { key: "MAIL_SUPPRESS_SEND", value: yesNo(c.suppress_send) },
    { key: "MAIL_SERVER", value: orNotSpecified(c.server) },
    { key: "MAIL_PORT", value: orNotSpecified(c.port) },
    { key: "MAIL_USE_TLS", value: yesNo(c.use_tls) },
    { key: "MAIL_USE_SSL", value: yesNo(c.use_ssl) },
    { key: "MAIL_USERNAME", value: orNotSpecified(c.username) },
    // Only whether a password is set ever reaches the browser.
    { key: "MAIL_PASSWORD", value: c.password_set ? "••••••" : t("Not specified") },
    { key: "MAIL_DEFAULT_SENDER", value: orNotSpecified(c.default_sender) },
  ];
});

async function load() {
  loading.value = true;
  loadError.value = null;
  const { data, error } = await api.GET("/bff/admin/email");
  if (data) config.value = data;
  else loadError.value = error?.message ?? t("Error");
  loading.value = false;
}

async function send(asynchronous: boolean) {
  if (busy.value) return;

  sending.value = true;
  sendError.value = null;
  recipientError.value = null;
  reset();

  const { data, error } = await api.POST("/bff/admin/email/test", {
    body: { recipient: recipient.value, asynchronous },
  });
  sending.value = false;

  if (!data) {
    if (error && "errors" in error) {
      const field = error.errors.find((e) => e.loc[0] === "recipient");
      if (field) recipientError.value = field.msg;
      else sendError.value = error.errors.map((e) => e.msg).join(" ");
    } else {
      sendError.value = error?.message ?? t("Error");
    }
    return;
  }

  if (asynchronous) track(data);
  else notify.success(t("Mail sent successfully"));
}

onMounted(load);
</script>

<template>
  <div>
    <AppBreadcrumb
      :items="[{ label: t('Admin'), to: { name: 'home' } }, { label: t('Email') }]"
    />

    <div v-if="loadError" class="alert alert-danger" role="alert">{{ loadError }}</div>

    <BOverlay :show="loading">
      <table v-if="config" class="table table-striped table-bordered my-4 mail-config">
        <tbody>
          <tr v-for="row in rows" :key="row.key">
            <td>{{ row.key }}</td>
            <td>{{ row.value }}</td>
          </tr>
        </tbody>
      </table>
    </BOverlay>

    <h4>{{ t("Test mail") }}</h4>

    <div v-if="sendError" class="alert alert-danger" role="alert">{{ sendError }}</div>

    <form @submit.prevent="send(false)">
      <BFormGroup
        class="mb-3"
        :label="`${t('Recipient')} *`"
        label-for="test-mail-recipient"
        :state="recipientError ? false : null"
        :invalid-feedback="recipientError ?? ''"
      >
        <BFormInput
          id="test-mail-recipient"
          v-model="recipient"
          type="email"
          required
          :state="recipientError ? false : null"
        />
      </BFormGroup>

      <MailJobProgress :job="job" />

      <button type="submit" class="btn btn-primary" :disabled="busy">
        {{ t("Send test mail synchronously") }}
      </button>
      <p class="mt-3">
        <button type="button" class="btn btn-outline-primary" :disabled="busy" @click="send(true)">
          {{ t("Send test mail asynchronously") }}
        </button>
      </p>
    </form>
  </div>
</template>
