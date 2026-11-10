import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";
import { boot } from "@/shared/boot";
import CalendarEditPage from "./pages/CalendarEditPage.vue";
import CalendarsPage from "./pages/CalendarsPage.vue";
import CustomWidgetEditPage from "./pages/CustomWidgetEditPage.vue";
import CustomWidgetsPage from "./pages/CustomWidgetsPage.vue";
import EventEditPage from "./pages/EventEditPage.vue";
import EventOrganizerEditPage from "./pages/EventOrganizerEditPage.vue";
import EventPlaceEditPage from "./pages/EventPlaceEditPage.vue";
import EventReferenceRequestCreatePage from "./pages/EventReferenceRequestCreatePage.vue";
import EventReferenceRequestReviewPage from "./pages/EventReferenceRequestReviewPage.vue";
import ManageEventsPage from "./pages/ManageEventsPage.vue";
import NotFoundPage from "@/shared/NotFoundPage.vue";
import OrganizationCreatePage from "./pages/OrganizationCreatePage.vue";
import OrganizationExportPage from "./pages/OrganizationExportPage.vue";
import OrganizationRelationEditPage from "./pages/OrganizationRelationEditPage.vue";
import OrganizationSettingsPage from "./pages/OrganizationSettingsPage.vue";
import OrganizationVerificationRequestReviewPage from "./pages/OrganizationVerificationRequestReviewPage.vue";
import PlanningPage from "./pages/PlanningPage.vue";

