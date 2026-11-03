<script setup lang="ts">
import { useI18n } from "vue-i18n";

// The read view of an OAuth2 client as a definition list (the old `ReadDisplay`).
export interface OAuth2ClientDetail {
  client_id: string;
  client_secret?: string | null;
  client_uri?: string | null;
  grant_types: string[];
  redirect_uris: string[];
  response_types: string[];
  scope: string;
  token_endpoint_auth_method: string[];
}

defineProps<{ client: OAuth2ClientDetail }>();

const { t } = useI18n();
</script>

<template>
  <dl class="row" data-test="oauth2-client-details">
    <dt class="col-sm-3">{{ t("Client ID") }}</dt>
    <dd class="col-sm-9 text-break">{{ client.client_id }}</dd>
    <dt class="col-sm-3">{{ t("Client secret") }}</dt>
    <dd class="col-sm-9 text-break">{{ client.client_secret }}</dd>
    <dt class="col-sm-3">{{ t("Client URI") }}</dt>
    <dd class="col-sm-9 text-break">{{ client.client_uri }}</dd>
    <dt class="col-sm-3">{{ t("Grant types") }}</dt>
    <dd class="col-sm-9 text-break">{{ client.grant_types.join(", ") }}</dd>
    <dt class="col-sm-3">{{ t("Redirect URIs") }}</dt>
    <dd class="col-sm-9 text-break">{{ client.redirect_uris.join(", ") }}</dd>
    <dt class="col-sm-3">{{ t("Response types") }}</dt>
    <dd class="col-sm-9 text-break">{{ client.response_types.join(", ") }}</dd>
    <dt class="col-sm-3">{{ t("Scope") }}</dt>
    <dd class="col-sm-9 text-break">{{ client.scope }}</dd>
    <dt class="col-sm-3">{{ t("Token endpoint auth method") }}</dt>
    <dd class="col-sm-9 text-break">
      {{ client.token_endpoint_auth_method.join(", ") }}
    </dd>
  </dl>
</template>
