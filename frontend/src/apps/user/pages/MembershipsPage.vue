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

type UserMembershipPage = components["schemas"]["UserMembershipPage"];

const { t } = useI18n();

useFlashNotice();

const { page, loading, error, currentPage } = usePagedList<UserMembershipPage>(
  (current) => api.GET("/bff/user/memberships", { params: { query: { page: current } } }),
  "memberships",
  t("Error"),
);

const fields = computed<TableFieldRaw[]>(() => [
  { key: "organization_name", label: t("Organization") },
  { key: "actions", label: "" },
]);
</script>

<template>
  <div>
    <ProfileBreadcrumb :items="[{ label: t('Organizations') }]" />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <BOverlay :show="loading">
      <BTable :items="page?.items ?? []" :fields="fields" responsive striped bordered>
        <template #cell(actions)="{ item }">
          <router-link :to="{ name: 'membership-leave', params: { memberId: item.id } }">
            {{ t("Leave organization") }}
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
