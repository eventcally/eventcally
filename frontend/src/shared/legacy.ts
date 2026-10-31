// Jinja pages the Vue apps link to (strangler fig); a constant, never taken from the DOM.
export const legacy = {
  login: "/login",
  flaskAdmin: "/admin/flask-admin/",
};

// Public server-rendered pages the admin links to.
export const publicPages = {
  home: "/",
  tos: "/tos",
  legalNotice: "/legal_notice",
  contact: "/contact",
  privacy: "/privacy",
  organization: (id: number) => `/organizations/${id}`,
  organizationEventDates: (id: number) => `/eventdates?admin_unit_id=${id}`,
  event: (id: number) => `/event/${id}`,
  eventDate: (id: number) => `/eventdate/${id}`,
  eventDates: (organizerId: number) => `/eventdates?organizer_id=${organizerId}`,
  eventActions: (id: number) => `/event/${id}/actions`,
};

// Jinja manage area the admin links to.
export const manage = {
  organization: (id: number) => `/manage/admin_unit/${id}`,
  settings: (id: number) => `/manage/admin_unit/${id}/update`,
  requestDeletion: (id: number) => `/manage/admin_unit/${id}/request-deletion`,
  cancelDeletion: (id: number) => `/manage/admin_unit/${id}/cancel-deletion`,
  events: (organizationId: number) => `/manage/admin_unit/${organizationId}/events`,
  eventOrganizers: (organizationId: number) =>
    `/manage/admin_unit/${organizationId}/event_organizers`,
  eventPlaces: (organizationId: number) => `/manage/admin_unit/${organizationId}/event_places`,
  eventCreate: (organizationId: number) => `/manage/admin_unit/${organizationId}/event/create`,
  eventUpdate: (organizationId: number, id: number) =>
    `/manage/admin_unit/${organizationId}/event/${id}/update`,
  eventPlaceUpdate: (organizationId: number, id: number) =>
    `/manage/admin_unit/${organizationId}/event_place/${id}/update`,
  eventOrganizerUpdate: (organizationId: number, id: number) =>
    `/manage/admin_unit/${organizationId}/event_organizer/${id}/update`,
  eventDelete: (organizationId: number, id: number) =>
    `/manage/admin_unit/${organizationId}/event/${id}/delete`,
  eventReferenceRequestCreate: (organizationId: number, eventId: number) =>
    `/manage/admin_unit/${organizationId}/outgoing_event_reference_request/create_for_event/${eventId}`,
  outgoingOrganizationRelations: (organizationId: number) =>
    `/manage/admin_unit/${organizationId}/outgoing_organization_relations`,
  outgoingEventReferenceRequests: (organizationId: number) =>
    `/manage/admin_unit/${organizationId}/outgoing_event_reference_requests`,
  incomingEventReferenceRequests: (organizationId: number) =>
    `/manage/admin_unit/${organizationId}/incoming_event_reference_requests`,
  incomingVerificationRequests: (organizationId: number) =>
    `/manage/admin_unit/${organizationId}/incoming_organization_verification_requests`,
  customWidgets: (organizationId: number) => `/manage/admin_unit/${organizationId}/custom-widgets`,
  customWidgetCreate: (organizationId: number) =>
    `/manage/admin_unit/${organizationId}/custom-widgets/create`,
  customWidgetUpdate: (organizationId: number, id: number) =>
    `/manage/admin_unit/${organizationId}/custom-widgets/${id}/update`,
};
