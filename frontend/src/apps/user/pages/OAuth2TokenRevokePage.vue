<script setup lang="ts">
import { BButton } from "bootstrap-vue-next";
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import { setFlash } from "@/shared/flash";
import { errorMessage } from "@/shared/apiError";
import ProfileBreadcrumb from "../components/ProfileBreadcrumb.vue";

type UserOAuth2Token = components["schemas"]["UserOAuth2Token"];

const props = defineProps<{ id: number }>();

const { t } = useI18n();
const router = useRouter();

const token = ref<UserOAuth2Token | null>(null);
const busy = ref(false);
const error = ref<string | null>(null);

const modelName = computed(() => t("OAuth2 token"));
const title = computed(() =>
  t("Revoke %(model_display_name)s", { model_display_name: modelName.value }),
);
const objectTitle = computed(
  () => `${modelName.value} ${props.id} (${token.value?.client_name ?? ""})`,
);

onMounted(async () => {
  const { data, error: err } = await api.GET("/bff/user/oauth2-tokens/{id}", {
    params: { path: { id: props.id } },
  });
  if (data) token.value = data;
  else error.value = errorMessage(err, t("Error"));
});

async function revoke() {
  if (busy.value) return;
  busy.value = true;
  error.value = null;

  const { error: err, response } = await api.POST("/bff/user/oauth2-tokens/{id}/revoke", {
    params: { path: { id: props.id } },
  });

  if (response.ok) {
    setFlash(
      t("%(model_display_name)s successfully revoked", {
        model_display_name: modelName.value,
      }),
    );
    await router.push({ name: "oauth2-tokens" });
    return;
  }

  busy.value = false;
  error.value = errorMessage(err, t("Error"));
}
</script>

<template>
  <div>
    <ProfileBreadcrumb
      :items="[{ label: t('OAuth2 tokens'), to: { name: 'oauth2-tokens' } }, { label: title }]"
    />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <form v-if="token" data-test="revoke-form" @submit.prevent="revoke">
      <p>
        {{
          t("Do you want to revoke '%(object_title)s'?", {
            object_title: objectTitle,
          })
        }}
      </p>
      <BButton id="submit" type="submit" variant="primary" :disabled="busy">
        {{ t("Revoke OAuth2 token") }}
      </BButton>
    </form>
  </div>
</template>
