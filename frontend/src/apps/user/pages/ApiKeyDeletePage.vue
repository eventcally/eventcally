<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import { api } from "@/shared/api";
import { setFlash } from "@/shared/flash";
import NameConfirmationForm from "@/shared/NameConfirmationForm.vue";
import { errorMessage, mapFieldErrors } from "@/shared/apiError";
import ProfileBreadcrumb from "../components/ProfileBreadcrumb.vue";

const props = defineProps<{ id: number }>();

const { t } = useI18n();
const router = useRouter();

const name = ref<string | null>(null);
const busy = ref(false);
const error = ref<string | null>(null);
const nameError = ref<string | undefined>();

const modelName = computed(() => t("API key"));
const title = computed(() =>
  t("Delete %(model_display_name)s", { model_display_name: modelName.value }),
);

onMounted(async () => {
  const { data, error: err } = await api.GET("/bff/user/api-keys/{id}", {
    params: { path: { id: props.id } },
  });
  if (data) name.value = data.name;
  else error.value = errorMessage(err, t("Error"));
});

async function submit(value: string) {
  if (busy.value) return;
  busy.value = true;
  error.value = null;
  nameError.value = undefined;

  const { error: err, response } = await api.POST("/bff/user/api-keys/{id}/delete", {
    params: { path: { id: props.id } },
    body: { name: value },
  });

  if (response.ok) {
    setFlash(
      t("%(model_display_name)s successfully deleted", {
        model_display_name: modelName.value,
      }),
    );
    await router.push({ name: "api-keys" });
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
        { label: t('API keys'), to: { name: 'api-keys' } },
        {
          label: `${modelName} ${id}`,
          to: { name: 'api-key', params: { apiKeyId: id } },
        },
        { label: title },
      ]"
    />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <NameConfirmationForm
      v-if="name !== null"
      :label="t('Name')"
      :submit-label="title"
      :error="nameError"
      :busy="busy"
      @submit="submit"
    >
      <p>
        {{
          t("Do you want to delete '%(object_title)s'?", {
            object_title: `${modelName} ${id}`,
          })
        }}
      </p>
    </NameConfirmationForm>
  </div>
</template>
