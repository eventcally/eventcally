<script setup lang="ts">
import { BFormGroup, BFormInput, BFormTextarea } from "bootstrap-vue-next";
import { reactive } from "vue";
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";
import ImageField from "@/shared/ImageField.vue";
import LocationFields from "@/shared/LocationFields.vue";
import type { OrganizationFormValue } from "../organizationForm";
import { suggestShortName } from "../organizationShortName";

type NameField = "name" | "short_name";

const props = defineProps<{
  licenses: { id: number; name: string }[];
  // The organization whose own names do not count as taken (settings).
  excludeId?: number;
  // The stored names: unchanged values need no check.
  originalNames?: { name: string; short_name: string };
  // Fill an empty short name from the name (create).
  suggestShortName?: boolean;
}>();

const form = defineModel<OrganizationFormValue>({ required: true });
const errors = defineModel<Record<string, string>>("errors", { required: true });
const logoPreview = defineModel<string | null>("logoPreview", { default: null });

const { t } = useI18n();

// Live availability of the name fields (`null`: not checked).
const taken = reactive<{ name: string | null; short_name: string | null }>({
  name: null,
  short_name: null,
});
const checkTimers: Partial<Record<NameField, ReturnType<typeof setTimeout>>> = {};
const CHECK_DELAY_MS = 300;
const SHORT_NAME_PATTERN = /^\w+$/;

function fieldErrors(prefix: string): Record<string, string | undefined> {
  const result: Record<string, string | undefined> = {};
  for (const [key, message] of Object.entries(errors.value)) {
    if (key.startsWith(`${prefix}.`)) result[key.slice(prefix.length + 1)] = message;
  }
  return result;
}

function nameState(field: NameField): boolean | null {
  if (errors.value[field] || taken[field]) return false;
  const value = form.value[field].trim();
  if (value && value === props.originalNames?.[field]) return null;
  return value && taken[field] === "" ? true : null;
}

function nameMessage(field: NameField) {
  return errors.value[field] ?? taken[field] ?? undefined;
}

function checkName(field: NameField) {
  clearTimeout(checkTimers[field]);
  const value = form.value[field].trim();
  const rest = { ...errors.value };
  delete rest[field];
  errors.value = rest;
  taken[field] = null;

  const valid =
    field === "name" ? value.length >= 5 : value.length >= 5 && SHORT_NAME_PATTERN.test(value);
  if (!valid || value === props.originalNames?.[field]) return;

  checkTimers[field] = setTimeout(async () => {
    const { data } = await api.GET("/bff/manage/organizations/name-availability", {
      params: { query: { [field]: value, exclude_id: props.excludeId } },
    });
    // The field changed while the request was in flight.
    if (!data || form.value[field].trim() !== value) return;
    const isTaken = field === "name" ? data.name_taken : data.short_name_taken;
    taken[field] = isTaken
      ? field === "name"
        ? t("Name is already taken")
        : t("Short name is already taken")
      : "";
  }, CHECK_DELAY_MS);
}

function suggest() {
  if (!props.suggestShortName || form.value.short_name) return;
  form.value.short_name = suggestShortName(form.value.name);
  checkName("short_name");
}

// Checks both names (and fills the short name) of a prefilled form.
function checkNames() {
  checkName("name");
  suggest();
  checkName("short_name");
}

defineExpose({ checkNames });
</script>

<template>
  <div>
    <BFormGroup
      :label="`${t('Name of organization')} *`"
      label-for="name"
      :description="t('The full name of the organization')"
      :state="nameState('name')"
      :invalid-feedback="nameMessage('name')"
      class="mb-3"
    >
      <BFormInput
        id="name"
        v-model="form.name"
        required
        minlength="5"
        maxlength="255"
        autocomplete="off"
        :state="nameState('name')"
        @update:model-value="checkName('name')"
        @blur="suggest"
      />
    </BFormGroup>

    <BFormGroup
      :label="`${t('Short name for organization')} *`"
      label-for="short_name"
      :description="t('The short name is used to create a unique identifier for your events')"
      :state="nameState('short_name')"
      :invalid-feedback="nameMessage('short_name')"
      class="mb-3"
    >
      <BFormInput
        id="short_name"
        v-model="form.short_name"
        required
        minlength="5"
        maxlength="100"
        pattern="\w+"
        :title="t('Short name must contain only letters numbers or underscore')"
        autocomplete="off"
        :state="nameState('short_name')"
        @update:model-value="checkName('short_name')"
      />
    </BFormGroup>

    <BFormGroup
      :label="t('Description')"
      label-for="description"
      :description="t('Describe the organization in a few words')"
      class="mb-3"
    >
      <BFormTextarea id="description" v-model="form.description" rows="2" />
    </BFormGroup>

    <div class="card mb-4">
      <div class="card-header">{{ t("Location") }}</div>
      <div class="card-body">
        <LocationFields v-model="form.location" :errors="fieldErrors('location')" />
      </div>
    </div>

    <div class="card mb-4">
      <div class="card-header">{{ t("Logo") }}</div>
      <div class="card-body">
        <ImageField
          v-model="form.logo"
          v-model:preview="logoPreview"
          :licenses="licenses"
          :errors="fieldErrors('logo')"
        />
      </div>
    </div>

    <div class="card mb-4">
      <div class="card-header">{{ t("Additional information") }}</div>
      <div class="card-body">
        <BFormGroup :label="t('Link URL')" label-for="additional_information-url" class="mb-3"
          :state="errors.url ? false : null" :invalid-feedback="errors.url">
          <BFormInput id="additional_information-url" v-model="form.url" type="url" maxlength="255"
            :state="errors.url ? false : null" />
        </BFormGroup>
        <BFormGroup :label="t('Email')" label-for="additional_information-email" class="mb-3"
          :state="errors.email ? false : null" :invalid-feedback="errors.email">
          <BFormInput id="additional_information-email" v-model="form.email" type="email" maxlength="255"
            :state="errors.email ? false : null" />
        </BFormGroup>
        <BFormGroup :label="t('Phone')" label-for="additional_information-phone" class="mb-3"
          :state="errors.phone ? false : null" :invalid-feedback="errors.phone">
          <BFormInput id="additional_information-phone" v-model="form.phone" type="tel" maxlength="255"
            :state="errors.phone ? false : null" />
        </BFormGroup>
        <BFormGroup :label="t('Fax')" label-for="additional_information-fax" class="mb-3"
          :state="errors.fax ? false : null" :invalid-feedback="errors.fax">
          <BFormInput id="additional_information-fax" v-model="form.fax" type="tel" maxlength="255"
            :state="errors.fax ? false : null" />
        </BFormGroup>
      </div>
    </div>
  </div>
</template>
