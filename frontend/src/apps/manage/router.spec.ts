import { describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

vi.mock("@/shared/boot", () => ({ boot: { base: "/" } }));
// FullCalendar does not render in jsdom; the router only needs the page component.
vi.mock("./pages/PlanningPage.vue", () => ({ default: { render: () => null } }));

import { routes } from "./router";

async function resolve(path: string) {
  const router = createRouter({ history: createMemoryHistory(), routes });
  await router.push(path);
  return router.currentRoute.value;
}

describe("manage router", () => {
  it("resolves the planning page", async () => {
    expect((await resolve("/planning")).name).toBe("planning");
  });

  it("resolves the custom widget list with a numeric organization", async () => {
    const route = await resolve("/manage/admin_unit/3/custom-widgets");
    expect(route.name).toBe("custom-widgets");
    expect(route.params.organizationId).toBe("3");
  });

  it("resolves the organization export with a numeric organization", async () => {
    const route = await resolve("/manage/admin_unit/3/export");
    expect(route.name).toBe("organization-export");
    expect(route.params.organizationId).toBe("3");
    expect((await resolve("/manage/admin_unit/x/export")).name).toBe("not-found");
  });

  it("resolves the event create page and passes the template", async () => {
    const route = await resolve("/manage/admin_unit/3/event/create?template_id=7");
    expect(route.name).toBe("event-create");
    const props = route.matched[0].props.default as (r: typeof route) => Record<string, unknown>;
    expect(props(route)).toEqual({ organizationId: 3, templateId: 7 });

    const plain = await resolve("/manage/admin_unit/3/event/create");
    expect(props(plain)).toEqual({ organizationId: 3, templateId: undefined });
  });

  it("resolves the event update page with numeric ids", async () => {
    const route = await resolve("/manage/admin_unit/3/event/9/update");
    expect(route.name).toBe("event-update");
    const props = route.matched[0].props.default as (r: typeof route) => Record<string, unknown>;
    expect(props(route)).toEqual({ organizationId: 3, id: 9 });
    expect((await resolve("/manage/admin_unit/3/event/x/update")).name).toBe("not-found");
  });

  it("resolves the organization settings with a numeric organization", async () => {
    const route = await resolve("/manage/admin_unit/3/update");
    expect(route.name).toBe("organization-settings");
    expect(route.params.organizationId).toBe("3");
    expect((await resolve("/manage/admin_unit/x/update")).name).toBe("not-found");
  });

  it("resolves the organization create page and keeps the invitation", async () => {
    const route = await resolve("/manage/organization/create?invitation_id=4");
    expect(route.name).toBe("organization-create");
    expect(route.query.invitation_id).toBe("4");
  });

  it("resolves the event list with a numeric organization and keeps the query", async () => {
    const route = await resolve("/manage/admin_unit/3/events?event_place_id=5");
    expect(route.name).toBe("manage-events");
    expect(route.params.organizationId).toBe("3");
    expect(route.query.event_place_id).toBe("5");
    expect((await resolve("/manage/admin_unit/x/events")).name).toBe("not-found");
  });

  it("resolves the configurator for create and update", async () => {
    expect((await resolve("/manage/admin_unit/3/custom-widgets/create")).name).toBe(
      "custom-widget-create",
    );
    const update = await resolve("/manage/admin_unit/3/custom-widgets/8/update");
    expect(update.name).toBe("custom-widget-update");
    expect(update.params).toMatchObject({ organizationId: "3", id: "8" });
  });

  it("resolves the organizer form for create and update", async () => {
    const create = await resolve("/manage/admin_unit/3/event_organizer/create");
    expect(create.name).toBe("event-organizer-create");
    expect(create.params.organizationId).toBe("3");

    const update = await resolve("/manage/admin_unit/3/event_organizer/8/update");
    expect(update.name).toBe("event-organizer-update");
    expect(update.params).toMatchObject({ organizationId: "3", id: "8" });
    expect((await resolve("/manage/admin_unit/3/event_organizer/x/update")).name).toBe("not-found");
    expect((await resolve("/manage/admin_unit/x/event_organizer/create")).name).toBe("not-found");
  });

  it("resolves the place form for create and update", async () => {
    const create = await resolve("/manage/admin_unit/3/event_place/create");
    expect(create.name).toBe("event-place-create");
    expect(create.params.organizationId).toBe("3");

    const update = await resolve("/manage/admin_unit/3/event_place/8/update");
    expect(update.name).toBe("event-place-update");
    expect(update.params).toMatchObject({ organizationId: "3", id: "8" });
    expect((await resolve("/manage/admin_unit/3/event_place/x/update")).name).toBe("not-found");
    expect((await resolve("/manage/admin_unit/x/event_place/create")).name).toBe("not-found");
  });

  it("resolves the organizer and place lists and the event delete page", async () => {
    const organizers = await resolve("/manage/admin_unit/3/event_organizers?keyword=x");
    expect(organizers.name).toBe("event-organizers");
    expect(organizers.matched[0].props.default).toBeTypeOf("function");
    const orgProps = organizers.matched[0].props.default as (r: typeof organizers) => unknown;
    expect(orgProps(organizers)).toEqual({ organizationId: 3 });

    const places = await resolve("/manage/admin_unit/3/event_places");
    expect(places.name).toBe("event-places");
    const placeProps = places.matched[0].props.default as (r: typeof places) => unknown;
    expect(placeProps(places)).toEqual({ organizationId: 3 });

    const remove = await resolve("/manage/admin_unit/3/event/9/delete");
    expect(remove.name).toBe("event-delete");
    const removeProps = remove.matched[0].props.default as (r: typeof remove) => unknown;
    expect(removeProps(remove)).toEqual({ organizationId: 3, id: 9 });
    expect((await resolve("/manage/admin_unit/3/event/x/delete")).name).toBe("not-found");
    expect((await resolve("/manage/admin_unit/x/event_places")).name).toBe("not-found");
  });

  it("does not take other organization paths", async () => {
    expect((await resolve("/manage/admin_unit/x/custom-widgets")).name).toBe("not-found");
    expect((await resolve("/manage/admin_unit/3/custom-widgets/x/update")).name).toBe("not-found");
  });

  it("renders unknown paths as not found", async () => {
    expect((await resolve("/x")).name).toBe("not-found");
  });

  it("resolves the review pages with numeric ids", async () => {
    const reference = await resolve("/manage/admin_unit/3/incoming_event_reference_request/7/review");
    expect(reference.name).toBe("event-reference-request-review");
    expect(reference.params).toMatchObject({ organizationId: "3", id: "7" });

    const verification = await resolve(
      "/manage/admin_unit/3/incoming_organization_verification_request/9/review",
    );
    expect(verification.name).toBe("verification-request-review");
    expect(verification.params).toMatchObject({ organizationId: "3", id: "9" });

    expect(
      (await resolve("/manage/admin_unit/3/incoming_event_reference_request/x/review")).name,
    ).toBe("not-found");
  });

  it("resolves the outgoing relation and reference request forms with numeric ids", async () => {
    const create = await resolve("/manage/admin_unit/3/outgoing_organization_relation/create");
    expect(create.name).toBe("outgoing-organization-relation-create");
    expect(create.params).toMatchObject({ organizationId: "3" });

    const update = await resolve("/manage/admin_unit/3/outgoing_organization_relation/7/update");
    expect(update.name).toBe("outgoing-organization-relation-update");
    expect(update.params).toMatchObject({ organizationId: "3", id: "7" });

    const request = await resolve(
      "/manage/admin_unit/3/outgoing_event_reference_request/create_for_event/9",
    );
    expect(request.name).toBe("event-reference-request-create");
    expect(request.params).toMatchObject({ organizationId: "3", eventId: "9" });

    expect(
      (await resolve("/manage/admin_unit/3/outgoing_organization_relation/x/update")).name,
    ).toBe("not-found");
  });

  it("resolves the reference and reference request pages", async () => {
    const lists = [
      ["incoming_event_references", "incoming-event-references"],
      ["outgoing_event_references", "outgoing-event-references"],
      ["incoming_event_reference_requests", "incoming-event-reference-requests"],
      ["outgoing_event_reference_requests", "outgoing-event-reference-requests"],
    ];
    for (const [path, name] of lists) {
      const route = await resolve(`/manage/admin_unit/3/${path}`);
      expect(route.name).toBe(name);
      const props = route.matched[0].props.default as (r: typeof route) => unknown;
      expect(props(route)).toEqual({ organizationId: 3 });
      expect((await resolve(`/manage/admin_unit/x/${path}`)).name).toBe("not-found");
    }

    const reads = [
      ["incoming_event_reference", "incoming-event-reference"],
      ["outgoing_event_reference_request", "outgoing-event-reference-request"],
    ];
    for (const [path, name] of reads) {
      const route = await resolve(`/manage/admin_unit/3/${path}/7`);
      expect(route.name).toBe(name);
      const props = route.matched[0].props.default as (r: typeof route) => unknown;
      expect(props(route)).toEqual({ organizationId: 3, id: 7 });
      expect((await resolve(`/manage/admin_unit/3/${path}/x`)).name).toBe("not-found");
    }
  });

  it("resolves the relation and verification request pages", async () => {
    const lists = [
      ["outgoing_organization_relations", "outgoing-organization-relations"],
      ["incoming_organization_verification_requests", "incoming-verification-requests"],
      ["outgoing_organization_verification_requests", "outgoing-verification-requests"],
    ];
    for (const [path, name] of lists) {
      const route = await resolve(`/manage/admin_unit/3/${path}`);
      expect(route.name).toBe(name);
      const props = route.matched[0].props.default as (r: typeof route) => unknown;
      expect(props(route)).toEqual({ organizationId: 3 });
      expect((await resolve(`/manage/admin_unit/x/${path}`)).name).toBe("not-found");
    }

    const read = await resolve("/manage/admin_unit/3/outgoing_organization_verification_request/7");
    expect(read.name).toBe("outgoing-verification-request");
    const props = read.matched[0].props.default as (r: typeof read) => unknown;
    expect(props(read)).toEqual({ organizationId: 3, id: 7 });
    expect(
      (await resolve("/manage/admin_unit/3/outgoing_organization_verification_request/x")).name,
    ).toBe("not-found");
  });

  it("resolves the member and invitation pages", async () => {
    const lists = [
      ["organization_members", "organization-members"],
      ["organization_member_invitations", "organization-member-invitations"],
      ["organization_member_invitation/create", "organization-member-invitation-create"],
      ["organization_invitations", "organization-invitations"],
      ["organization_invitation/create", "organization-invitation-create"],
    ];
    for (const [path, name] of lists) {
      const route = await resolve(`/manage/admin_unit/3/${path}`);
      expect(route.name).toBe(name);
      const props = route.matched[0].props.default as (r: typeof route) => unknown;
      expect(props(route)).toEqual({ organizationId: 3 });
      expect((await resolve(`/manage/admin_unit/x/${path}`)).name).toBe("not-found");
    }

    const update = await resolve("/manage/admin_unit/3/organization_invitation/7/update");
    expect(update.name).toBe("organization-invitation-update");
    const props = update.matched[0].props.default as (r: typeof update) => unknown;
    expect(props(update)).toEqual({ organizationId: 3, id: 7 });
    expect((await resolve("/manage/admin_unit/3/organization_invitation/x/update")).name).toBe(
      "not-found",
    );
  });

  it("resolves the organization list, the widgets and the deletion pages", async () => {
    expect((await resolve("/manage/admin_units")).name).toBe("organizations");

    const pages = [
      ["widgets", "organization-widgets", undefined],
      ["request-deletion", "organization-request-deletion", "request"],
      ["cancel-deletion", "organization-cancel-deletion", "cancel"],
    ] as const;
    for (const [path, name, mode] of pages) {
      const route = await resolve(`/manage/admin_unit/3/${path}`);
      expect(route.name).toBe(name);
      const props = route.matched[0].props.default as (r: typeof route) => unknown;
      expect(props(route)).toEqual(mode ? { organizationId: 3, mode } : { organizationId: 3 });
      expect((await resolve(`/manage/admin_unit/x/${path}`)).name).toBe("not-found");
    }
  });

  it("resolves the organization API key and OAuth2 client pages", async () => {
    const lists = [
      ["api_keys", "organization-api-keys"],
      ["api_key/create", "organization-api-key-create"],
      ["oauth2_clients", "organization-oauth2-clients"],
      ["oauth2_client/create", "organization-oauth2-client-create"],
    ];
    for (const [path, name] of lists) {
      const route = await resolve(`/manage/admin_unit/3/${path}`);
      expect(route.name).toBe(name);
      const props = route.matched[0].props.default as (r: typeof route) => unknown;
      expect(props(route)).toEqual({ organizationId: 3 });
      expect((await resolve(`/manage/admin_unit/x/${path}`)).name).toBe("not-found");
    }

    const objects = [
      ["api_key/7", "organization-api-key"],
      ["oauth2_client/7", "organization-oauth2-client"],
      ["oauth2_client/7/update", "organization-oauth2-client-update"],
    ];
    for (const [path, name] of objects) {
      const route = await resolve(`/manage/admin_unit/3/${path}`);
      expect(route.name).toBe(name);
      const props = route.matched[0].props.default as (r: typeof route) => unknown;
      expect(props(route)).toEqual({ organizationId: 3, id: 7 });
      expect((await resolve(`/manage/admin_unit/3/${path.replace("7", "x")}`)).name).toBe(
        "not-found",
      );
    }

    // The removed update / delete URLs of an API key resolve to nothing.
    expect((await resolve("/manage/admin_unit/3/api_key/7/update")).name).toBe("not-found");
    expect((await resolve("/manage/admin_unit/3/api_key/7/delete")).name).toBe("not-found");
    expect((await resolve("/manage/admin_unit/3/oauth2_client/7/delete")).name).toBe("not-found");
  });

  it("resolves the app and app installation pages", async () => {
    const lists = [
      ["apps", "apps"],
      ["app/create", "app-create"],
      ["app_installations", "app-installations"],
    ];
    for (const [path, name] of lists) {
      const route = await resolve(`/manage/admin_unit/3/${path}`);
      expect(route.name).toBe(name);
      const props = route.matched[0].props.default as (r: typeof route) => unknown;
      expect(props(route)).toEqual({ organizationId: 3 });
      expect((await resolve(`/manage/admin_unit/x/${path}`)).name).toBe("not-found");
    }

    const objects = [
      ["app/7", "app"],
      ["app/7/update", "app-update"],
      ["app_installation/7", "app-installation"],
    ];
    for (const [path, name] of objects) {
      const route = await resolve(`/manage/admin_unit/3/${path}`);
      expect(route.name).toBe(name);
      const props = route.matched[0].props.default as (r: typeof route) => unknown;
      expect(props(route)).toEqual({ organizationId: 3, id: 7 });
      expect((await resolve(`/manage/admin_unit/3/${path.replace("7", "x")}`)).name).toBe(
        "not-found",
      );
    }

    const install = await resolve("/manage/admin_unit/3/app_installations/install/8");
    expect(install.name).toBe("app-install");
    const installProps = install.matched[0].props.default as (r: typeof install) => unknown;
    expect(installProps(install)).toEqual({ organizationId: 3, appId: 8 });

    const deliveries = await resolve("/manage/admin_unit/3/app/5/webhook_deliveries");
    expect(deliveries.name).toBe("webhook-deliveries");
    const deliveriesProps = deliveries.matched[0].props.default as (r: typeof deliveries) => unknown;
    expect(deliveriesProps(deliveries)).toEqual({ organizationId: 3, appId: 5 });

    const delivery = await resolve("/manage/admin_unit/3/app/5/webhook_delivery/9");
    expect(delivery.name).toBe("webhook-delivery");
    const deliveryProps = delivery.matched[0].props.default as (r: typeof delivery) => unknown;
    expect(deliveryProps(delivery)).toEqual({ organizationId: 3, appId: 5, id: 9 });

    // The removed delete, key and attempt URLs resolve to nothing.
    for (const path of [
      "app/7/delete",
      "app/7/app_keys",
      "app/7/app_key/create",
      "app/7/app_key/2",
      "app/7/app_key/2/delete",
      "app/5/webhook_delivery/9/webhook_delivery_attempts",
      "app/5/webhook_delivery/9/webhook_delivery_attempt/create",
      "app/5/webhook_delivery/9/webhook_delivery_attempt/1",
      "app_installation/7/delete",
      "app_installation/7/accept_permissions",
    ]) {
      expect((await resolve(`/manage/admin_unit/3/${path}`)).name).toBe("not-found");
    }
  });
});
