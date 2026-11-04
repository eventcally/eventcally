<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import { boot } from "@/shared/boot";
import { formatDateTimeShort } from "@/shared/format";

export interface Audit {
  created_at?: string | null;
  updated_at?: string | null;
  created_by_label?: string | null;
  updated_by_label?: string | null;
}

const props = defineProps<{ audit?: Audit | null }>();

const { t } = useI18n();

const fmt = (iso: string | null | undefined) => formatDateTimeShort(iso, boot.locale);

// Like the `render_audit` macro: the update line only when it differs from the creation.
const lines = computed(() => {
  const a = props.audit;
  if (!a) return [];
  const result: string[] = [];
  if (a.created_at) {
    result.push(
      a.created_by_label
        ? t("Created at %(created_at)s by %(created_by)s.", {
            created_at: fmt(a.created_at),
            created_by: a.created_by_label,
          })
        : t("Created at %(created_at)s.", { created_at: fmt(a.created_at) }),
    );
  }
  if (a.updated_at && fmt(a.updated_at) !== fmt(a.created_at)) {
    result.push(
      a.updated_by_label
        ? t("Last updated at %(updated_at)s by %(updated_by)s.", {
            updated_at: fmt(a.updated_at),
            updated_by: a.updated_by_label,
          })
        : t("Last updated at %(updated_at)s.", {
            updated_at: fmt(a.updated_at),
          }),
    );
  }
  return result;
});
</script>

<template>
  <div v-if="lines.length" class="my-4 small text-muted" data-test="audit">
    <div v-for="line in lines" :key="line">{{ line }}</div>
  </div>
</template>
