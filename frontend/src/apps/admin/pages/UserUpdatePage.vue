<script setup lang="ts">
import { BFormCheckboxGroup, BFormGroup, BOverlay } from "bootstrap-vue-next";
import { ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";
import { useNotify } from "@/shared/notify";
import UserDeleteModal from "../components/UserDeleteModal.vue";

type UserDetail = components["schemas"]["AdminUserDetail"];

const props = defineProps<{ id: number }>();

const { t } = useI18n();
const router = useRouter();
const notify = useNotify();

const detail = ref<UserDetail | null>(null);
const roles = ref<string[]>([]);
const loading = ref(false);
const saving = ref(false);
const error = ref<string | null>(null);
const showDelete = ref(false);

async function load() {
  loading.value = true;
  error.value = null;
  detail.value = null;
  const { data, error: err } = await api.GET("/bff/admin/users/{id}", {
    params: { path: { id: props.id } },
  });
  if (data) {
    detail.value = data;
    roles.value = [...data.user.roles];
  } else {
    error.value = err?.message ?? t("Error");
  }
  loading.value = false;
}

async function save() {
  saving.value = true;
  error.value = null;
  const { error: err } = await api.PUT("/bff/admin/users/{id}/roles", {
    params: { path: { id: props.id } },
    body: { roles: roles.value },
  });
  saving.value = false;

  if (err) {
    error.value =
      ("errors" in err ? err.errors.map((e) => e.msg).join(" ") : "") || err.message || t("Error");
    return;
  }

  notify.success(t("User successfully updated"));
  router.push({ name: "users" });
}

watch(() => props.id, load, { immediate: true });
</script>

<template>
  <div>
    <AppBreadcrumb
      :items="[
        { label: t('Admin'), to: { name: 'home' } },
        { label: t('Users'), to: { name: 'users' } },
        { label: detail?.user.email ?? '…' },
      ]"
    />

    <h1>{{ t("Update user") }}</h1>

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <BOverlay :show="loading">
      <form v-if="detail" @submit.prevent="save">
        <div class="card mb-3">
          <div class="card-header">{{ detail.user.email }}</div>
          <div class="card-body">
            <BFormGroup :label="t('Roles')">
              <BFormCheckboxGroup
                v-model="roles"
                stacked
                :options="detail.available_roles.map((r) => ({ value: r.name, text: r.title }))"
              />
            </BFormGroup>
          </div>
        </div>

        <button type="submit" class="btn btn-primary me-2" :disabled="saving">
          {{ t("Update user") }}
        </button>
        <button type="button" class="btn btn-outline-danger me-2" @click="showDelete = true">
          {{ t("Delete user") }}
        </button>
        <router-link :to="{ name: 'users' }" class="btn btn-link">{{ t("Cancel") }}</router-link>
      </form>
    </BOverlay>

    <UserDeleteModal
      v-model="showDelete"
      :user="detail?.user ?? null"
      @deleted="router.push({ name: 'users' })"
    />
  </div>
</template>
