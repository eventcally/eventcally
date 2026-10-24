import type { ImageValue } from "@/shared/ImageField.vue";
import type { LocationValue } from "@/shared/LocationFields.vue";

// The fields the settings and the create form of an organization share.
export interface OrganizationFormValue {
  name: string;
  short_name: string;
  description: string;
  location: LocationValue;
  logo: ImageValue | null;
  url: string;
  email: string;
  phone: string;
  fax: string;
}

export const ORGANIZATION_FORM_FIELDS = [
  "name",
  "short_name",
  "description",
  "location.street",
  "location.postalCode",
  "location.city",
  "location.state",
  "location.latitude",
  "location.longitude",
  "logo.image_base64",
  "logo.copyright_text",
  "logo.license_id",
  "url",
  "email",
  "phone",
  "fax",
];

export function emptyOrganizationForm(): OrganizationFormValue {
  return {
    name: "",
    short_name: "",
    description: "",
    location: { street: "", postalCode: "", city: "", state: "", latitude: null, longitude: null },
    logo: null,
    url: "",
    email: "",
    phone: "",
    fax: "",
  };
}
