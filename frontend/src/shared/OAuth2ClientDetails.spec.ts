import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createI18n } from "vue-i18n";
import OAuth2ClientDetails from "./OAuth2ClientDetails.vue";

describe("OAuth2ClientDetails", () => {
  it("lists the fields, joining the lists", () => {
    const wrapper = mount(OAuth2ClientDetails, {
      props: {
        client: {
          client_id: "id-1",
          client_secret: "secret",
          client_uri: null,
          grant_types: ["authorization_code", "refresh_token"],
          redirect_uris: ["/a", "/b"],
          response_types: ["code"],
          scope: "openid profile",
          token_endpoint_auth_method: ["none"],
        },
      },
      global: {
        plugins: [createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
      },
    });

    const text = wrapper.text();
    expect(text).toContain("id-1");
    expect(text).toContain("secret");
    expect(text).toContain("authorization_code, refresh_token");
    expect(text).toContain("/a, /b");
    expect(text).toContain("openid profile");
    expect(text).toContain("Grant types");
  });
});
