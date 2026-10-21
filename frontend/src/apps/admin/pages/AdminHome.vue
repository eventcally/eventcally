<script setup lang="ts">
import { useI18n } from "vue-i18n";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";
import { legacy } from "@/shared/legacy";

const { t } = useI18n();

type Entry = { label: string; href?: string; to?: { name: string } };

const entries: Entry[] = [
  { label: t("Settings"), to: { name: "settings" } },
  { label: t("Organizations"), to: { name: "organizations" } },
  { label: t("Users"), to: { name: "users" } },
  { label: t("Email"), to: { name: "email" } },
  { label: t("Newsletter"), to: { name: "newsletter" } },
  { label: t("Planning"), to: { name: "planning" } },
  { label: "Flask-Admin", href: legacy.flaskAdmin },
];
</script>

<template>
  <div>
    <AppBreadcrumb :items="[{ label: t('Admin') }]" />
    <div class="list-group">
      <template v-for="entry in entries" :key="entry.label">
        <router-link v-if="entry.to" :to="entry.to" class="admin-entry list-group-item">
          {{ entry.label }} <i class="fa fa-caret-right"></i>
        </router-link>
        <a v-else :href="entry.href" class="admin-entry list-group-item">
          {{ entry.label }} <i class="fa fa-caret-right"></i>
        </a>
      </template>
    </div>
  </div>
</template>

<style scoped>
/* Same look as the list group of the Bootstrap 4 admin page: blue links, roomier rows. */
.admin-entry {
  padding: 0.75rem 1.25rem;
  color: var(--bs-link-color);
  text-decoration: none;
}
.admin-entry:hover {
  background-color: var(--bs-tertiary-bg);
}
</style>
