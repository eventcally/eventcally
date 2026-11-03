<script setup lang="ts">
import { BButton } from "bootstrap-vue-next";
import { onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import { manage } from "@/shared/legacy";
import { errorMessage } from "../apiError";
import ProfileBreadcrumb from "../components/ProfileBreadcrumb.vue";

type UserOrganizationInvitationItem = components["schemas"]["UserOrganizationInvitationItem"];

const props = defineProps<{ id: number }>();

const { t } = useI18n();

const invitation = ref<UserOrganizationInvitationItem | null>(null);
const busy = ref(false);
const error = ref<string | null>(null);

onMounted(async () => {
  const { data, error: err } = await api.GET("/bff/user/organization-invitations/{id}", {
    params: { path: { id: props.id } },
  });
  if (data) invitation.value = data;
  else error.value = errorMessage(err, t("Error"));
});

async function decline() {
  if (busy.value) return;
  busy.value = true;
  error.value = null;

  const { data, error: err } = await api.POST("/bff/user/organization-invitations/{id}/decline", {
    params: { path: { id: props.id } },
  });

  if (data) {
    window.location.assign(data.redirect_url);
    return;
  }

  busy.value = false;
  error.value = errorMessage(err, t("Error"));
}
</script>

<template>
  <div>
    <ProfileBreadcrumb
      :items="[
        {
          label: t('Organization invitations'),
          to: { name: 'organization-invitations' },
        },
      ]"
    />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <div v-if="invitation" data-test="negotiate">
      <p>
        {{
          t("%(name)s invited you to create an organization.", {
            name: invitation.organization_name,
          })
        }}
      </p>
      <!-- A page of the manage entry: a full page load. -->
      <a id="accept" :href="manage.organizationCreate(invitation.id)" class="btn btn-success">
        {{ t("Create organization") }}
      </a>
      <BButton id="decline" class="float-end" variant="danger" :disabled="busy" @click="decline">
        {{ t("Decline") }}
      </BButton>
    </div>
  </div>
</template>
