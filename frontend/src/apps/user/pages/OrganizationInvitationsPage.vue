<script setup lang="ts">
import { BOverlay, BTable, type TableFieldRaw } from "bootstrap-vue-next";
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppPager from "@/shared/AppPager.vue";
import { boot } from "@/shared/boot";
import { formatDate } from "@/shared/format";
import ProfileBreadcrumb from "../components/ProfileBreadcrumb.vue";
import { useFlashNotice } from "@/shared/useFlashNotice";
import { usePagedList } from "@/shared/usePagedList";

type UserOrganizationInvitationPage = components["schemas"]["UserOrganizationInvitationPage"];

const { t } = useI18n();

useFlashNotice();

const { page, loading, error, currentPage } = usePagedList<UserOrganizationInvitationPage>(
  (current) =>
    api.GET("/bff/user/organization-invitations", {
      params: { query: { page: current } },
    }),
  "organization-invitations",
  t("Error"),
);

const fields = computed<TableFieldRaw[]>(() => [
  { key: "organization_name", label: t("Organization") },
  { key: "name", label: t("Name") },
  { key: "created_at", label: t("Created at") },
  { key: "actions", label: "" },
]);
</script>

<template>
  <div>
    <ProfileBreadcrumb :items="[{ label: t('Organization invitations') }]" />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <BOverlay :show="loading">
      <BTable :items="page?.items ?? []" :fields="fields" responsive striped bordered>
        <template #cell(created_at)="{ item }">{{
          formatDate(item.created_at, boot.locale)
        }}</template>
        <template #cell(actions)="{ item }">
          <router-link
            :to="{
              name: 'organization-invitation',
              params: { invitationId: item.id },
            }"
          >
            {{ t("View") }}
          </router-link>
        </template>
      </BTable>
    </BOverlay>

    <AppPager
      v-if="page && page.total > 0"
      v-model:page="currentPage"
      :pages="page.pages"
      :total="page.total"
    />
  </div>
</template>
