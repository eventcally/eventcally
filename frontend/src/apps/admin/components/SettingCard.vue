<script setup lang="ts">
import { BFormTextarea } from "bootstrap-vue-next";
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useNotify } from "@/shared/notify";

const props = withDefaults(
  defineProps<{
    label: string;
    value: string | null;
    /** Resolves to the stored value; rejects with an Error whose message is shown. */
    save: (value: string | null) => Promise<string | null>;
    inputId: string;
    href?: string;
    monospace?: boolean;
    rows?: number;
  }>(),
  { href: undefined, monospace: false, rows: 8 },
);
const emit = defineEmits<{ saved: [value: string | null] }>();

const BLOCK_TAG = /<\/?(?:p|div|h[1-6]|li|ul|ol|br|tr|table|blockquote|pre|hr)\b[^>]*>/gi;

const { t } = useI18n();
const notify = useNotify();

const editing = ref(false);
const draft = ref("");
const busy = ref(false);
const error = ref<string | null>(null);

const dirty = computed(() => draft.value !== (props.value ?? ""));

// The texts are admin-authored HTML; show them as plain text, never render them here.
const preview = computed(() => {
  if (!props.value) return "";
  // Block tags get a space, so "</p><p>" does not glue two words together.
  const spaced = props.value.replace(BLOCK_TAG, " $&");
  const text = new DOMParser().parseFromString(spaced, "text/html").body.textContent ?? "";
  if (props.monospace) return text.trim();
  const flat = text.replace(/\s+/g, " ").trim();
  return flat.length > 200 ? `${flat.slice(0, 200)}…` : flat;
});

function edit() {
  draft.value = props.value ?? "";
  error.value = null;
  editing.value = true;
}

function cancel() {
  draft.value = props.value ?? "";
  error.value = null;
  editing.value = false;
}

async function onSave() {
  busy.value = true;
  error.value = null;
  try {
    const stored = await props.save(draft.value.trim() ? draft.value : null);
    editing.value = false;
    emit("saved", stored);
    notify.success(t("Settings successfully updated"));
  } catch (e) {
    error.value = e instanceof Error && e.message ? e.message : t("Error");
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <div class="card">
    <div class="card-header d-flex align-items-center">
      <span class="me-auto">{{ label }}</span>
      <a v-if="href" :href="href" target="_blank" rel="noopener" class="btn btn-sm btn-link">
        {{ t("Show") }}
      </a>
      <button v-if="!editing" type="button" class="btn btn-sm btn-outline-primary" @click="edit">
        {{ t("Edit") }}
      </button>
    </div>
    <div class="card-body">
      <form v-if="editing" @submit.prevent="onSave">
        <slot name="help" />
        <BFormTextarea
          :id="inputId"
          v-model="draft"
          :rows="rows"
          :class="{ 'font-monospace': monospace }"
          :state="error ? false : null"
        />
        <div v-if="error" class="alert alert-danger mt-3" role="alert">
          {{ error }}
        </div>
        <div class="mt-3">
          <button type="submit" class="btn btn-primary me-2" :disabled="busy || !dirty">
            {{ t("Save") }}
          </button>
          <button type="button" class="btn btn-link" :disabled="busy" @click="cancel">
            {{ t("Cancel") }}
          </button>
        </div>
      </form>
      <template v-else>
        <pre v-if="preview && monospace" class="small mb-0">{{ preview }}</pre>
        <span v-else-if="preview" class="setting-preview">{{ preview }}</span>
        <em v-else class="text-muted">{{ t("Not specified") }}</em>
      </template>
    </div>
  </div>
</template>
