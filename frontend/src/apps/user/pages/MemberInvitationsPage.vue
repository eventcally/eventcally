<script setup lang="ts">
import { BOverlay, BTable, type TableFieldRaw } from "bootstrap-vue-next";
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppPager from "@/shared/AppPager.vue";
import ProfileBreadcrumb from "../components/ProfileBreadcrumb.vue";
import { usePagedList } from "../usePagedList";

type UserMemberInvitationPage = components["schemas"]["UserMemberInvitationPage"];

const { t } = useI18n();

const { page, loading, error, currentPage } = usePagedList<UserMemberInvitationPage>(
  (current) =>
    api.GET("/bff/user/member-invitations", {
      params: { query: { page: current } },
    }),
  "member-invitations",
  t("Error"),
);

const fields = computed<TableFieldRaw[]>(() => [
  { key: "organization_name", label: t("Organization") },
  { key: "actions", label: "" },
]);
</script>

<template>
  <div>
    <ProfileBreadcrumb :items="[{ label: t('Organization member invitations') }]" />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <BOverlay :show="loading">
      <BTable :items="page?.items ?? []" :fields="fields" responsive striped bordered>
        <template #cell(actions)="{ item }">
          <router-link
            :to="{
              name: 'member-invitation',
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
