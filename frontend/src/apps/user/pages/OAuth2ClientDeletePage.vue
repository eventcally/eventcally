<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import { api } from "@/shared/api";
import { setFlash } from "@/shared/flash";
import NameConfirmationForm from "@/shared/NameConfirmationForm.vue";
import { errorMessage, mapFieldErrors } from "../apiError";
import ProfileBreadcrumb from "../components/ProfileBreadcrumb.vue";

const props = defineProps<{ id: number }>();

const { t } = useI18n();
const router = useRouter();

const clientName = ref<string | null>(null);
const busy = ref(false);
const error = ref<string | null>(null);
const nameError = ref<string | undefined>();

onMounted(async () => {
  const { data, error: err } = await api.GET("/bff/user/oauth2-clients/{id}", {
    params: { path: { id: props.id } },
  });
  if (data) clientName.value = data.client_name ?? "";
  else error.value = errorMessage(err, t("Error"));
});

async function submit(value: string) {
  if (busy.value) return;
  busy.value = true;
  error.value = null;
  nameError.value = undefined;

  const { error: err, response } = await api.POST("/bff/user/oauth2-clients/{id}/delete", {
    params: { path: { id: props.id } },
    body: { name: value },
  });

  if (response.ok) {
    setFlash(
      t("%(model_display_name)s successfully deleted", {
        model_display_name: t("OAuth2 client"),
      }),
    );
    await router.push({ name: "oauth2-clients" });
    return;
  }

  busy.value = false;
  const mapped = mapFieldErrors(err, ["name"]);
  if (mapped) {
    nameError.value = mapped.byKey.name;
    if (mapped.unmatched.length) error.value = mapped.unmatched.join(" ");
  } else {
    error.value = errorMessage(err, t("Error"));
  }
}
</script>

<template>
  <div>
    <ProfileBreadcrumb
      :items="[
        { label: t('OAuth2 clients'), to: { name: 'oauth2-clients' } },
        {
          label: clientName ?? '',
          to: { name: 'oauth2-client', params: { clientId: id } },
        },
        { label: t('Delete OAuth2 client') },
      ]"
    />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <NameConfirmationForm
      v-if="clientName !== null"
      :label="t('Name')"
      :submit-label="t('Delete OAuth2 client')"
      :error="nameError"
      :busy="busy"
      @submit="submit"
    >
      <p>
        {{
          t("Do you want to delete '%(object_title)s'?", {
            object_title: clientName,
          })
        }}
      </p>
    </NameConfirmationForm>
  </div>
</template>
