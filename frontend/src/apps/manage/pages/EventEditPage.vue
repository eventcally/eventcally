<script setup lang="ts">
import {
  BButton,
  BFormCheckbox,
  BFormInput,
  BFormSelect,
  BFormTags,
  BFormTextarea,
  BOverlay,
  BSpinner,
} from "bootstrap-vue-next";
import { computed, nextTick, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";
import AppTypeahead from "@/shared/AppTypeahead.vue";
import { toFieldErrors } from "@/shared/fieldErrors";
import ImageField from "@/shared/ImageField.vue";
import { manage } from "@/shared/legacy";
import MultiTypeahead from "@/shared/MultiTypeahead.vue";
import EventDateDefinitionFields from "../components/EventDateDefinitionFields.vue";
import EventOrganizerCreateModal from "../components/EventOrganizerCreateModal.vue";
import EventPlaceCreateModal from "../components/EventPlaceCreateModal.vue";
import LabeledField from "../components/LabeledField.vue";
import {
  eventFormFields,
  eventFormValue,
  eventSaveBody,
  newDateDefinition,
  splitDate,
  type EventFormValue,
  type Ref as Option,
} from "../eventForm";

type EventForm = components["schemas"]["EventForm"];

const props = defineProps<{ organizationId: number; id?: number; templateId?: number }>();

const { t } = useI18n();

type PublicStatus = components["schemas"]["EventPublicStatus"];

// Public statuses of the three create buttons.
const PUBLISHED: PublicStatus = 2;
const PLANNED: PublicStatus = 3;
const DRAFT: PublicStatus = 1;

const loading = ref(true);
const loadError = ref<string | null>(null);
const saving = ref(false);
const saveError = ref<string | null>(null);
const eventForm = ref<EventForm | null>(null);
const form = ref<EventFormValue | null>(null);
const photoPreview = ref<string | null>(null);
const errors = ref<Record<string, string>>({});
const showPlaceModal = ref(false);
const showOrganizerModal = ref(false);
// The public status of the create button that submitted the form.
const submitStatus = ref<PublicStatus>(PUBLISHED);

const isUpdate = computed(() => props.id !== undefined);
const title = computed(() =>
  t(isUpdate.value ? "Update %(model_display_name)s" : "Create %(model_display_name)s", {
    model_display_name: t("Event"),
  }),
);
const choices = (items: { value: number; label: string }[]) =>
  items.map((item) => ({ value: item.value, text: item.label }));

function state(key: string): false | null {
  return errors.value[key] ? false : null;
}

function fieldErrors(prefix: string): Record<string, string | undefined> {
  const result: Record<string, string | undefined> = {};
  for (const [key, message] of Object.entries(errors.value)) {
    if (key.startsWith(`${prefix}.`)) result[key.slice(prefix.length + 1)] = message;
  }
  return result;
}

async function lookupOrganizers(keyword: string): Promise<Option[]> {
  const { data } = await api.GET("/bff/manage/organizations/{id}/event-organizers", {
    params: { path: { id: props.organizationId }, query: { keyword } },
  });
  return data?.items ?? [];
}

async function lookupPlaces(keyword: string): Promise<Option[]> {
  const { data } = await api.GET("/bff/manage/organizations/{id}/event-places", {
    params: { path: { id: props.organizationId }, query: { keyword } },
  });
  return data?.items ?? [];
}

async function lookupCategories(keyword: string): Promise<Option[]> {
  const needle = keyword.toLowerCase();
  return (eventForm.value?.category_choices ?? []).filter((choice) =>
    choice.name.toLowerCase().includes(needle),
  );
}

function lookupCustomCategories(setId: number) {
  return async (keyword: string): Promise<Option[]> => {
    const { data } = await api.GET("/bff/manage/organizations/{id}/custom-event-categories", {
      params: { path: { id: props.organizationId }, query: { set_id: setId, keyword } },
    });
    return data?.items ?? [];
  };
}

async function load() {
  loading.value = true;
  const { data, error } = isUpdate.value
    ? await api.GET("/bff/manage/organizations/{id}/events/{event_id}/form", {
        params: { path: { id: props.organizationId, event_id: props.id! } },
      })
    : await api.GET("/bff/manage/organizations/{id}/events/create-form", {
        params: {
          path: { id: props.organizationId },
          query: props.templateId ? { template_id: props.templateId } : {},
        },
      });
  loading.value = false;

  if (!data) {
    loadError.value = error?.message ?? t("Error");
    return;
  }

  eventForm.value = data;
  form.value = eventFormValue(data);
  photoPreview.value = data.photo?.image_base64 ?? null;
}

function addDateDefinition() {
  const template = form.value!.dateDefinitions[0];
  const start = template
    ? { date: template.startDate, time: template.startTime }
    : splitDate(new Date());
  form.value!.dateDefinitions = [...form.value!.dateDefinitions, newDateDefinition(start)];
}

function removeDateDefinition(index: number) {
  form.value!.dateDefinitions = form.value!.dateDefinitions.filter((_, i) => i !== index);
}

function toggleReferenceRequest(id: number, checked: boolean) {
  const rest = form.value!.referenceRequestIds.filter((item) => item !== id);
  form.value!.referenceRequestIds = checked ? [...rest, id] : rest;
}

async function scrollToFirstInvalid() {
  await nextTick();
  document
    .querySelector(".is-invalid, [data-test=image-error], [data-test=field-error]")
    ?.scrollIntoView({ block: "center" });
}

async function save() {
  if (saving.value || !form.value) return;

  saving.value = true;
  saveError.value = null;
  errors.value = {};

  const common = eventSaveBody(form.value);
  const path = { id: props.organizationId };
  const { data, error } = isUpdate.value
    ? await api.PUT("/bff/manage/organizations/{id}/events/{event_id}", {
        params: { path: { ...path, event_id: props.id! } },
        body: {
          ...common,
          status: form.value.status ?? 1,
          public_status: form.value.publicStatus,
        },
      })
    : await api.POST("/bff/manage/organizations/{id}/events", {
        params: { path },
        body: {
          ...common,
          public_status: submitStatus.value,
          reference_request_ids: form.value.referenceRequestIds,
        },
      });

  if (data) {
    // The server flashed the success message; the next page renders it. Keep the spinner.
    location.assign(data.redirect_url);
    return;
  }

  saving.value = false;

  if (error && "errors" in error) {
    const mapped = toFieldErrors(error.errors, eventFormFields(form.value.dateDefinitions.length));
    errors.value = mapped.byKey;
    if (mapped.unmatched.length) saveError.value = mapped.unmatched.join(" ");
    await scrollToFirstInvalid();
  } else {
    saveError.value = error?.message ?? t("Error");
  }
}

onMounted(load);
</script>

<template>
  <div>
    <AppBreadcrumb :items="[{ label: t('Events'), href: manage.events(organizationId) }, { label: title }]" />

    <div v-if="loadError" class="alert alert-danger" role="alert">{{ loadError }}</div>

    <BOverlay :show="loading">
      <form v-if="eventForm && form" id="main-form" data-test="event-form" @submit.prevent="save">
        <div class="card mb-4">
          <div class="card-header">{{ t("Event") }}</div>
          <div class="card-body">
            <LabeledField
              :label="t('Name')"
              label-for="name"
              :description="t('Enter a short, meaningful name for the event.')"
              :error="errors.name"
              required
            >
              <BFormInput
                id="name"
                v-model="form.name"
                required
                minlength="3"
                maxlength="255"
                autocomplete="off"
                :state="state('name')"
              />
            </LabeledField>
            <LabeledField
              :label="t('Description')"
              label-for="description"
              :description="t('Add an description of the event.')"
              :error="errors.description"
            >
              <BFormTextarea id="description" v-model="form.description" style="min-height: 10rem" />
            </LabeledField>
          </div>
        </div>

        <div class="card mb-4">
          <div class="card-header">{{ t("Event dates") }}</div>
          <div class="card-body pb-3">
            <EventDateDefinitionFields
              v-for="(_, index) in form.dateDefinitions"
              :key="index"
              v-model="form.dateDefinitions[index]"
              :organization-id="organizationId"
              :index="index"
              :removable="form.dateDefinitions.length > 1"
              :errors="{
                start: errors[`date_definitions.${index}.start`],
                end: errors[`date_definitions.${index}.end`],
              }"
              @remove="removeDateDefinition(index)"
            />
            <div v-if="errors.date_definitions" class="invalid-feedback d-block mb-2">
              {{ errors.date_definitions }}
            </div>
            <BButton
              id="add-date-definition-btn"
              size="sm"
              variant="outline-secondary"
              @click="addDateDefinition"
            >
              <i class="fa fa-calendar-plus"></i> {{ t("Add event date") }}
            </BButton>
          </div>
        </div>

        <div v-if="isUpdate" class="card mb-4">
          <div class="card-header">{{ t("Status") }}</div>
          <div class="card-body">
            <LabeledField
              :label="t('Public status')"
              label-for="public_status"
              :description="t('Planned events appear in the scheduling view, but not on public calendars.')"
              :error="errors.public_status"
            >
              <BFormSelect
                id="public_status"
                v-model="form.publicStatus"
                :options="choices(eventForm.public_status_choices)"
              />
            </LabeledField>
            <LabeledField
              :label="t('Status')"
              label-for="status"
              :description="t('Select the status of the event.')"
              :error="errors.status"
            >
              <BFormSelect id="status" v-model="form.status" :options="choices(eventForm.status_choices)" />
            </LabeledField>
          </div>
        </div>

        <div class="card mb-4">
          <div class="card-header">{{ t("Organizer") }} *</div>
          <div class="card-body">
            <LabeledField
              :label="t('Organizer')"
              label-for="organizer"
              :description="
                t('Select the organizer. You can add and modify organizers at Organization > Organizers.')
              "
              :error="errors.organizer_id"
              hide-label
            >
              <div class="d-flex gap-1 align-items-start">
                <div class="flex-grow-1">
                  <AppTypeahead
                    v-model="form.organizer"
                    :fetch="lookupOrganizers"
                    :placeholder="t('Please select')"
                    input-id="organizer"
                  />
                </div>
                <a
                  v-if="isUpdate && form.organizer"
                  class="btn btn-outline-secondary"
                  :href="manage.eventOrganizerUpdate(organizationId, form.organizer.id)"
                  target="_blank"
                  :title="t('Update organizer')"
                  data-test="organizer-edit"
                >
                  <i class="fa fa-edit"></i>
                </a>
                <BButton
                  v-if="eventForm.can_create_organizer"
                  id="organizer-new-btn"
                  variant="outline-secondary"
                  class="text-nowrap"
                  @click="showOrganizerModal = true"
                >
                  <i class="fa fa-plus"></i> {{ t("New") }}
                </BButton>
              </div>
            </LabeledField>
            <LabeledField
              :label="t('Co-organizers')"
              label-for="co_organizers"
              :description="
                t(
                  'Select optional co-organizers. You can add and modify organizers at Organization > Organizers.',
                )
              "
              :error="errors.co_organizer_ids"
              class="mb-0"
            >
              <MultiTypeahead
                v-model="form.coOrganizers"
                :fetch="lookupOrganizers"
                :placeholder="t('Please select')"
                input-id="co_organizers"
              />
            </LabeledField>
          </div>
        </div>

        <div class="card mb-4">
          <div class="card-header">{{ t("Place") }} *</div>
          <div class="card-body">
            <LabeledField
              :label="t('Place')"
              label-for="event_place"
              :description="
                t('Choose where the event takes place. You can add and modify places at Organization > Places.')
              "
              :error="errors.event_place_id"
              hide-label
              class="mb-0"
            >
              <div class="d-flex gap-1 align-items-start">
                <div class="flex-grow-1">
                  <AppTypeahead
                    v-model="form.eventPlace"
                    :fetch="lookupPlaces"
                    :placeholder="t('Please select')"
                    input-id="event_place"
                  />
                </div>
                <a
                  v-if="isUpdate && form.eventPlace"
                  class="btn btn-outline-secondary"
                  :href="manage.eventPlaceUpdate(organizationId, form.eventPlace.id)"
                  target="_blank"
                  :title="t('Update place')"
                  data-test="event_place-edit"
                >
                  <i class="fa fa-edit"></i>
                </a>
                <BButton
                  v-if="eventForm.can_create_place"
                  id="event_place-new-btn"
                  variant="outline-secondary"
                  class="text-nowrap"
                  @click="showPlaceModal = true"
                >
                  <i class="fa fa-plus"></i> {{ t("New") }}
                </BButton>
              </div>
            </LabeledField>
          </div>
        </div>

        <div class="card mb-4">
          <div class="card-header">{{ t("Photo") }}</div>
          <div class="card-body">
            <p class="text-muted">
              {{
                t(
                  "We recommend uploading a photo for the event. It looks a lot more, but of course it works without it.",
                )
              }}
            </p>
            <ImageField
              v-model="form.photo"
              v-model:preview="photoPreview"
              :licenses="eventForm.licenses"
              :errors="fieldErrors('photo')"
              id-prefix="photo-"
            />
          </div>
        </div>

        <div class="card mb-4">
          <div class="card-header">{{ t("Access") }}</div>
          <div class="card-body">
            <LabeledField
              :label="t('Accessible for free')"
              label-for="accessible_for_free"
              :description="t('If the event is accessible for free.')"
            >
              <BFormCheckbox id="accessible_for_free" v-model="form.accessibleForFree" switch />
            </LabeledField>
            <LabeledField
              :label="t('Registration required')"
              label-for="registration_required"
              :description="t('If the participants needs to register for the event.')"
            >
              <BFormCheckbox id="registration_required" v-model="form.registrationRequired" switch />
            </LabeledField>
            <LabeledField
              :label="t('Price info')"
              label-for="price_info"
              :description="
                t('Enter price information in textual form. E.g., different prices for adults and children.')
              "
              :error="errors.price_info"
            >
              <BFormTextarea id="price_info" v-model="form.priceInfo" />
            </LabeledField>
            <LabeledField
              :label="t('Ticket Link URL')"
              label-for="ticket_link"
              :description="t('Enter a link where tickets can be purchased.')"
              :error="errors.ticket_link"
            >
              <BFormInput
                id="ticket_link"
                v-model="form.ticketLink"
                type="url"
                maxlength="255"
                :state="state('ticket_link')"
              />
            </LabeledField>
            <LabeledField
              :label="t('Booked up')"
              label-for="booked_up"
              :description="t('If the event is booked up or sold out.')"
            >
              <BFormCheckbox id="booked_up" v-model="form.bookedUp" switch />
            </LabeledField>
            <LabeledField
              :label="t('Attendance mode')"
              label-for="attendance_mode"
              :description="t('Choose how people can attend the event.')"
              class="mb-0"
            >
              <BFormSelect
                id="attendance_mode"
                v-model="form.attendanceMode"
                :options="choices(eventForm.attendance_mode_choices)"
              />
            </LabeledField>
          </div>
        </div>

        <div class="card mb-4">
          <div class="card-header">{{ t("Target group") }}</div>
          <div class="card-body">
            <LabeledField
              :label="t('Target group origin')"
              label-for="target_group_origin"
              :description="t('Choose whether the event is particularly suitable for tourists or residents.')"
            >
              <BFormSelect
                id="target_group_origin"
                v-model="form.targetGroupOrigin"
                :options="choices(eventForm.target_group_origin_choices)"
              />
            </LabeledField>
            <LabeledField
              :label="t('Kid friendly')"
              label-for="kid_friendly"
              :description="t('If the event is particularly suitable for children.')"
            >
              <BFormCheckbox id="kid_friendly" v-model="form.kidFriendly" switch />
            </LabeledField>
            <LabeledField
              :label="t('Typical Age from')"
              label-for="age_from"
              :description="t('The minimum age that participants should be.')"
              :error="errors.age_from"
            >
              <BFormInput id="age_from" v-model.number="form.ageFrom" type="number" :state="state('age_from')" />
            </LabeledField>
            <LabeledField
              :label="t('Typical Age to')"
              label-for="age_to"
              :description="t('The maximum age that participants should be.')"
              :error="errors.age_to"
            >
              <BFormInput id="age_to" v-model.number="form.ageTo" type="number" :state="state('age_to')" />
            </LabeledField>
            <LabeledField
              :label="t('Expected number of participants')"
              label-for="expected_participants"
              :description="t('The estimated expected attendance.')"
              :error="errors.expected_participants"
              class="mb-0"
            >
              <BFormInput
                id="expected_participants"
                v-model.number="form.expectedParticipants"
                type="number"
                :state="state('expected_participants')"
              />
            </LabeledField>
          </div>
        </div>

        <div class="card mb-4">
          <div class="card-header">{{ t("Additional information") }}</div>
          <div class="card-body">
            <LabeledField
              :label="t('Categories')"
              label-for="categories"
              :description="t('Choose categories that fit the event.')"
              :error="errors.category_ids"
              required
            >
              <MultiTypeahead
                v-model="form.categories"
                :fetch="lookupCategories"
                :placeholder="t('Please select')"
                input-id="categories"
              />
            </LabeledField>
            <LabeledField
              :label="t('Tags')"
              label-for="tags"
              :description="
                t(
                  'Enter keywords with which the event should be found. Words do not need to be entered if they are already in the name or description.',
                )
              "
              :error="errors.tags"
            >
              <BFormTags
                v-model="form.tags"
                input-id="tags"
                class="tag-field"
                :placeholder="t('Add tag')"
                :duplicate-tag-text="t('Duplicate tag(s)')"
                :invalid-tag-text="t('Invalid tag(s)')"
                :tag-remove-label="t('Remove tag')"
                :tag-removed-label="t('Tag removed')"
                separator=",;"
                no-outer-focus
              />
            </LabeledField>
            <LabeledField
              :label="t('Internal tags')"
              label-for="internal_tags"
              :description="t('Keywords for internal use. These will not be published.')"
              :error="errors.internal_tags"
            >
              <BFormTags
                v-model="form.internalTags"
                input-id="internal_tags"
                class="tag-field"
                :placeholder="t('Add internal tag')"
                :duplicate-tag-text="t('Duplicate tag(s)')"
                :invalid-tag-text="t('Invalid tag(s)')"
                :tag-remove-label="t('Remove tag')"
                :tag-removed-label="t('Tag removed')"
                separator=",;"
                no-outer-focus
              />
            </LabeledField>
            <LabeledField
              :label="t('Link URL')"
              label-for="external_link"
              :description="t('Enter a link to an external website containing more information about the event.')"
              :error="errors.external_link"
              class="mb-0"
            >
              <BFormInput
                id="external_link"
                v-model="form.externalLink"
                type="url"
                maxlength="255"
                :state="state('external_link')"
              />
            </LabeledField>
          </div>
        </div>

        <div v-if="eventForm.custom_category_sets.length" class="card mb-4">
          <div class="card-header">{{ t("Custom event categories") }}</div>
          <div class="card-body">
            <LabeledField
              v-for="set in eventForm.custom_category_sets"
              :key="set.id"
              :label="set.label"
              :label-for="`custom_categories-set_${set.id}`"
              :error="errors.custom_category_ids"
            >
              <MultiTypeahead
                v-model="form.customCategories[set.id]"
                :fetch="lookupCustomCategories(set.id)"
                :placeholder="t('Please select')"
                :input-id="`custom_categories-set_${set.id}`"
              />
            </LabeledField>
          </div>
        </div>

        <div v-if="eventForm.rating_choices.length > 1" class="card mb-4">
          <div class="card-header">{{ t("Rating") }}</div>
          <div class="card-body">
            <LabeledField
              :label="t('Rating')"
              label-for="rating"
              :description="
                t(
                  'Choose how relevant the event is to your organization. The value is not visible and is used for sorting.',
                )
              "
              :error="errors.rating"
              class="mb-0"
            >
              <BFormSelect id="rating" v-model="form.rating" :options="choices(eventForm.rating_choices)" />
            </LabeledField>
          </div>
        </div>

        <div v-if="!isUpdate && eventForm.reference_request_choices.length" class="card mb-4 border-info">
          <div class="card-header border-info text-info">{{ t("Reference requests") }}</div>
          <div class="card-body pb-0">
            <p class="text-muted">
              {{ t("References are important for the visibility of your events.") }}
              {{ t("Select organizations to display your event on their calendars.") }}
            </p>
            <div class="mb-3" data-test="reference-requests">
              <BFormCheckbox
                v-for="choice in eventForm.reference_request_choices"
                :id="`reference_request_admin_unit_id-${choice.id}`"
                :key="choice.id"
                :model-value="form.referenceRequestIds.includes(choice.id)"
                @update:model-value="toggleReferenceRequest(choice.id, Boolean($event))"
              >
                {{ choice.name }}
              </BFormCheckbox>
              <div v-if="errors.reference_request_ids" class="invalid-feedback d-block">
                {{ errors.reference_request_ids }}
              </div>
            </div>
          </div>
        </div>

        <div v-if="saveError" class="alert alert-danger" role="alert">{{ saveError }}</div>

        <template v-if="isUpdate">
          <BButton id="submit" type="submit" variant="primary" :disabled="saving">
            <BSpinner v-if="saving" small />
            {{ t("Update") }}
          </BButton>
        </template>
        <template v-else>
          <p class="px-2 text-muted">
            {{ t("Planned events appear in the scheduling view, but not on public calendars.") }}
          </p>
          <div class="d-flex flex-column flex-sm-row">
            <BButton
              id="submit"
              type="submit"
              variant="primary"
              class="m-1"
              :disabled="saving"
              @click="submitStatus = PUBLISHED"
            >
              <BSpinner v-if="saving && submitStatus === PUBLISHED" small />
              {{ t("Publish event") }}
            </BButton>
            <BButton
              id="submit_planned"
              type="submit"
              variant="secondary"
              class="m-1"
              :disabled="saving"
              @click="submitStatus = PLANNED"
            >
              <BSpinner v-if="saving && submitStatus === PLANNED" small />
              {{ t("Save as planned") }}
            </BButton>
            <BButton
              id="submit_draft"
              type="submit"
              variant="secondary"
              class="m-1"
              :disabled="saving"
              @click="submitStatus = DRAFT"
            >
              <BSpinner v-if="saving && submitStatus === DRAFT" small />
              {{ t("Save as draft") }}
            </BButton>
          </div>
        </template>
      </form>
    </BOverlay>

    <EventPlaceCreateModal
      v-model="showPlaceModal"
      :organization-id="organizationId"
      @created="form && (form.eventPlace = $event)"
    />
    <EventOrganizerCreateModal
      v-model="showOrganizerModal"
      :organization-id="organizationId"
      @created="form && (form.organizer = $event)"
    />
  </div>
</template>

<style scoped>
/* Tag fields: single-line input height, no add button, white close (CLAUDE.md § Frontend). */
.tag-field {
  padding-top: 0.25rem;
  padding-bottom: 0.25rem;
}
.tag-field :deep(.b-form-tags-list) {
  margin-top: 0;
}
.tag-field :deep(.b-form-tag),
.tag-field :deep(.b-from-tags-field) {
  margin-top: 0;
  margin-bottom: 0;
}
.tag-field :deep(.b-from-tags-field),
.tag-field :deep(.b-from-tags-field > div),
.tag-field :deep(.b-form-tags-input) {
  height: 24px;
  min-height: 0;
}
.tag-field :deep(.b-form-tags-button) {
  display: none;
}
.tag-field :deep(.btn-close) {
  filter: invert(1) grayscale(100%) brightness(200%);
  opacity: 1;
}
</style>
