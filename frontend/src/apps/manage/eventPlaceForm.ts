import type { components } from "@/api/schema";
import type { ImageValue } from "@/shared/ImageField.vue";
import type { LocationValue } from "@/shared/LocationFields.vue";

type PlaceForm = components["schemas"]["EventPlaceForm"];

// The fields of a place: the place page and the "new place" modal of the event form.
export interface EventPlaceFormValue {
  name: string;
  url: string;
  description: string;
  location: LocationValue;
  photo: ImageValue | null;
}

export const EVENT_PLACE_FORM_FIELDS = [
  "name",
  "url",
  "description",
  "location.street",
  "location.postalCode",
  "location.city",
  "location.state",
  "location.latitude",
  "location.longitude",
  "photo.image_base64",
  "photo.copyright_text",
  "photo.license_id",
];

export function emptyLocation(): LocationValue {
  return { street: "", postalCode: "", city: "", state: "", latitude: null, longitude: null };
}

/** The field values of a loaded place form. */
export function eventPlaceFormValue(data: PlaceForm): EventPlaceFormValue {
  return {
    name: data.name,
    url: data.url ?? "",
    description: data.description ?? "",
    location: {
      street: data.location.street ?? "",
      postalCode: data.location.postalCode ?? "",
      city: data.location.city ?? "",
      state: data.location.state ?? "",
      latitude: data.location.latitude ?? null,
      longitude: data.location.longitude ?? null,
    },
    // The stored image stays on the server (`image_base64: null`); the preview shows it.
    photo: data.photo
      ? {
          image_base64: null,
          copyright_text: data.photo.copyright_text ?? null,
          license_id: data.photo.license_id ?? null,
        }
      : null,
  };
}

/** The save body; `inline` when created from the modal of the event form (no flash). */
export function eventPlaceSaveBody(value: EventPlaceFormValue, inline = false) {
  return {
    name: value.name,
    url: value.url,
    description: value.description,
    location: { ...value.location },
    photo: value.photo ? { ...value.photo } : null,
    inline,
  };
}

/** How the place lookup labels a place (`get_place_str` on the server). */
export function eventPlaceLabel(value: EventPlaceFormValue): string {
  const { street, postalCode, city } = value.location;
  const name = value.name.trim();
  const location = street.trim()
    ? `${street}, ${postalCode} ${city}`
    : `${postalCode} ${city}`.trim();
  return location ? `${name}, ${location}` : name;
}
