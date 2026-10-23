<script setup lang="ts">
import { BButton, BFormGroup, BFormInput, BFormSelect } from "bootstrap-vue-next";
import { computed, defineAsyncComponent, ref } from "vue";
import { useI18n } from "vue-i18n";

const ImageCropper = defineAsyncComponent(() => import("./ImageCropper.vue"));

export interface ImageValue {
  image_base64: string | null;
  copyright_text: string | null;
  license_id: number | null;
}

const props = defineProps<{
  licenses: { id: number; name: string }[];
  /** Messages by sub-field: `image_base64`, `copyright_text`, `license_id`. */
  errors?: Record<string, string | undefined>;
  minSize?: number;
}>();
// `null`: no image. `image_base64` is `null` while the stored image is unchanged.
const model = defineModel<ImageValue | null>({ default: null });
// What the preview shows (the stored image or the cropped one).
const preview = defineModel<string | null>("preview", { default: null });

const { t } = useI18n();
const fileInput = ref<HTMLInputElement | null>(null);
const cropSource = ref("");
const cropMime = ref("image/png");
const showCropper = ref(false);
const dragover = ref(false);
const message = ref<string | null>(null);

const minSize = computed(() => props.minSize ?? 320);
const licenseOptions = computed(() => [
  { value: null, text: t("Please select") },
  ...props.licenses.map((license) => ({ value: license.id, text: license.name })),
]);

function openCropper(src: string, mime: string) {
  message.value = null;
  cropSource.value = src;
  cropMime.value = mime;
  showCropper.value = true;
}

function takeFile(file: File | undefined) {
  dragover.value = false;
  if (!file) return;
  if (!/^image\/\w+/.test(file.type)) {
    message.value = t("Please choose an image file.");
    return;
  }
  const reader = new FileReader();
  reader.onload = () => openCropper(String(reader.result), file.type);
  reader.readAsDataURL(file);
}

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  takeFile(input.files?.[0]);
  input.value = "";
}

function onCropped(dataUri: string) {
  preview.value = dataUri;
  model.value = {
    image_base64: dataUri,
    copyright_text: model.value?.copyright_text ?? null,
    license_id: model.value?.license_id ?? null,
  };
}

function setField(field: "copyright_text" | "license_id", value: string | number | null) {
  if (!model.value) return;
  model.value = { ...model.value, [field]: value === "" ? null : value };
}

function remove() {
  preview.value = null;
  model.value = null;
}

function edit() {
  if (preview.value) openCropper(preview.value, /^data:(image\/\w+)/.exec(preview.value)?.[1] ?? "image/png");
}
</script>

<template>
  <div data-test="image-field">
    <div v-if="preview" class="mb-1">
      <img :src="preview" alt="" style="max-height: 20vh; max-width: 100%" data-test="preview" />
    </div>

    <div class="py-1">
      <div
        v-if="!preview"
        class="dropzone-wrapper mb-2 position-relative border border-2 border-dashed rounded text-center text-secondary p-3"
        style="border-style: dashed !important"
        :class="{ 'border-primary': dragover }"
        data-test="dropzone"
        @dragover.prevent="dragover = true"
        @dragleave="dragover = false"
        @drop.prevent="takeFile(($event as DragEvent).dataTransfer?.files?.[0])"
      >
        <i class="fa fa-upload"></i>
        <p class="mb-0">{{ t("Choose image file") }}&hellip;</p>
        <input
          ref="fileInput"
          type="file"
          name="photo"
          accept="image/*"
          class="position-absolute top-0 start-0 w-100 h-100 opacity-0"
          style="cursor: pointer"
          data-test="file"
          @change="onFileChange"
        />
      </div>
      <template v-else>
        <BButton variant="outline-secondary" class="me-1" data-test="edit" @click="edit">
          <i class="fa fa-edit"></i>
        </BButton>
        <BButton variant="outline-secondary" data-test="remove" @click="remove">
          <i class="fa fa-trash"></i>
        </BButton>
      </template>
    </div>

    <div v-if="message || errors?.image_base64" class="text-danger small mb-2" role="alert" data-test="image-error">
      {{ message ?? errors?.image_base64 }}
    </div>

    <template v-if="model">
      <BFormGroup
        :label="`${t('Copyright text')} *`"
        label-for="logo-copyright_text"
        :state="errors?.copyright_text ? false : null"
        :invalid-feedback="errors?.copyright_text"
        class="mb-3"
      >
        <BFormInput
          id="logo-copyright_text"
          :model-value="model.copyright_text ?? ''"
          maxlength="255"
          required
          :state="errors?.copyright_text ? false : null"
          @update:model-value="setField('copyright_text', $event as string)"
        />
      </BFormGroup>
      <BFormGroup
        :label="t('License')"
        label-for="logo-license"
        :description="t('Please select if the image should be displayed in external event calendars.')"
        class="mb-3"
      >
        <BFormSelect
          id="logo-license"
          :model-value="model.license_id"
          :options="licenseOptions"
          @update:model-value="setField('license_id', $event as number | null)"
        />
      </BFormGroup>
    </template>

    <ImageCropper
      v-model:show="showCropper"
      :src="cropSource"
      :mime-type="cropMime"
      :min-width="minSize"
      :min-height="minSize"
      @cropped="onCropped"
      @error="message = $event"
    />
  </div>
</template>
