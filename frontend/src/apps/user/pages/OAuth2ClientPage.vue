<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AuditLine from "@/shared/AuditLine.vue";
import OAuth2ClientDetails from "@/shared/OAuth2ClientDetails.vue";
import { errorMessage } from "../apiError";
import ProfileBreadcrumb from "../components/ProfileBreadcrumb.vue";
import { useFlashNotice } from "../useFlashNotice";

type UserOAuth2ClientDetail = components["schemas"]["UserOAuth2ClientDetail"];

const props = defineProps<{ id: number }>();

const { t } = useI18n();

useFlashNotice();

const client = ref<UserOAuth2ClientDetail | null>(null);
const error = ref<string | null>(null);

onMounted(async () => {
  const { data, error: err } = await api.GET("/bff/user/oauth2-clients/{id}", {
    params: { path: { id: props.id } },
  });
  if (data) client.value = data;
  else error.value = errorMessage(err, t("Error"));
});
</script>

<template>
  <div>
    <ProfileBreadcrumb
      :items="[
        { label: t('OAuth2 clients'), to: { name: 'oauth2-clients' } },
        { label: client?.client_name ?? `${t('OAuth2 client')} ${id}` },
      ]"
    />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <template v-if="client">
      <div class="mb-4">
        <router-link
          :to="{ name: 'oauth2-client-update', params: { clientId: id } }"
          class="btn btn-outline-secondary me-2"
        >
          {{ t("Update") }}
        </router-link>
        <router-link
          :to="{ name: 'oauth2-client-delete', params: { clientId: id } }"
          class="btn btn-outline-danger"
        >
          {{ t("Delete") }}
        </router-link>
      </div>

      <OAuth2ClientDetails :client="client" />
      <AuditLine :audit="client.audit" />
    </template>
  </div>
</template>
