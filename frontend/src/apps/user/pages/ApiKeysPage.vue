<script setup lang="ts">
import { BOverlay, BTable, type TableFieldRaw } from "bootstrap-vue-next";
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import { boot } from "@/shared/boot";
import { formatDate } from "@/shared/format";
import AppPager from "@/shared/AppPager.vue";
import ProfileBreadcrumb from "../components/ProfileBreadcrumb.vue";
import { useFlashNotice } from "@/shared/useFlashNotice";
import { usePagedList } from "@/shared/usePagedList";

type UserApiKeyPage = components["schemas"]["UserApiKeyPage"];

const { t } = useI18n();

useFlashNotice();

const sort = ref<"name" | "-created_at">("name");

const { page, loading, error, currentPage } = usePagedList<UserApiKeyPage>(
  (current) =>
    api.GET("/bff/user/api-keys", {
      params: { query: { page: current, sort: sort.value } },
    }),
  "api-keys",
  t("Error"),
  [sort],
);

const fields = computed<TableFieldRaw[]>(() => [
  { key: "name", label: t("Name") },
  { key: "created_at", label: t("Created at") },
]);
</script>

<template>
  <div>
    <ProfileBreadcrumb :items="[{ label: t('API keys') }]" />

    <div class="my-4">
      <router-link :to="{ name: 'api-key-create' }" class="btn btn-outline-secondary">
        <i class="fa fa-plus"></i>
        {{
          t("Create %(model_display_name)s", {
            model_display_name: t("API key"),
          })
        }}
      </router-link>
    </div>

    <div class="mb-3 col-md-4 px-0">
      <label class="form-label" for="sort">{{ t("Sort") }}</label>
      <select id="sort" v-model="sort" class="form-select">
        <option value="name">{{ t("Name") }}</option>
        <option value="-created_at">{{ t("Last created first") }}</option>
      </select>
    </div>

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <BOverlay :show="loading">
      <BTable :items="page?.items ?? []" :fields="fields" responsive striped bordered>
        <template #cell(name)="{ item }">
          <router-link :to="{ name: 'api-key', params: { apiKeyId: item.id } }">
            {{ item.name }}
          </router-link>
        </template>
        <template #cell(created_at)="{ item }">{{
          formatDate(item.created_at, boot.locale)
        }}</template>
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
