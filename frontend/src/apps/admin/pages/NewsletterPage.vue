<script setup lang="ts">
import {
  BFormGroup,
  BFormInput,
  BFormRadio,
  BFormRadioGroup,
  BFormTextarea,
} from "bootstrap-vue-next";
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";
import MailJobProgress from "../components/MailJobProgress.vue";
import NewsletterConfirmModal from "../components/NewsletterConfirmModal.vue";
import { useMailJob } from "../composables/useMailJob";

type Audience = "test" | "all";

const { t } = useI18n();
const { job, track, reset } = useMailJob();

const audience = ref<Audience>("test");
const testRecipient = ref("");
const message = ref("");
const sending = ref(false);
const showConfirm = ref(false);
const error = ref<string | null>(null);
const fieldErrors = ref<Record<string, string>>({});

const busy = computed(() => sending.value || job.state === "running");

function submit() {
  if (busy.value) return;
  // Everyone is only mailed after the confirmation that shows the recipient count.
  if (audience.value === "all") showConfirm.value = true;
  else void send();
}

async function send() {
  sending.value = true;
  error.value = null;
  fieldErrors.value = {};
  reset();

  const { data, error: err } = await api.POST("/bff/admin/newsletter", {
    body: {
      audience: audience.value,
      test_recipient: audience.value === "test" ? testRecipient.value : null,
      message: message.value,
    },
  });
  sending.value = false;

  if (data) {
    track(data);
    if (data.count === 0) {
      error.value = t("There are no recipients.");
      reset();
    }
    return;
  }

  if (err && "errors" in err) {
    const unmapped: string[] = [];
    for (const e of err.errors) {
      const field = e.loc[0];
      if (field === "test_recipient" || field === "message") fieldErrors.value[field] = e.msg;
      else unmapped.push(e.msg);
    }
    if (unmapped.length) error.value = unmapped.join(" ");
  } else {
    error.value = err?.message ?? t("Error");
  }
}
</script>

<template>
  <div>
    <AppBreadcrumb
      :items="[{ label: t('Admin'), to: { name: 'home' } }, { label: t('Newsletter') }]"
    />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <form @submit.prevent="submit">
      <fieldset :disabled="busy">
        <BFormGroup class="my-4">
          <BFormRadioGroup v-model="audience" stacked name="audience">
            <BFormRadio value="test">{{ t("Test recipient") }}</BFormRadio>
            <BFormRadio value="all">
              {{ t("All users with enabled newsletter setting") }}
            </BFormRadio>
          </BFormRadioGroup>
        </BFormGroup>

        <BFormGroup
          v-if="audience === 'test'"
          class="mb-3"
          :label="`${t('Test recipient')} *`"
          label-for="newsletter-test-recipient"
          :state="fieldErrors.test_recipient ? false : null"
          :invalid-feedback="fieldErrors.test_recipient ?? ''"
        >
          <BFormInput
            id="newsletter-test-recipient"
            v-model="testRecipient"
            type="email"
            required
            :state="fieldErrors.test_recipient ? false : null"
          />
        </BFormGroup>

        <BFormGroup
          class="mb-3"
          :label="`${t('Message')} *`"
          label-for="newsletter-message"
          :state="fieldErrors.message ? false : null"
          :invalid-feedback="fieldErrors.message ?? ''"
        >
          <BFormTextarea
            id="newsletter-message"
            v-model="message"
            :rows="10"
            required
            :state="fieldErrors.message ? false : null"
          />
        </BFormGroup>
      </fieldset>

      <MailJobProgress :job="job" />

      <button type="submit" class="btn btn-primary" :disabled="busy">
        {{ t("Send newsletter") }}
      </button>
    </form>

    <NewsletterConfirmModal v-model="showConfirm" @confirm="send" />
  </div>
</template>
