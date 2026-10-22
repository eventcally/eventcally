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
  eventDates: (organizerId: number) => `/eventdates?organizer_id=${organizerId}`,
};

// Jinja manage area the admin links to.
export const manage = {
  organization: (id: number) => `/manage/admin_unit/${id}`,
};
