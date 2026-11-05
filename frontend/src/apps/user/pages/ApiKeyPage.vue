<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AuditLine from "@/shared/AuditLine.vue";
import { boot } from "@/shared/boot";
import { takeCreatedKey } from "@/shared/createdKey";
import { formatDate } from "@/shared/format";
import { errorMessage } from "@/shared/apiError";
import ProfileBreadcrumb from "../components/ProfileBreadcrumb.vue";
import { useFlashNotice } from "@/shared/useFlashNotice";

type UserApiKeyDetail = components["schemas"]["UserApiKeyDetail"];

const props = defineProps<{ id: number }>();

const { t } = useI18n();

useFlashNotice();

const apiKey = ref<UserApiKeyDetail | null>(null);
const error = ref<string | null>(null);

// The key is only known right after the creation (the create page hands it over through
// the history state). It is taken out of the state, so a reload or any later visit never
// shows it.
const createdKey = takeCreatedKey();

const title = computed(() => `${t("API key")} ${props.id}`);

onMounted(async () => {
  const { data, error: err } = await api.GET("/bff/user/api-keys/{id}", {
    params: { path: { id: props.id } },
  });
  if (data) apiKey.value = data;
  else error.value = errorMessage(err, t("Error"));
});
</script>

<template>
  <div>
    <div v-if="createdKey" class="alert alert-success" role="status">
      {{
        t("%(model_display_name)s successfully created", {
          model_display_name: t("API key"),
        })
      }}
    </div>
    <div v-if="createdKey" class="alert alert-warning" role="alert" data-test="created-key">
      {{
        t("Please note the key: %(key)s. It will only be displayed once.", {
          key: createdKey,
        })
      }}
    </div>

    <ProfileBreadcrumb
      :items="[{ label: t('API keys'), to: { name: 'api-keys' } }, { label: title }]"
    />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <template v-if="apiKey">
      <div class="mb-4">
        <router-link
          :to="{ name: 'api-key-update', params: { apiKeyId: id } }"
          class="btn btn-outline-secondary me-2"
        >
          {{ t("Update") }}
        </router-link>
        <router-link
          :to="{ name: 'api-key-delete', params: { apiKeyId: id } }"
          class="btn btn-outline-danger"
        >
          {{ t("Delete") }}
        </router-link>
      </div>

      <dl class="row">
        <dt class="col-sm-3">{{ t("Name") }}</dt>
        <dd class="col-sm-9">{{ apiKey.name }}</dd>
        <dt class="col-sm-3">{{ t("Rate limit") }}</dt>
        <dd class="col-sm-9">
          <div v-for="row in apiKey.rate_limits" :key="row">{{ row }}</div>
        </dd>
        <dt class="col-sm-3">{{ t("Created at") }}</dt>
        <dd class="col-sm-9">
          {{ formatDate(apiKey.created_at, boot.locale) }}
        </dd>
      </dl>

      <AuditLine :audit="apiKey.audit" />
    </template>
  </div>
</template>
