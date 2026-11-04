<script setup lang="ts">
import { BOverlay, BTable, type TableFieldRaw } from "bootstrap-vue-next";
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppPager from "@/shared/AppPager.vue";
import ProfileBreadcrumb from "../components/ProfileBreadcrumb.vue";
import { useFlashNotice } from "@/shared/useFlashNotice";
import { usePagedList } from "@/shared/usePagedList";

type UserOAuth2ClientPage = components["schemas"]["UserOAuth2ClientPage"];

const { t } = useI18n();

useFlashNotice();

const { page, loading, error, currentPage } = usePagedList<UserOAuth2ClientPage>(
  (current) =>
    api.GET("/bff/user/oauth2-clients", {
      params: { query: { page: current } },
    }),
  "oauth2-clients",
  t("Error"),
);

const fields = computed<TableFieldRaw[]>(() => [{ key: "client_name", label: t("Client Name") }]);
</script>

<template>
  <div>
    <ProfileBreadcrumb :items="[{ label: t('OAuth2 clients') }]" />

    <div class="my-4">
      <router-link :to="{ name: 'oauth2-client-create' }" class="btn btn-outline-secondary">
        <i class="fa fa-plus"></i>
        {{
          t("Create %(model_display_name)s", {
            model_display_name: t("OAuth2 client"),
          })
        }}
      </router-link>
    </div>

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <BOverlay :show="loading">
      <BTable :items="page?.items ?? []" :fields="fields" responsive striped bordered>
        <template #cell(client_name)="{ item }">
          <router-link :to="{ name: 'oauth2-client', params: { clientId: item.id } }">
            {{ item.client_name }}
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
