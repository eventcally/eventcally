<script setup lang="ts">
import { BModal } from "bootstrap-vue-next";
import { ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";
import { errorMessage } from "@/shared/apiError";
import CalendarPicker from "@/shared/CalendarPicker.vue";
import { useNotify } from "@/shared/notify";

// Puts an event into calendars of an organization. Used by the manage pages and, through
// the `manage` BFF, by the public pages for members with `calendars:write`.
const props = defineProps<{ organizationId: number; eventId: number | null }>();
const show = defineModel<boolean>({ default: false });
const emit = defineEmits<{ saved: [] }>();

const { t } = useI18n();
const notify = useNotify();

type Choice = { id: number; name: string; private: boolean };

const choices = ref<Choice[]>([]);
const selected = ref<number[]>([]);
const loading = ref(false);
const busy = ref(false);
const error = ref<string | null>(null);

async function load() {
  if (props.eventId === null) return;
  loading.value = true;
  error.value = null;
  const { data, error: err } = await api.GET(
    "/bff/manage/organizations/{id}/events/{event_id}/calendars",
    { params: { path: { id: props.organizationId, event_id: props.eventId } } },
  );
  loading.value = false;

  if (!data) {
    error.value = errorMessage(err, t("Error"));
    return;
  }
  choices.value = data.choices;
  selected.value = [...data.selected_ids];
}

// Every opening starts with the calendars the event is in.
watch(show, (open) => {
  if (open) {
    choices.value = [];
    load();
  }
});

async function save() {
  if (busy.value || props.eventId === null) return;
  busy.value = true;
  error.value = null;

  const { data, error: err } = await api.PUT(
    "/bff/manage/organizations/{id}/events/{event_id}/calendars",
    {
      params: { path: { id: props.organizationId, event_id: props.eventId } },
      body: { calendar_ids: selected.value },
    },
  );
  busy.value = false;

  if (!data) {
    error.value = errorMessage(err, t("Error"));
    return;
  }

  notify.success(data.message);
  show.value = false;
  emit("saved");
}
</script>

<template>
  <BModal
    v-model="show"
    :title="t('Calendars')"
    :ok-title="t('Save')"
    :cancel-title="t('Cancel')"
    :ok-disabled="busy || loading || !choices.length"
    @ok.prevent="save"
  >
    <div v-if="error" class="alert alert-danger" role="alert" data-test="calendar-modal-error">
      {{ error }}
    </div>
    <p v-if="!loading && !error && !choices.length" data-test="no-calendars">
      {{ t("The organization has no calendars yet.") }}
      <a :href="`/manage/admin_unit/${organizationId}/calendar/create`">{{
        t("Manage calendars")
      }}</a>
    </p>
    <CalendarPicker v-model="selected" :choices="choices" id-prefix="assign-calendar" />
  </BModal>
</template>
