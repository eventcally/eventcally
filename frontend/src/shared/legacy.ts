// Jinja pages the Vue apps link to (strangler fig); a constant, never taken from the DOM.
export const legacy = {
  login: "/login",
  flaskAdmin: "/admin/flask-admin/",
};

// Server-rendered pages the user area links to (account pages the SPA does not own).
export const account = {
  changePassword: "/change",
};

// Public server-rendered pages the admin links to.
export const publicPages = {
  home: "/",
  tos: "/tos",
  legalNotice: "/legal_notice",
  contact: "/contact",
  privacy: "/privacy",
  organization: (id: number) => `/organizations/${id}`,
  eventDatesSearch: "/eventdates",
  organizationEventDates: (id: number) => `/eventdates?admin_unit_id=${id}`,
  event: (id: number) => `/event/${id}`,
  organizer: (id: number) => `/organizers/${id}`,
  eventDate: (id: number) => `/eventdate/${id}`,
  eventDates: (organizerId: number) => `/eventdates?organizer_id=${organizerId}`,
  eventActions: (id: number) => `/event/${id}/actions`,
  eventReport: (id: number) => `/event/${id}/report`,
  eventReference: (id: number) => `/event/${id}/reference`,
};

// Jinja manage area the admin links to.
export const manage = {
  organizationCreate: (invitationId: number) =>
    `/manage/organization/create?invitation_id=${invitationId}`,
  organization: (id: number) => `/manage/admin_unit/${id}`,
  settings: (id: number) => `/manage/admin_unit/${id}/update`,
  requestDeletion: (id: number) => `/manage/admin_unit/${id}/request-deletion`,
  cancelDeletion: (id: number) => `/manage/admin_unit/${id}/cancel-deletion`,
  events: (organizationId: number) => `/manage/admin_unit/${organizationId}/events`,
  eventCreate: (organizationId: number) => `/manage/admin_unit/${organizationId}/event/create`,
  eventUpdate: (organizationId: number, id: number) =>
    `/manage/admin_unit/${organizationId}/event/${id}/update`,
  eventDelete: (organizationId: number, id: number) =>
    `/manage/admin_unit/${organizationId}/event/${id}/delete`,
  eventDuplicate: (organizationId: number, id: number) =>
    `/manage/admin_unit/${organizationId}/event/create?template_id=${id}`,
  outgoingEventReferenceRequest: (organizationId: number, id: number) =>
    `/manage/admin_unit/${organizationId}/outgoing_event_reference_request/${id}`,
  eventPlaceUpdate: (organizationId: number, id: number) =>
    `/manage/admin_unit/${organizationId}/event_place/${id}/update`,
  eventOrganizerUpdate: (organizationId: number, id: number) =>
    `/manage/admin_unit/${organizationId}/event_organizer/${id}/update`,
  eventReferenceRequestCreate: (organizationId: number, eventId: number) =>
    `/manage/admin_unit/${organizationId}/outgoing_event_reference_request/create_for_event/${eventId}`,
  customWidgets: (organizationId: number) => `/manage/admin_unit/${organizationId}/custom-widgets`,
  customWidgetCreate: (organizationId: number) =>
    `/manage/admin_unit/${organizationId}/custom-widgets/create`,
  customWidgetUpdate: (organizationId: number, id: number) =>
    `/manage/admin_unit/${organizationId}/custom-widgets/${id}/update`,
};
