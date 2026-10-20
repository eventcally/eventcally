<script setup lang="ts">
import { BFormGroup, BFormInput, BModal } from "bootstrap-vue-next";
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";
import { useNotify } from "@/shared/notify";

const props = defineProps<{ user: { id: number; email: string } | null }>();
const show = defineModel<boolean>({ default: false });
const emit = defineEmits<{ deleted: [] }>();

const { t } = useI18n();
const notify = useNotify();

const input = ref("");
const error = ref<string | null>(null);
const busy = ref(false);

// The server stays authoritative; this only mirrors its rule to enable the button.
const matches = computed(
  () =>
    props.user !== null &&
    input.value.trim().toLocaleLowerCase() === props.user.email.toLocaleLowerCase(),
);

watch(show, (open) => {
  if (open) {
    input.value = "";
    error.value = null;
  }
});

async function onOk(event: { preventDefault: () => void }) {
  event.preventDefault();
  if (!props.user || !matches.value || busy.value) return;

  busy.value = true;
  error.value = null;
  const { error: err } = await api.DELETE("/bff/admin/users/{id}", {
    params: { path: { id: props.user.id } },
    body: { email: input.value.trim() },
  });
  busy.value = false;

  if (err) {
    const fieldError = "errors" in err ? err.errors[0]?.msg : undefined;
    error.value = fieldError ?? err.message ?? t("Error");
    return;
  }

  notify.success(t("User successfully deleted"));
  show.value = false;
  emit("deleted");
}
</script>

<template>
  <BModal
    v-model="show"
    :title="t('Delete user')"
    :ok-title="t('Delete user')"
    :cancel-title="t('Cancel')"
    ok-variant="danger"
    :ok-disabled="!matches || busy"
    @ok="onOk"
  >
    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>
    <p>
      <strong>{{ user?.email }}</strong>
    </p>
    <BFormGroup :label="t('Email')" label-for="delete-user-email">
      <BFormInput id="delete-user-email" v-model="input" autocomplete="off" />
    </BFormGroup>
  </BModal>
</template>