export const routes: RouteRecordRaw[] = [
  { path: "/planning", name: "planning", component: PlanningPage },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/calendars",
    name: "calendars",
    component: CalendarsPage,
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/calendar/create",
    name: "calendar-create",
    component: CalendarEditPage,
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/calendar/:id(\\d+)/update",
    name: "calendar-update",
    component: CalendarEditPage,
    props: (route) => ({
      organizationId: Number(route.params.organizationId),
      id: Number(route.params.id),
    }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/custom-widgets",
    name: "custom-widgets",
    component: CustomWidgetsPage,
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/custom-widgets/create",
    name: "custom-widget-create",
    component: CustomWidgetEditPage,
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/custom-widgets/:id(\\d+)/update",
    name: "custom-widget-update",
    component: CustomWidgetEditPage,
    props: (route) => ({
      organizationId: Number(route.params.organizationId),
      id: Number(route.params.id),
    }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/events",
    name: "manage-events",
    component: ManageEventsPage,
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/event/create",
    name: "event-create",
    component: EventEditPage,
    props: (route) => ({
      organizationId: Number(route.params.organizationId),
      templateId: Number(route.query.template_id) || undefined,
    }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/event/:id(\\d+)/update",
    name: "event-update",
    component: EventEditPage,
    props: (route) => ({
      organizationId: Number(route.params.organizationId),
      id: Number(route.params.id),
    }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/event_organizers",
    name: "event-organizers",
    component: () => import("./pages/EventOrganizersPage.vue"),
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/event_places",
    name: "event-places",
    component: () => import("./pages/EventPlacesPage.vue"),
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/event/:id(\\d+)/delete",
    name: "event-delete",
    component: () => import("./pages/EventDeletePage.vue"),
    props: (route) => ({
      organizationId: Number(route.params.organizationId),
      id: Number(route.params.id),
    }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/incoming_event_references",
    name: "incoming-event-references",
    component: () => import("./pages/IncomingEventReferencesPage.vue"),
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/incoming_event_reference/:id(\\d+)",
    name: "incoming-event-reference",
    component: () => import("./pages/IncomingEventReferencePage.vue"),
    props: (route) => ({
      organizationId: Number(route.params.organizationId),
      id: Number(route.params.id),
    }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/outgoing_event_references",
    name: "outgoing-event-references",
    component: () => import("./pages/OutgoingEventReferencesPage.vue"),
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/incoming_event_reference_requests",
    name: "incoming-event-reference-requests",
    component: () => import("./pages/IncomingEventReferenceRequestsPage.vue"),
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/outgoing_event_reference_requests",
    name: "outgoing-event-reference-requests",
    component: () => import("./pages/OutgoingEventReferenceRequestsPage.vue"),
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/outgoing_event_reference_request/:id(\\d+)",
    name: "outgoing-event-reference-request",
    component: () => import("./pages/OutgoingEventReferenceRequestPage.vue"),
    props: (route) => ({
      organizationId: Number(route.params.organizationId),
      id: Number(route.params.id),
    }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/outgoing_organization_relations",
    name: "outgoing-organization-relations",
    component: () => import("./pages/OrganizationRelationsPage.vue"),
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/organization_members",
    name: "organization-members",
    component: () => import("./pages/MembersPage.vue"),
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/organization_member_invitations",
    name: "organization-member-invitations",
    component: () => import("./pages/MemberInvitationsPage.vue"),
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/organization_member_invitation/create",
    name: "organization-member-invitation-create",
    component: () => import("./pages/MemberInvitationCreatePage.vue"),
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/organization_invitations",
    name: "organization-invitations",
    component: () => import("./pages/OrganizationInvitationsPage.vue"),
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/organization_invitation/create",
    name: "organization-invitation-create",
    component: () => import("./pages/OrganizationInvitationEditPage.vue"),
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/organization_invitation/:id(\\d+)/update",
    name: "organization-invitation-update",
    component: () => import("./pages/OrganizationInvitationEditPage.vue"),
    props: (route) => ({
      organizationId: Number(route.params.organizationId),
      id: Number(route.params.id),
    }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/incoming_organization_verification_requests",
    name: "incoming-verification-requests",
    component: () => import("./pages/IncomingVerificationRequestsPage.vue"),
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/outgoing_organization_verification_requests",
    name: "outgoing-verification-requests",
    component: () => import("./pages/OutgoingVerificationRequestsPage.vue"),
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/outgoing_organization_verification_request/:id(\\d+)",
    name: "outgoing-verification-request",
    component: () => import("./pages/OutgoingVerificationRequestPage.vue"),
    props: (route) => ({
      organizationId: Number(route.params.organizationId),
      id: Number(route.params.id),
    }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/update",
    name: "organization-settings",
    component: OrganizationSettingsPage,
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/event_organizer/create",
    name: "event-organizer-create",
    component: EventOrganizerEditPage,
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/event_organizer/:id(\\d+)/update",
    name: "event-organizer-update",
    component: EventOrganizerEditPage,
    props: (route) => ({
      organizationId: Number(route.params.organizationId),
      id: Number(route.params.id),
    }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/event_place/create",
    name: "event-place-create",
    component: EventPlaceEditPage,
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/event_place/:id(\\d+)/update",
    name: "event-place-update",
    component: EventPlaceEditPage,
    props: (route) => ({
      organizationId: Number(route.params.organizationId),
      id: Number(route.params.id),
    }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/export",
    name: "organization-export",
    component: OrganizationExportPage,
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/incoming_event_reference_request/:id(\\d+)/review",
    name: "event-reference-request-review",
    component: EventReferenceRequestReviewPage,
    props: (route) => ({
      organizationId: Number(route.params.organizationId),
      id: Number(route.params.id),
    }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/incoming_organization_verification_request/:id(\\d+)/review",
    name: "verification-request-review",
    component: OrganizationVerificationRequestReviewPage,
    props: (route) => ({
      organizationId: Number(route.params.organizationId),
      id: Number(route.params.id),
    }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/outgoing_organization_relation/create",
    name: "outgoing-organization-relation-create",
    component: OrganizationRelationEditPage,
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/outgoing_organization_relation/:id(\\d+)/update",
    name: "outgoing-organization-relation-update",
    component: OrganizationRelationEditPage,
    props: (route) => ({
      organizationId: Number(route.params.organizationId),
      id: Number(route.params.id),
    }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/outgoing_event_reference_request/create_for_event/:eventId(\\d+)",
    name: "event-reference-request-create",
    component: EventReferenceRequestCreatePage,
    props: (route) => ({
      organizationId: Number(route.params.organizationId),
      eventId: Number(route.params.eventId),
    }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/api_keys",
    name: "organization-api-keys",
    component: () => import("./pages/OrganizationApiKeysPage.vue"),
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/api_key/create",
    name: "organization-api-key-create",
    component: () => import("./pages/OrganizationApiKeyCreatePage.vue"),
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/api_key/:id(\\d+)",
    name: "organization-api-key",
    component: () => import("./pages/OrganizationApiKeyPage.vue"),
    props: (route) => ({
      organizationId: Number(route.params.organizationId),
      id: Number(route.params.id),
    }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/oauth2_clients",
    name: "organization-oauth2-clients",
    component: () => import("./pages/OrganizationOAuth2ClientsPage.vue"),
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/oauth2_client/create",
    name: "organization-oauth2-client-create",
    component: () => import("./pages/OrganizationOAuth2ClientEditPage.vue"),
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/oauth2_client/:id(\\d+)",
    name: "organization-oauth2-client",
    component: () => import("./pages/OrganizationOAuth2ClientPage.vue"),
    props: (route) => ({
      organizationId: Number(route.params.organizationId),
      id: Number(route.params.id),
    }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/oauth2_client/:id(\\d+)/update",
    name: "organization-oauth2-client-update",
    component: () => import("./pages/OrganizationOAuth2ClientEditPage.vue"),
    props: (route) => ({
      organizationId: Number(route.params.organizationId),
      id: Number(route.params.id),
    }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/apps",
    name: "apps",
    component: () => import("./pages/AppsPage.vue"),
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/app/create",
    name: "app-create",
    component: () => import("./pages/AppEditPage.vue"),
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/app/:id(\\d+)",
    name: "app",
    component: () => import("./pages/AppPage.vue"),
    props: (route) => ({
      organizationId: Number(route.params.organizationId),
      id: Number(route.params.id),
    }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/app/:id(\\d+)/update",
    name: "app-update",
    component: () => import("./pages/AppEditPage.vue"),
    props: (route) => ({
      organizationId: Number(route.params.organizationId),
      id: Number(route.params.id),
    }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/app/:appId(\\d+)/webhook_deliveries",
    name: "webhook-deliveries",
    component: () => import("./pages/WebhookDeliveriesPage.vue"),
    props: (route) => ({
      organizationId: Number(route.params.organizationId),
      appId: Number(route.params.appId),
    }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/app/:appId(\\d+)/webhook_delivery/:id(\\d+)",
    name: "webhook-delivery",
    component: () => import("./pages/WebhookDeliveryPage.vue"),
    props: (route) => ({
      organizationId: Number(route.params.organizationId),
      appId: Number(route.params.appId),
      id: Number(route.params.id),
    }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/app_installations",
    name: "app-installations",
    component: () => import("./pages/AppInstallationsPage.vue"),
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/app_installations/install/:appId(\\d+)",
    name: "app-install",
    component: () => import("./pages/AppInstallPage.vue"),
    props: (route) => ({
      organizationId: Number(route.params.organizationId),
      appId: Number(route.params.appId),
    }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/app_installation/:id(\\d+)",
    name: "app-installation",
    component: () => import("./pages/AppInstallationPage.vue"),
    props: (route) => ({
      organizationId: Number(route.params.organizationId),
      id: Number(route.params.id),
    }),
  },
  { path: "/manage/admin_units", name: "organizations", component: () => import("./pages/OrganizationsPage.vue") },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/widgets",
    name: "organization-widgets",
    component: () => import("./pages/OrganizationWidgetsPage.vue"),
    props: (route) => ({ organizationId: Number(route.params.organizationId) }),
  },
  // Two URLs (the cancel link is mailed, the request link is on the settings page), one page.
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/request-deletion",
    name: "organization-request-deletion",
    component: () => import("./pages/OrganizationDeletionPage.vue"),
    props: (route) => ({ organizationId: Number(route.params.organizationId), mode: "request" }),
  },
  {
    path: "/manage/admin_unit/:organizationId(\\d+)/cancel-deletion",
    name: "organization-cancel-deletion",
    component: () => import("./pages/OrganizationDeletionPage.vue"),
    props: (route) => ({ organizationId: Number(route.params.organizationId), mode: "cancel" }),
  },
  { path: "/manage/organization/create", name: "organization-create", component: OrganizationCreatePage },
  { path: "/:rest(.*)*", name: "not-found", component: NotFoundPage },
];

export const router = createRouter({
  history: createWebHistory(boot.base),
  routes,
});
