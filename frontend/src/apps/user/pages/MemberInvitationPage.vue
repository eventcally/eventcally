<script setup lang="ts">
import { BButton } from "bootstrap-vue-next";
import { onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import { errorMessage } from "../apiError";
import ProfileBreadcrumb from "../components/ProfileBreadcrumb.vue";

type UserMemberInvitationItem = components["schemas"]["UserMemberInvitationItem"];

const props = defineProps<{ id: number }>();

const { t } = useI18n();

const invitation = ref<UserMemberInvitationItem | null>(null);
const busy = ref(false);
const error = ref<string | null>(null);

onMounted(async () => {
  const { data, error: err } = await api.GET("/bff/user/member-invitations/{id}", {
    params: { path: { id: props.id } },
  });
  if (data) invitation.value = data;
  else error.value = errorMessage(err, t("Error"));
});

async function negotiate(action: "accept" | "decline") {
  if (busy.value) return;
  busy.value = true;
  error.value = null;

  const path = { params: { path: { id: props.id } } };
  const { data, error: err } =
    action === "accept"
      ? await api.POST("/bff/user/member-invitations/{id}/accept", path)
      : await api.POST("/bff/user/member-invitations/{id}/decline", path);

  if (data) {
    // The server flashed the message for the page it leads to.
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
          label: t('Organization member invitations'),
          to: { name: 'member-invitations' },
        },
      ]"
    />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <div v-if="invitation" data-test="negotiate">
      <p>
        {{
          t("Would you like to accept the invitation from %(name)s?", {
            name: invitation.organization_name,
          })
        }}
      </p>
      <BButton id="accept" variant="success" :disabled="busy" @click="negotiate('accept')">
        {{ t("Accept") }}
      </BButton>
      <BButton
        id="decline"
        class="float-end"
        variant="secondary"
        :disabled="busy"
        @click="negotiate('decline')"
      >
        {{ t("Decline") }}
      </BButton>
    </div>
  </div>
</template>
