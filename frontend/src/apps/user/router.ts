import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";
import { boot } from "@/shared/boot";
import NotFoundPage from "@/shared/NotFoundPage.vue";
import AcceptTosPage from "./pages/AcceptTosPage.vue";
import AccountDeletionPage from "./pages/AccountDeletionPage.vue";
import ApiKeyDeletePage from "./pages/ApiKeyDeletePage.vue";
import ApiKeyEditPage from "./pages/ApiKeyEditPage.vue";
import ApiKeyPage from "./pages/ApiKeyPage.vue";
import ApiKeysPage from "./pages/ApiKeysPage.vue";
import GeneralSettingsPage from "./pages/GeneralSettingsPage.vue";
import MemberInvitationPage from "./pages/MemberInvitationPage.vue";
import MemberInvitationsPage from "./pages/MemberInvitationsPage.vue";
import MembershipLeavePage from "./pages/MembershipLeavePage.vue";
import MembershipsPage from "./pages/MembershipsPage.vue";
import NotificationSettingsPage from "./pages/NotificationSettingsPage.vue";
import OAuth2ClientDeletePage from "./pages/OAuth2ClientDeletePage.vue";
import OAuth2ClientEditPage from "./pages/OAuth2ClientEditPage.vue";
import OAuth2ClientPage from "./pages/OAuth2ClientPage.vue";
import OAuth2ClientsPage from "./pages/OAuth2ClientsPage.vue";
import OAuth2TokenRevokePage from "./pages/OAuth2TokenRevokePage.vue";
import OAuth2TokensPage from "./pages/OAuth2TokensPage.vue";
import OrganizationInvitationPage from "./pages/OrganizationInvitationPage.vue";
import OrganizationInvitationsPage from "./pages/OrganizationInvitationsPage.vue";
import ProfilePage from "./pages/ProfilePage.vue";

// The URLs (and their endpoint names in Flask) are a contract: e-mails, the invitation
// landings and bookmarks link to them.
const idProps = (name: string) => (route: { params: Record<string, unknown> }) => ({
  id: Number(route.params[name]),
});

export const routes: RouteRecordRaw[] = [
  { path: "/profile", name: "profile", component: ProfilePage },
  { path: "/user/general", name: "general", component: GeneralSettingsPage },
  {
    path: "/user/notifications",
    name: "notifications",
    component: NotificationSettingsPage,
  },
  {
    path: "/user/request-deletion",
    name: "request-deletion",
    component: AccountDeletionPage,
    props: { mode: "request" },
  },
  {
    path: "/user/cancel-deletion",
    name: "cancel-deletion",
    component: AccountDeletionPage,
    props: { mode: "cancel" },
  },
  {
    path: "/user/accept-tos",
    name: "accept-tos",
    component: AcceptTosPage,
    props: (route) => ({
      next: typeof route.query.next === "string" ? route.query.next : undefined,
    }),
  },
  { path: "/user/api_keys", name: "api-keys", component: ApiKeysPage },
  {
    path: "/user/api_key/create",
    name: "api-key-create",
    component: ApiKeyEditPage,
  },
  {
    path: "/user/api_key/:apiKeyId(\\d+)",
    name: "api-key",
    component: ApiKeyPage,
    props: idProps("apiKeyId"),
  },
  {
    path: "/user/api_key/:apiKeyId(\\d+)/update",
    name: "api-key-update",
    component: ApiKeyEditPage,
    props: idProps("apiKeyId"),
  },
  {
    path: "/user/api_key/:apiKeyId(\\d+)/delete",
    name: "api-key-delete",
    component: ApiKeyDeletePage,
    props: idProps("apiKeyId"),
  },
  {
    path: "/user/oauth2_clients",
    name: "oauth2-clients",
    component: OAuth2ClientsPage,
  },
  {
    path: "/user/oauth2_client/create",
    name: "oauth2-client-create",
    component: OAuth2ClientEditPage,
  },
  {
    path: "/user/oauth2_client/:clientId(\\d+)",
    name: "oauth2-client",
    component: OAuth2ClientPage,
    props: idProps("clientId"),
  },
  {
    path: "/user/oauth2_client/:clientId(\\d+)/update",
    name: "oauth2-client-update",
    component: OAuth2ClientEditPage,
    props: idProps("clientId"),
  },
  {
    path: "/user/oauth2_client/:clientId(\\d+)/delete",
    name: "oauth2-client-delete",
    component: OAuth2ClientDeletePage,
    props: idProps("clientId"),
  },
  {
    path: "/user/oauth2_tokens",
    name: "oauth2-tokens",
    component: OAuth2TokensPage,
  },
  {
    path: "/user/oauth2_token/:tokenId(\\d+)/revoke",
    name: "oauth2-token-revoke",
    component: OAuth2TokenRevokePage,
    props: idProps("tokenId"),
  },
  {
    path: "/user/organization_members",
    name: "memberships",
    component: MembershipsPage,
  },
  {
    path: "/user/organization_member/:memberId(\\d+)/delete",
    name: "membership-leave",
    component: MembershipLeavePage,
    props: idProps("memberId"),
  },
  {
    path: "/user/organization_member_invitations",
    name: "member-invitations",
    component: MemberInvitationsPage,
  },
  {
    path: "/user/organization_member_invitation/:invitationId(\\d+)/negotiate",
    name: "member-invitation",
    component: MemberInvitationPage,
    props: idProps("invitationId"),
  },
  {
    path: "/user/organization_invitations",
    name: "organization-invitations",
    component: OrganizationInvitationsPage,
  },
  {
    path: "/user/organization_invitation/:invitationId(\\d+)/negotiate",
    name: "organization-invitation",
    component: OrganizationInvitationPage,
    props: idProps("invitationId"),
  },
  { path: "/:rest(.*)*", name: "not-found", component: NotFoundPage },
];

export const router = createRouter({
  history: createWebHistory(boot.base),
  routes,
});
