<script setup lang="ts">
import { BFormGroup, BFormInput, BModal } from "bootstrap-vue-next";
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";

const props = defineProps<{
  title: string;
  okTitle: string;
  /** Shown in bold and compared (trimmed, case-insensitive) with the input. */
  subject: string | null;
  label: string;
  inputId: string;
  /** Runs the deletion with the trimmed input; throws an `Error` with the message to show. */
  confirm: (input: string) => Promise<void>;
}>();
const show = defineModel<boolean>({ default: false });
const emit = defineEmits<{ done: [] }>();

const { t } = useI18n();

const input = ref("");
const error = ref<string | null>(null);
const busy = ref(false);

// The server stays authoritative; this only mirrors its rule to enable the button.
const matches = computed(
  () =>
    props.subject !== null &&
    input.value.trim().toLocaleLowerCase() === props.subject.toLocaleLowerCase(),
);

watch(show, (open) => {
  if (open) {
    input.value = "";
    error.value = null;
  }
});

async function onOk(event: { preventDefault: () => void }) {
  event.preventDefault();
  if (!matches.value || busy.value) return;

  busy.value = true;
  error.value = null;
  try {
    await props.confirm(input.value.trim());
  } catch (e) {
    error.value = e instanceof Error ? e.message : t("Error");
    return;
  } finally {
    busy.value = false;
  }

  show.value = false;
  emit("done");
}
</script>

<template>
  <BModal
    v-model="show"
    :title="title"
    :ok-title="okTitle"
    :cancel-title="t('Cancel')"
    ok-variant="danger"
    :ok-disabled="!matches || busy"
    @ok="onOk"
  >
    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>
    <p>
      <strong>{{ subject }}</strong>
    </p>
    <BFormGroup :label="label" :label-for="inputId">
      <BFormInput :id="inputId" v-model="input" autocomplete="off" />
    </BFormGroup>
  </BModal>
</template>
