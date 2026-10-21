<script setup lang="ts">
import { BFormCheckbox, BOverlay } from "bootstrap-vue-next";
import { computed, reactive, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import { boot } from "@/shared/boot";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";
import { formatDateTime } from "@/shared/format";
import { manage, publicPages } from "@/shared/legacy";
import { useNotify } from "@/shared/notify";
import OrganizationDeleteModal from "../components/OrganizationDeleteModal.vue";

type Detail = components["schemas"]["AdminOrganizationDetail"];
type SettingKey =
  | "incoming_reference_requests_allowed"
  | "can_create_other"
  | "can_invite_other"
  | "can_verify_other";

const props = defineProps<{ id: number }>();

const { t } = useI18n();
const router = useRouter();
const notify = useNotify();

const detail = ref<Detail | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);
const showDelete = ref(false);
const saving = reactive(new Set<SettingKey>());

const switches = computed<{ key: SettingKey; label: string; description: string }[]>(() => [
  {
    key: "incoming_reference_requests_allowed",
    label: t("Incoming reference requests allowed"),
    description: t(
      "If set, other organizations can ask this organization to reference their event.",
    ),
  },
  {
    key: "can_create_other",
    label: t("Create other organizations"),
    description: t("If set, members of the organization can create other organizations."),
  },
  {
    key: "can_invite_other",
    label: t("Invite other organizations"),
    description: t("If set, members of the organization can invite other organizations."),
  },
  {
    key: "can_verify_other",
    label: t("Verify other organizations"),
    description: t("If set, members of the organization can verify other organizations."),
  },
]);

const fmt = (iso: string | null | undefined) => formatDateTime(iso, boot.locale);

const auditLines = computed(() => {
  const a = detail.value?.audit;
  if (!a) return [];
  const lines: string[] = [];
  if (a.created_at) {
    lines.push(
      a.created_by_label
        ? t("Created at %(created_at)s by %(created_by)s.", {
            created_at: fmt(a.created_at),
            created_by: a.created_by_label,
          })
        : t("Created at %(created_at)s.", { created_at: fmt(a.created_at) }),
    );
  }
  if (a.updated_at) {
    lines.push(
      a.updated_by_label
        ? t("Last updated at %(updated_at)s by %(updated_by)s.", {
            updated_at: fmt(a.updated_at),
            updated_by: a.updated_by_label,
          })
        : t("Last updated at %(updated_at)s.", { updated_at: fmt(a.updated_at) }),
    );
  }
  return lines;
});

async function load() {
  loading.value = true;
  error.value = null;
  detail.value = null;
  const { data, error: err } = await api.GET("/bff/admin/organizations/{id}", {
    params: { path: { id: props.id } },
  });
  if (data) {
    detail.value = data;
  } else {
    error.value = err?.message ?? t("Error");
  }
  loading.value = false;
}

// Every switch saves on its own; the server answer is authoritative.
async function toggle(key: SettingKey, value: boolean) {
  if (!detail.value) return;
  const previous = detail.value[key];
  detail.value[key] = value;
  saving.add(key);
  error.value = null;

  const { data, error: err } = await api.PUT("/bff/admin/organizations/{id}/settings/{key}", {
    params: { path: { id: props.id, key } },
    body: { value },
  });
  saving.delete(key);

  if (err || !data) {
    if (detail.value) detail.value[key] = previous;
    error.value =
      (err && "errors" in err ? err.errors.map((e) => e.msg).join(" ") : "") ||
      err?.message ||
      t("Error");
    return;
  }

  detail.value = data;
  notify.success(t("Organization successfully updated"));
}

watch(() => props.id, load, { immediate: true });
</script>

<template>
  <div>
    <AppBreadcrumb
      :items="[
        { label: t('Admin'), to: { name: 'home' } },
        { label: t('Organizations'), to: { name: 'organizations' } },
        { label: detail?.name ?? '…' },
      ]"
    />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <BOverlay :show="loading">
      <template v-if="detail">
        <h1>
          {{ detail.name }}
          <span v-if="detail.is_verified" class="badge text-bg-success fs-6">
            {{ t("Verified") }}
          </span>
        </h1>
        <p>
          <a :href="manage.organization(detail.id)" class="me-3">{{ t("Manage") }}</a>
          <a :href="publicPages.organization(detail.id)">{{ t("View") }}</a>
        </p>

        <div class="card mb-3">
          <div class="card-body">
            <BFormCheckbox
              v-for="s in switches"
              :id="`org-${s.key}`"
              :key="s.key"
              switch
              class="mb-3"
              :model-value="detail[s.key]"
              :disabled="saving.has(s.key)"
              @update:model-value="(v: unknown) => toggle(s.key, Boolean(v))"
            >
              {{ s.label }}
              <div class="form-text mt-0">{{ s.description }}</div>
            </BFormCheckbox>
          </div>
        </div>

        <p v-if="auditLines.length" class="small text-muted">{{ auditLines.join(" ") }}</p>

        <div class="card border-danger mb-3">
          <div class="card-body">
            <button type="button" class="btn btn-outline-danger" @click="showDelete = true">
              {{ t("Delete organization") }}
            </button>
          </div>
        </div>
      </template>
    </BOverlay>

    <OrganizationDeleteModal
      v-model="showDelete"
      :organization="detail ? { id: detail.id, name: detail.name } : null"
      @deleted="router.push({ name: 'organizations' })"
    />
  </div>
</template>
