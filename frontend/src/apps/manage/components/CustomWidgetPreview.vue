<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { previewResizerOptions, type Settings, type WidgetType } from "@/shared/customWidget";

const props = defineProps<{
  type: WidgetType;
  settings: Settings;
  size: string;
}>();

const SETTINGS_EVENT = "EVENTCALLY_WIDGET_SETTINGS_UPDATE_EVENT";

const iframe = ref<HTMLIFrameElement | null>(null);
// A new key remounts the iframe: iframeResizer cannot be re-initialised on the same element.
const counter = ref(0);

// iframeResizer throws when it is asked to send through a torn-down or not yet initialised iframe.
let active = false;

function send() {
  if (!active) return;
  // postMessage cannot clone a reactive proxy.
  const data = JSON.parse(JSON.stringify(props.settings));
  iframe.value?.iFrameResizer?.sendMessage({ type: SETTINGS_EVENT, data });
}

function teardown() {
  active = false;
  iframe.value?.iFrameResizer?.removeListeners();
}

async function init() {
  teardown();
  counter.value++;
  await nextTick();
  if (!iframe.value) return;
  window.iFrameResize?.(
    {
      ...previewResizerOptions(props.settings),
      scrolling: "omit",
      onInit: () => {
        active = true;
        send();
      },
    },
    iframe.value,
  );
}

onMounted(init);
onBeforeUnmount(teardown);

// The size options and the widget type need a fresh iframe; every other setting is sent live.
watch(() => `${props.type}|${JSON.stringify(previewResizerOptions(props.settings))}`, init);
watch(() => props.settings, send, { deep: true });
watch(
  () => props.size,
  async () => {
    await nextTick();
    iframe.value?.iFrameResizer?.resize();
  },
);
</script>

<template>
  <iframe
    :key="counter"
    ref="iframe"
    :src="`/custom_widget/${type}`"
    class="w-100 border-0"
    style="height: 300px"
    :title="type"
    data-test="widget-preview"
  ></iframe>
</template>
