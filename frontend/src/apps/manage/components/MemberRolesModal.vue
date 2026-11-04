<script setup lang="ts">
import { BModal } from "bootstrap-vue-next";
import { ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";
import { errorMessage } from "@/shared/apiError";
import { useNotify } from "@/shared/notify";
import RoleCheckboxes from "./RoleCheckboxes.vue";

// The roles edit of a member or of a member invitation (the old update pages) in a modal.
const props = defineProps<{
  organizationId: number;
  kind: "member" | "invitation";
  itemId: number | null;
  email: string;
  roles: string[];
  choices: { name: string; title: string }[];
}>();
const show = defineModel<boolean>({ default: false });
const emit = defineEmits<{ saved: [] }>();

const { t } = useI18n();
const notify = useNotify();

const selected = ref<string[]>([]);
const busy = ref(false);
const error = ref<string | null>(null);

// Every opening starts with the current roles.
watch(show, (open) => {
  if (open) {
    selected.value = [...props.roles];
    error.value = null;
  }
});

async function save() {
  if (busy.value || props.itemId === null) return;
  busy.value = true;
  error.value = null;

  const path = { id: props.organizationId };
  const body = { roles: selected.value };
  const { data, error: err } =
    props.kind === "member"
      ? await api.PUT("/bff/manage/organizations/{id}/members/{member_id}", {
          params: { path: { ...path, member_id: props.itemId } },
          body,
        })
      : await api.PUT("/bff/manage/organizations/{id}/member-invitations/{invitation_id}", {
          params: { path: { ...path, invitation_id: props.itemId } },
          body,
        });
  busy.value = false;

  if (!data) {
    error.value = errorMessage(err, t("Error"));
    return;
  }

  notify.success(data.message);
  show.value = false;
  emit("saved");
}
</script>

<template>
  <BModal
    v-model="show"
    :title="
      t('Update %(model_display_name)s', {
        model_display_name:
          kind === 'member' ? t('Organization member') : t('Organization member invitation'),
      })
    "
    :ok-title="t('Update')"
    :cancel-title="t('Cancel')"
    :ok-disabled="busy"
    @ok.prevent="save"
  >
    <div v-if="error" class="alert alert-danger" role="alert" data-test="roles-modal-error">
      {{ error }}
    </div>
    <div class="row mb-3">
      <div class="col-sm-3 fw-bold">{{ t("Email") }}</div>
      <div class="col-sm-9" data-test="roles-modal-email">{{ email }}</div>
    </div>
    <RoleCheckboxes v-model="selected" :choices="choices" id-prefix="modal-role" />
  </BModal>
</template>
