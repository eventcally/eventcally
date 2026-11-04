<script setup lang="ts">
import { BOverlay } from "bootstrap-vue-next";
import { onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import { errorMessage } from "@/shared/apiError";
import { manage } from "@/shared/legacy";
import { useFlashNotice } from "@/shared/useFlashNotice";

type Overview = components["schemas"]["OrganizationsOverview"];

const { t } = useI18n();

useFlashNotice();

const overview = ref<Overview | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

onMounted(async () => {
  const { data, error: err } = await api.GET("/bff/manage/organizations");
  loading.value = false;

  if (data) overview.value = data;
  else error.value = errorMessage(err, t("Error"));
});
</script>

<template>
  <div>
    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <BOverlay :show="loading">
      <template v-if="overview">
        <template v-if="overview.invitations.length">
          <h1>{{ t("Invitations") }}</h1>
          <div class="list-group mb-4" data-test="invitations">
            <a
              v-for="invitation in overview.invitations"
              :key="invitation.id"
              :href="invitation.url"
              class="list-group-item"
            >
              {{ invitation.name }}
            </a>
          </div>
        </template>

        <template v-if="overview.organization_invitations.length">
          <h1>{{ t("Organization invitations") }}</h1>
          <div class="list-group mb-4" data-test="organization-invitations">
            <a
              v-for="invitation in overview.organization_invitations"
              :key="invitation.id"
              :href="invitation.url"
              class="list-group-item"
            >
              {{ invitation.name }}
            </a>
          </div>
        </template>

        <h1>
          {{ t("Organizations") }}
          <a
            v-if="overview.docs_url"
            class="btn btn-outline-info btn-sm m-1 my-auto float-end"
            :href="overview.docs_url"
            target="_blank"
            rel="noopener noreferrer"
            role="button"
          >
            <i class="fa fa-fw fa-info-circle"></i> {{ t("Docs") }}
          </a>
        </h1>

        <div class="my-4">
          <router-link
            v-if="overview.can_create"
            class="btn btn-outline-secondary m-1"
            :to="{ name: 'organization-create' }"
            role="button"
          >
            <i class="fa fa-fw fa-plus"></i> {{ t("Create organization") }}
          </router-link>
          <router-link
            v-if="overview.invite_organization_id !== null && overview.invite_organization_id !== undefined"
            class="btn btn-outline-secondary m-1"
            :to="{
              name: 'organization-invitation-create',
              params: { organizationId: overview.invite_organization_id },
            }"
            role="button"
          >
            <i class="fa fa-fw fa-plus"></i> {{ t("Invite organization") }}
          </router-link>
        </div>

        <div class="list-group" data-test="organizations">
          <a
            v-for="organization in overview.organizations"
            :key="organization.id"
            :href="manage.organization(organization.id)"
            class="list-group-item"
          >
            {{ organization.name }}
          </a>
        </div>
      </template>
    </BOverlay>
  </div>
</template>
