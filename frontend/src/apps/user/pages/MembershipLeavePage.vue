<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import NameConfirmationForm from "@/shared/NameConfirmationForm.vue";
import { errorMessage, mapFieldErrors } from "../apiError";
import ProfileBreadcrumb from "../components/ProfileBreadcrumb.vue";

type UserMembershipDetail = components["schemas"]["UserMembershipDetail"];

const props = defineProps<{ id: number }>();

const { t } = useI18n();

const membership = ref<UserMembershipDetail | null>(null);
const busy = ref(false);
const error = ref<string | null>(null);
const nameError = ref<string | undefined>();

onMounted(async () => {
  const { data, error: err } = await api.GET("/bff/user/memberships/{id}", {
    params: { path: { id: props.id } },
  });
  if (data) membership.value = data;
  else error.value = errorMessage(err, t("Error"));
});

async function submit(name: string) {
  if (busy.value) return;
  busy.value = true;
  error.value = null;
  nameError.value = undefined;

  const { data, error: err } = await api.POST("/bff/user/memberships/{id}/leave", {
    params: { path: { id: props.id } },
    body: { name },
  });

  if (data) {
    // The server flashed the message; the list renders it.
    window.location.assign(data.redirect_url);
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
        { label: t('Organizations'), to: { name: 'memberships' } },
        { label: t('Leave organization') },
      ]"
    />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <NameConfirmationForm
      v-if="membership"
      :label="t('Name')"
      :submit-label="t('Leave organization')"
      :error="nameError"
      :busy="busy || !membership.can_leave"
      @submit="submit"
    >
      <p>
        {{
          t("Do you want to leave organization %(name)s?", {
            name: membership.organization_name,
          })
        }}
      </p>
    </NameConfirmationForm>
  </div>
</template>
