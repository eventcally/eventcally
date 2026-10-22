<script setup lang="ts">
import { useDebounceFn } from "@vueuse/core";
import { BFormInput, BOverlay } from "bootstrap-vue-next";
import { onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppPager from "@/shared/AppPager.vue";

type OrganizationPage = components["schemas"]["PublicOrganizationPage"];

const PER_PAGE = 10;

const { t } = useI18n();

const page = ref<OrganizationPage | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);

const keyword = ref("");
const currentKeyword = ref<string | undefined>(undefined);
const currentPage = ref(1);

// A new search always starts on page 1.
const search = useDebounceFn((value: string) => {
  currentKeyword.value = value.trim() || undefined;
  currentPage.value = 1;
}, 300);

async function load() {
  loading.value = true;
  error.value = null;
  const { data, error: err } = await api.GET("/bff/public/organizations", {
    params: {
      query: { page: currentPage.value, per_page: PER_PAGE, keyword: currentKeyword.value },
    },
  });
  if (data) page.value = data;
  else error.value = err?.message ?? t("Error");
  loading.value = false;
}

watch(keyword, (value) => search(value));
watch([currentKeyword, currentPage], load);
onMounted(load);
</script>

<template>
  <div>
    <h1>{{ t("Organizations") }}</h1>

    <BFormInput
      v-model="keyword"
      type="search"
      class="mb-3"
      :placeholder="t('Keyword')"
      :aria-label="t('Keyword')"
      autocomplete="off"
    />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <BOverlay :show="loading">
      <div class="list-group" style="min-height: 100px">
        <RouterLink
          v-for="item in page?.items ?? []"
          :key="item.id"
          :to="{ name: 'organization', params: { id: item.id } }"
          class="list-group-item list-group-item-action"
        >
          <div>
            {{ item.name }}
            <i v-if="item.is_verified" class="fa fa-check-circle text-primary"></i>
          </div>
          <div v-if="item.short_name" class="text-muted">@{{ item.short_name }}</div>
        </RouterLink>
        <div v-if="page && page.items.length === 0" class="list-group-item text-muted">
          {{ t("No organizations found") }}
        </div>
      </div>
    </BOverlay>

    <AppPager
      v-if="page && page.pages > 1"
      class="mt-3"
      :page="currentPage"
      :pages="page.pages"
      :total="page.total"
      @update:page="currentPage = $event"
    />
  </div>
</template>
