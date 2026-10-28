import type { components } from "@/api/schema";
import type { ImageValue } from "@/shared/ImageField.vue";
import type { LocationValue } from "@/shared/LocationFields.vue";

type OrganizerForm = components["schemas"]["EventOrganizerForm"];

// The fields of an organizer: the organizer page and the "new organizer" modal of the
// event form.
export interface EventOrganizerFormValue {
  name: string;
  url: string;
  email: string;
  phone: string;
  fax: string;
  location: LocationValue;
  logo: ImageValue | null;
}

export const EVENT_ORGANIZER_FORM_FIELDS = [
  "name",
  "url",
  "email",
  "phone",
  "fax",
  "location.street",
  "location.postalCode",
  "location.city",
  "location.state",
  "location.latitude",
  "location.longitude",
  "logo.image_base64",
  "logo.copyright_text",
  "logo.license_id",
];

/** The field values of a loaded organizer form. */
export function eventOrganizerFormValue(data: OrganizerForm): EventOrganizerFormValue {
  return {
    name: data.name,
    url: data.url ?? "",
    email: data.email ?? "",
    phone: data.phone ?? "",
    fax: data.fax ?? "",
    location: {
      street: data.location.street ?? "",
      postalCode: data.location.postalCode ?? "",
      city: data.location.city ?? "",
      state: data.location.state ?? "",
      latitude: data.location.latitude ?? null,
      longitude: data.location.longitude ?? null,
    },
    // The stored image stays on the server (`image_base64: null`); the preview shows it.
    logo: data.logo
      ? {
          image_base64: null,
          copyright_text: data.logo.copyright_text ?? null,
          license_id: data.logo.license_id ?? null,
        }
      : null,
  };
}

/** The save body; `inline` when created from the modal of the event form (no flash). */
export function eventOrganizerSaveBody(value: EventOrganizerFormValue, inline = false) {
  return {
    name: value.name,
    url: value.url,
    email: value.email,
    phone: value.phone,
    fax: value.fax,
    location: { ...value.location },
    logo: value.logo ? { ...value.logo } : null,
    inline,
  };
}
