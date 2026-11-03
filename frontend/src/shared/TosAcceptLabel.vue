<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import { publicPages } from "./legacy";

// "I read and accept the Terms of Service and Privacy." with the two links. The msgids
// carry the link markers as placeholders; the text is split on sentinels and rendered as
// text nodes and anchors, never as HTML.
const props = defineProps<{ hasTos: boolean }>();

const { t } = useI18n();

const OPEN_TOS = "\u0001";
const CLOSE_TOS = "\u0002";
const OPEN_PRIVACY = "\u0003";
const CLOSE_PRIVACY = "\u0004";
const SENTINELS = new RegExp(`([${OPEN_TOS}-${CLOSE_PRIVACY}])`);

interface Part {
  text: string;
  href?: string;
}

const parts = computed<Part[]>(() => {
  const markers = {
    tos_open: OPEN_TOS,
    tos_close: CLOSE_TOS,
    privacy_open: OPEN_PRIVACY,
    privacy_close: CLOSE_PRIVACY,
  };
  const text = props.hasTos
    ? t(
        "I read and accept %(tos_open)sTerms of Service%(tos_close)s and %(privacy_open)sPrivacy%(privacy_close)s.",
        markers,
      )
    : t("I read and accept %(privacy_open)sPrivacy%(privacy_close)s.", markers);

  const result: Part[] = [];
  let href: string | undefined;
  for (const piece of text.split(SENTINELS)) {
    if (piece === OPEN_TOS) href = publicPages.tos;
    else if (piece === OPEN_PRIVACY) href = publicPages.privacy;
    else if (piece === CLOSE_TOS || piece === CLOSE_PRIVACY) href = undefined;
    else if (piece) result.push({ text: piece, href });
  }
  return result;
});
</script>

<template>
  <span>
    <template v-for="(part, index) in parts" :key="index">
      <a v-if="part.href" :href="part.href" target="_blank" rel="noopener">{{ part.text }}</a>
      <template v-else>{{ part.text }}</template>
    </template>
  </span>
</template>
