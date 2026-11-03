<script setup lang="ts">
import { BOverlay, BTable, type TableFieldRaw } from "bootstrap-vue-next";
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppPager from "@/shared/AppPager.vue";
import { boot } from "@/shared/boot";
import { formatDateTime } from "@/shared/format";
import ProfileBreadcrumb from "../components/ProfileBreadcrumb.vue";
import { useFlashNotice } from "../useFlashNotice";
import { usePagedList } from "../usePagedList";

type UserOAuth2TokenPage = components["schemas"]["UserOAuth2TokenPage"];

const { t } = useI18n();

useFlashNotice();

const { page, loading, error, currentPage } = usePagedList<UserOAuth2TokenPage>(
  (current) =>
    api.GET("/bff/user/oauth2-tokens", {
      params: { query: { page: current } },
    }),
  "oauth2-tokens",
  t("Error"),
);

const fields = computed<TableFieldRaw[]>(() => [
  { key: "id", label: t("ID") },
  { key: "client_name", label: t("Application") },
  { key: "scope", label: t("Scopes") },
  { key: "issued_at", label: t("Issued") },
  { key: "expires_at", label: t("Expires") },
  { key: "status", label: t("Status") },
]);

const statusLabel = (status: string | null | undefined) =>
  status === "expired" ? t("Expired") : status === "revoked" ? t("Revoked") : "";
</script>

<template>
  <div>
    <ProfileBreadcrumb :items="[{ label: t('OAuth2 tokens') }]" />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <BOverlay :show="loading">
      <BTable :items="page?.items ?? []" :fields="fields" responsive striped bordered>
        <template #cell(id)="{ item }">
          <router-link
            v-if="item.status !== 'revoked'"
            :to="{ name: 'oauth2-token-revoke', params: { tokenId: item.id } }"
            :title="t('Revoke')"
          >
            {{ item.id }}
          </router-link>
          <template v-else>{{ item.id }}</template>
        </template>
        <template #cell(issued_at)="{ item }">
          {{ formatDateTime(item.issued_at, boot.locale) }}
        </template>
        <template #cell(expires_at)="{ item }">
          {{ formatDateTime(item.expires_at, boot.locale) }}
        </template>
        <template #cell(status)="{ item }">{{ statusLabel(item.status) }}</template>
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
