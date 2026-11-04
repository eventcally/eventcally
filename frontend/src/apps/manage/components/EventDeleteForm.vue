<script setup lang="ts">
import { BButton, BOverlay } from "bootstrap-vue-next";
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import { errorMessage } from "@/shared/apiError";

type Form = components["schemas"]["EventDeleteForm"];
type Deleted = components["schemas"]["EventDeleted"];

// What the old event delete page showed: the question, the warning for an event with
// several dates and the delete button. Shared by `EventDeletePage` and `EventDeleteModal`.
const props = defineProps<{ organizationId: number; id: number; inline?: boolean }>();
const emit = defineEmits<{ deleted: [answer: Deleted] }>();

const { t } = useI18n();

const form = ref<Form | null>(null);
const loading = ref(true);
const busy = ref(false);
const error = ref<string | null>(null);

const instruction = computed(() =>
  t("Do you want to delete '%(object_title)s'?", { object_title: form.value?.name ?? "" }),
);

onMounted(async () => {
  const { data, error: err } = await api.GET(
    "/bff/manage/organizations/{id}/events/{event_id}/delete-form",
    { params: { path: { id: props.organizationId, event_id: props.id } } },
  );
  if (data) form.value = data;
  else error.value = errorMessage(err, t("Error"));
  loading.value = false;
});

async function remove() {
  if (busy.value) return;
  busy.value = true;
  error.value = null;
  const { data, error: err } = await api.POST(
    "/bff/manage/organizations/{id}/events/{event_id}/delete",
    {
      params: { path: { id: props.organizationId, event_id: props.id } },
      body: { inline: props.inline ?? false },
    },
  );
  busy.value = false;
  if (data) emit("deleted", data);
  else error.value = errorMessage(err, t("Error"));
}
</script>

<template>
  <BOverlay :show="loading">
    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>
    <template v-if="form">
      <p>{{ instruction }}</p>
      <div v-if="form.has_multiple_dates" class="alert alert-danger my-3" role="alert">
        {{
          t(
            "You are about to delete an event with multiple dates. If you want to delete a single date instead, you have to edit the event to do so.",
          )
        }}
        <div class="mt-3">
          <router-link
            class="btn btn-outline-dark"
            :to="{ name: 'event-update', params: { organizationId, id } }"
          >
            {{ t("Edit event") }}
          </router-link>
        </div>
      </div>
      <BButton id="submit" variant="danger" :disabled="busy" @click="remove">
        {{ t("Delete") }}
      </BButton>
    </template>
  </BOverlay>
</template>
