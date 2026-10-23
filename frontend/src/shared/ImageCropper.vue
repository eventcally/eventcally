<script setup lang="ts">
import { BButton, BButtonGroup, BModal } from "bootstrap-vue-next";
import Cropper from "cropperjs";
import "cropperjs/dist/cropper.css";
import { nextTick, onBeforeUnmount, ref } from "vue";
import { useI18n } from "vue-i18n";

const props = withDefaults(
  defineProps<{ src: string; minWidth?: number; minHeight?: number; mimeType?: string }>(),
  { minWidth: 320, minHeight: 320, mimeType: "image/png" },
);
const visible = defineModel<boolean>("show", { default: false });
const emit = defineEmits<{ cropped: [dataUri: string]; error: [message: string] }>();

const { t } = useI18n();
const image = ref<HTMLImageElement | null>(null);
let cropper: Cropper | null = null;

function destroy() {
  cropper?.destroy();
  cropper = null;
}

async function onShown() {
  await nextTick();
  if (!image.value) return;

  cropper = new Cropper(image.value, {
    viewMode: 1,
    autoCropArea: 1,
    ready() {
      // The source itself is too small to ever yield the minimum resolution.
      const { naturalWidth, naturalHeight } = cropper!.getImageData();
      if (naturalWidth < props.minWidth || naturalHeight < props.minHeight) {
        emit(
          "error",
          t("The resolution is too low. At least %(width)sx%(height)spx.", {
            width: props.minWidth,
            height: props.minHeight,
          }),
        );
        visible.value = false;
      }
    },
    crop(event) {
      const { width, height } = event.detail;
      if (width < props.minWidth || height < props.minHeight) {
        cropper?.setData({
          width: Math.max(props.minWidth, width),
          height: Math.max(props.minHeight, height),
        });
      }
    },
  });
}

function onOk() {
  if (!cropper) return;
  emit("cropped", cropper.getCroppedCanvas().toDataURL(props.mimeType));
}

const zoom = (ratio: number) => cropper?.zoom(ratio);
const rotate = (degrees: number) => cropper?.rotate(degrees);

onBeforeUnmount(destroy);
</script>

<template>
  <BModal
    v-model="visible"
    :title="t('Edit image')"
    :ok-title="t('Okay')"
    :cancel-title="t('Close')"
    @shown="onShown"
    @hidden="destroy"
    @ok="onOk"
  >
    <div style="height: 40vh">
      <img ref="image" :src="src" alt="" class="w-100" />
    </div>
    <div class="my-3">
      <BButtonGroup class="me-2">
        <BButton variant="outline-secondary" data-test="zoom-in" @click="zoom(0.1)">
          <i class="fa fa-search-plus"></i>
        </BButton>
        <BButton variant="outline-secondary" data-test="zoom-out" @click="zoom(-0.1)">
          <i class="fa fa-search-minus"></i>
        </BButton>
      </BButtonGroup>
      <BButtonGroup>
        <BButton variant="outline-secondary" data-test="rotate-left" @click="rotate(-90)">
          <i class="fa fa-undo-alt"></i>
        </BButton>
        <BButton variant="outline-secondary" data-test="rotate-right" @click="rotate(90)">
          <i class="fa fa-redo-alt"></i>
        </BButton>
      </BButtonGroup>
    </div>
  </BModal>
</template>
