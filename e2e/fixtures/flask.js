// Flask CLI wrappers used to build test fixtures.
//
// Ported from cypress/support/commands.js:1-183. Unlike the Cypress commands
// these are plain synchronous functions returning the id directly — no promise
// chain — and they pass argv arrays instead of hand-quoted shell strings.
const { execFileSync } = require("child_process");

/**
 * Run `flask <args>` and return its stdout.
 *
 * @param {string[]} args
 * @returns {string}
 */
function run(args) {
  try {
    return execFileSync("flask", args, { encoding: "utf8" });
  } catch (error) {
    // SOURCE: cypress/support/commands.js:1-12 (error message format)
    throw new Error(`Execution of "flask ${args.join(" ")}" failed
          Exit code: ${error.status}
          Stdout:\n${error.stdout || ""}
          Stderr:\n${error.stderr || error.message}`);
  }
}

/**
 * Run `flask <args>` and parse its stdout as JSON.
 *
 * @param {string[]} args
 * @returns {any}
 */
function runJson(args) {
  const stdout = run(args);

  try {
    return JSON.parse(stdout);
  } catch (error) {
    throw new Error(`Output of "flask ${args.join(" ")}" is not valid JSON
          Stdout:\n${stdout}`);
  }
}

function resetAndSeed() {
  run(["test", "reset", "--seed"]);
}

function createUser(email = "test@test.de", password = "password", admin = false) {
  const args = ["user", "create", email, password, "--confirm", "--accept-tos"];

  if (admin) {
    args.push("--admin");
  }

  return runJson(args).user_id;
}

function createAdminUnit(userEmail = "test@test.de", name = "Meine Crew", verified = true) {
  return runJson([
    "test",
    "admin-unit-create",
    userEmail,
    name,
    verified ? "--verified" : "--no-verified",
  ]).admin_unit_id;
}

function createAdminUnitMemberInvitation(adminUnitId, userEmail = "new@test.de") {
  return runJson([
    "test",
    "admin-unit-member-invitation-create",
    String(adminUnitId),
    userEmail,
  ]).invitation_id;
}

function createAdminUnitMember(adminUnitId, userEmail = "new@test.de") {
  return runJson(["test", "admin-unit-member-create", String(adminUnitId), userEmail]).member_id;
}

function createEvent(adminUnitId) {
  return runJson(["test", "event-create", String(adminUnitId)]).event_id;
}

function createEventPlace(adminUnitId, name = "Mein Platz") {
  return runJson(["test", "event-place-create", String(adminUnitId), name]).event_place_id;
}

function createEventOrganizer(adminUnitId, name = "Mein Veranstalter") {
  return runJson(["test", "event-organizer-create", String(adminUnitId), name])
    .event_organizer_id;
}

function createOauth2Client(userId) {
  return runJson(["test", "oauth2-client-create", String(userId)]);
}

function createIncomingVerificationRequest(adminUnitId) {
  return runJson(["test", "verification-request-create-incoming", String(adminUnitId)])
    .verification_request_id;
}

function createIncomingReferenceRequest(adminUnitId) {
  return runJson(["test", "reference-request-create-incoming", String(adminUnitId)])
    .reference_request_id;
}

function createIncomingReference(adminUnitId) {
  return runJson(["test", "reference-create-incoming", String(adminUnitId)]).reference_id;
}

function createAdminUnitRelation(adminUnitId) {
  return runJson(["test", "admin-unit-relation-create", String(adminUnitId)]).relation_id;
}

function createAdminUnitOrganizationInvitation(adminUnitId, email = "invited@test.de") {
  return runJson([
    "test",
    "admin-unit-organization-invitation-create",
    String(adminUnitId),
    email,
  ]).invitation_id;
}

function createEventList(adminUnitId) {
  return runJson(["test", "event-list-create", String(adminUnitId)]).event_list_id;
}

module.exports = {
  run,
  runJson,
  resetAndSeed,
  createUser,
  createAdminUnit,
  createAdminUnitMemberInvitation,
  createAdminUnitMember,
  createEvent,
  createEventPlace,
  createEventOrganizer,
  createOauth2Client,
  createIncomingVerificationRequest,
  createIncomingReferenceRequest,
  createIncomingReference,
  createAdminUnitRelation,
  createAdminUnitOrganizationInvitation,
  createEventList,
};
