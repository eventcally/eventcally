<script setup lang="ts">
import { useI18n } from "vue-i18n";

defineProps<{
  url?: string | null;
  email?: string | null;
  phone?: string | null;
  fax?: string | null;
  address?: string | null;
}>();

const { t } = useI18n();

// A link without a scheme gets one, as the Jinja filter `ensure_link_scheme`.
const withScheme = (link: string) => (/^https?:\/\//.test(link) ? link : `https://${link}`);
</script>

<template>
  <div>
    <div v-if="url">
      <i class="fa fa-fw fa-link me-1" :title="t('Link')"></i>
      <a :href="withScheme(url)" target="_blank" rel="noopener noreferrer" style="word-break: break-all">{{
        url
      }}</a>
    </div>
    <div v-if="email">
      <i class="fa fa-fw fa-envelope me-1" :title="t('Email')"></i>
      <a :href="`mailto:${email}`">{{ email }}</a>
    </div>
    <div v-if="phone">
      <i class="fa fa-fw fa-phone me-1" :title="t('Phone')"></i>
      <a :href="`tel:${phone}`">{{ phone }}</a>
    </div>
    <div v-if="fax">
      <i class="fa fa-fw fa-fax me-1" :title="t('Fax')"></i>
      {{ fax }}
    </div>
    <div v-if="address">
      <i class="fa fa-fw fa-map-marker me-1" :title="t('Location')"></i>
      {{ address }}
    </div>
  </div>
</template>
