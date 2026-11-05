<script setup lang="ts">
import { BFormInput, BModal } from "bootstrap-vue-next";
import { ref } from "vue";
import { useI18n } from "vue-i18n";
import { useNotify } from "@/shared/notify";

export interface ShareLinks {
  url: string;
  facebook: string;
  twitter: string;
  email: string;
  whatsapp: string;
  telegram: string;
}

defineProps<{ links: ShareLinks }>();
const visible = defineModel<boolean>({ default: false });

const { t } = useI18n();
const notify = useNotify();
const input = ref<InstanceType<typeof BFormInput> | null>(null);

async function copy(url: string) {
  try {
    await navigator.clipboard.writeText(url);
    notify.success(t("Link copied"));
  } catch {
    // Clipboard API unavailable (e.g. no HTTPS): let the user copy from the selected input.
    input.value?.$el?.select?.();
  }
}
</script>

<template>
  <BModal v-model="visible" :title="t('Share')" no-footer centered>
    <div class="input-group mb-3">
      <BFormInput
        ref="input"
        :model-value="links.url"
        readonly
        name="shareUrl"
        @focus="($event.target as HTMLInputElement).select()"
      />
      <button type="button" class="btn btn-outline-secondary" data-test="copy-link" @click="copy(links.url)">
        {{ t("Copy link") }}
      </button>
    </div>
    <div class="list-group">
      <a class="list-group-item list-group-item-action" :href="links.facebook" target="_blank" rel="noopener noreferrer"
        ><i class="fab fa-fw me-2 fa-facebook"></i>Facebook</a
      >
      <a class="list-group-item list-group-item-action" :href="links.twitter" target="_blank" rel="noopener noreferrer"
        ><i class="fab fa-fw me-2 fa-twitter"></i>Twitter</a
      >
      <a class="list-group-item list-group-item-action" :href="links.email" target="_blank" rel="noopener noreferrer"
        ><i class="fa fa-fw me-2 fa-envelope"></i>{{ t("Email") }}</a
      >
      <a
        class="list-group-item list-group-item-action"
        :href="links.whatsapp"
        target="_blank"
        rel="noopener noreferrer"
        data-action="share/whatsapp/share"
        ><i class="fab fa-fw me-2 fa-whatsapp"></i>Whatsapp</a
      >
      <a class="list-group-item list-group-item-action" :href="links.telegram" target="_blank" rel="noopener noreferrer"
        ><i class="fab fa-fw me-2 fa-telegram"></i>Telegram</a
      >
    </div>
  </BModal>
</template>
