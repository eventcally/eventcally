// The only place that knows the old Jinja admin URLs (strangler fig).
export const legacy = {
  home: "/admin",
  settings: "/admin/settings",
  organizations: "/admin/organizations",
  email: "/admin/email",
  newsletter: "/admin/newsletter",
  planning: "/admin/planning",
  flaskAdmin: "/admin/flask-admin/",
  userUpdate: (id: number) => `/admin/user/${id}/update`,
  userDelete: (id: number) => `/admin/user/${id}/delete`,
};
