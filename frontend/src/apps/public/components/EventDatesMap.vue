<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { formatEventDate } from "@/shared/format";

type EventDate = components["schemas"]["PublicEventDate"];
type Leaflet = typeof import("leaflet");

const props = defineProps<{ eventDates: EventDate[]; locale: string }>();
const emit = defineEmits<{ "show-in-list": [eventDateId: number] }>();

const { t } = useI18n();
const element = ref<HTMLElement | null>(null);

let L: Leaflet | null = null;
let map: import("leaflet").Map | null = null;
let cluster: import("leaflet").MarkerClusterGroup | null = null;

const CLUSTER_OFF_ZOOM = 16;
// A fly-to requested before Leaflet finished loading.
let pendingFlyTo: [number, number] | null = null;

async function load(): Promise<Leaflet> {
  const leaflet = (await import("leaflet")).default;
  // The cluster plugin extends the global Leaflet namespace.
  (window as unknown as { L: Leaflet }).L = leaflet;
  await import("leaflet.markercluster");
  await import("leaflet/dist/leaflet.css");
  await import("leaflet.markercluster/dist/MarkerCluster.css");
  await import("leaflet.markercluster/dist/MarkerCluster.Default.css");
  return leaflet;
}

function popupOf(eventDate: EventDate): HTMLElement {
  const root = document.createElement("div");
  root.append(
    `${formatEventDate(eventDate.start, null, eventDate.allday, props.locale)} `,
  );
  const link = document.createElement("a");
  link.href = `#event_card_${eventDate.id}`;
  link.textContent = eventDate.event.name;
  link.addEventListener("click", (event) => {
    event.preventDefault();
    emit("show-in-list", eventDate.id);
  });
  root.append(link);
  return root;
}

function plot() {
  if (!L || !map || !cluster) return;
  cluster.clearLayers();

  const markers = props.eventDates.flatMap((eventDate) => {
    const place = eventDate.event.place;
    if (!place || place.latitude == null || place.longitude == null) return [];
    const icon = L!.divIcon({
      className: "event-dates-marker",
      html: '<i class="fas fa-map-marker-alt"></i>',
      iconSize: [28, 41],
      iconAnchor: [14, 41],
      popupAnchor: [0, -36],
    });
    return [
      L!
        .marker([place.latitude, place.longitude], { icon })
        .bindPopup(() => popupOf(eventDate)),
    ];
  });

  if (!markers.length) return;
  cluster.addLayers(markers);
  map.fitBounds(cluster.getBounds());
}

function addLocateControl() {
  if (!L || !map || !("geolocation" in navigator)) return;
  const Locate = L.Control.extend({
    onAdd() {
      const container = L!.DomUtil.create("div", "leaflet-bar leaflet-control");
      const button = L!.DomUtil.create("a", "", container) as HTMLAnchorElement;
      button.href = "#";
      button.role = "button";
      button.title = t("Current location");
      button.setAttribute("aria-label", t("Current location"));
      button.innerHTML = '<i class="fa fa-location-arrow"></i>';
      L!.DomEvent.disableClickPropagation(container);
      L!.DomEvent.on(button, "click", (event) => {
        L!.DomEvent.preventDefault(event);
        navigator.geolocation.getCurrentPosition((position) => {
          map?.setView([position.coords.latitude, position.coords.longitude], map.getZoom());
        });
      });
      return container;
    },
  });
  new Locate({ position: "topleft" }).addTo(map);
}

onMounted(async () => {
  L = await load();
  if (!element.value) return;
  map = L.map(element.value).fitWorld();
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);
  cluster = L.markerClusterGroup({ disableClusteringAtZoom: CLUSTER_OFF_ZOOM });
  map.addLayer(cluster);
  addLocateControl();
  plot();

  if (pendingFlyTo) {
    map.flyTo(pendingFlyTo, CLUSTER_OFF_ZOOM);
    pendingFlyTo = null;
  }
});

watch(() => props.eventDates, plot);

onBeforeUnmount(() => {
  map?.remove();
  map = null;
});

defineExpose({
  flyTo(latitude: number, longitude: number) {
    if (map) map.flyTo([latitude, longitude], CLUSTER_OFF_ZOOM);
    else pendingFlyTo = [latitude, longitude];
  },
  /** Leaflet measures its container once; call after the container was shown or resized. */
  invalidate() {
    map?.invalidateSize();
  },
});
</script>

<template>
  <div ref="element" class="event-dates-map" role="region" :aria-label="t('Map view')"></div>
</template>

<style>
.event-dates-map {
  height: 400px;
}

.event-dates-marker {
  color: var(--bs-primary);
  font-size: 2.2rem;
  line-height: 1;
  text-align: center;
}
</style>
