<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import { account } from "@/shared/legacy";
import { errorMessage } from "@/shared/apiError";

type UserProfile = components["schemas"]["UserProfile"];

const { t } = useI18n();

const profile = ref<UserProfile | null>(null);
const error = ref<string | null>(null);

onMounted(async () => {
  const { data, error: err } = await api.GET("/bff/user/profile");
  if (data) profile.value = data;
  else error.value = errorMessage(err, t("Error"));
});
</script>

<template>
  <div>
    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <template v-if="profile">
      <h1>{{ profile.email }}</h1>

      <div v-if="profile.deletion_requested_at" class="alert alert-danger" role="alert">
        {{ t("Your account is scheduled for deletion.") }}
        <router-link class="alert-link" :to="{ name: 'cancel-deletion' }">
          {{ t("Cancel deletion") }}
        </router-link>
      </div>

      <h2>{{ t("Profile") }}</h2>
      <div class="list-group mb-4">
        <a
          :href="account.changePassword"
          class="list-group-item list-group-item-action text-primary"
        >
          {{ t("Change password") }} <i class="fa fa-caret-right"></i>
        </a>
        <router-link
          v-if="!profile.deletion_requested_at"
          :to="{ name: 'request-deletion' }"
          class="list-group-item list-group-item-action text-danger"
        >
          {{ t("Delete account") }} <i class="fa fa-caret-right"></i>
        </router-link>
      </div>

      <h2>{{ t("Settings") }}</h2>
      <div class="list-group mb-4">
        <router-link
          :to="{ name: 'general' }"
          class="list-group-item list-group-item-action text-primary"
        >
          {{ t("General") }} <i class="fa fa-caret-right"></i>
        </router-link>
        <router-link
          :to="{ name: 'notifications' }"
          class="list-group-item list-group-item-action text-primary"
        >
          {{ t("Notifications") }} <i class="fa fa-caret-right"></i>
        </router-link>
        <router-link
          :to="{ name: 'oauth2-tokens' }"
          class="list-group-item list-group-item-action text-primary"
        >
          {{ t("Applications") }} <i class="fa fa-caret-right"></i>
        </router-link>
      </div>

      <h2>{{ t("Organizations") }}</h2>
      <div class="list-group mb-4">
        <router-link
          :to="{ name: 'memberships' }"
          class="list-group-item list-group-item-action text-primary"
        >
          {{ t("Organizations") }} <i class="fa fa-caret-right"></i>
        </router-link>
        <router-link
          :to="{ name: 'member-invitations' }"
          class="list-group-item list-group-item-action text-primary"
        >
          {{ t("Organization member invitations") }}
          <i class="fa fa-caret-right"></i>
        </router-link>
        <router-link
          :to="{ name: 'organization-invitations' }"
          class="list-group-item list-group-item-action text-primary"
        >
          {{ t("Organization invitations") }} <i class="fa fa-caret-right"></i>
        </router-link>
      </div>

      <h2>{{ t("Developer") }}</h2>
      <div class="list-group mb-4">
        <router-link
          :to="{ name: 'oauth2-clients' }"
          class="list-group-item list-group-item-action text-primary"
        >
          {{ t("OAuth2 clients") }} <i class="fa fa-caret-right"></i>
        </router-link>
        <router-link
          :to="{ name: 'api-keys' }"
          class="list-group-item list-group-item-action text-primary"
        >
          {{ t("API keys") }} <i class="fa fa-caret-right"></i>
        </router-link>
      </div>
    </template>
  </div>
</template>
