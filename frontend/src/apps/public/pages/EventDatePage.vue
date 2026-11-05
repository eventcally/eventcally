<script setup lang="ts">
import { BOverlay } from "bootstrap-vue-next";
import { onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import EventDetailView from "../components/EventDetailView.vue";

type PublicEventDateDetail = components["schemas"]["PublicEventDateDetail"];

const props = defineProps<{ id: number }>();

const { t } = useI18n();

const eventDate = ref<PublicEventDateDetail | null>(null);
const loading = ref(false);
const loadError = ref<string | null>(null);

async function load() {
  loading.value = true;
  loadError.value = null;
  const { data, error } = await api.GET("/bff/public/event-dates/{id}", {
    params: { path: { id: props.id } },
  });
  if (data) eventDate.value = data;
  else loadError.value = error?.message ?? t("Error");
  loading.value = false;
}

onMounted(load);
</script>

<template>
  <div>
    <div v-if="loadError" class="alert alert-danger m-3" role="alert">{{ loadError }}</div>

    <BOverlay :show="loading">
      <EventDetailView
        v-if="eventDate"
        :event="eventDate.event"
        :start="eventDate.start"
        :end="eventDate.end"
        :allday="eventDate.allday"
      />
    </BOverlay>
  </div>
</template>
