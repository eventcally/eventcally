// Flask CLI wrappers used to build test fixtures.
//
// Ported from cypress/support/commands.js:1-183. Unlike the Cypress commands
// these are plain synchronous functions returning the id directly -- no promise
// chain -- and they pass argv arrays instead of hand-quoted shell strings.
//
// Commands go to the long-lived fixture server (.scripts/e2e_fixture_server.py)
// rather than a fresh `flask` process. Importing the app costs ~3.8s and the
// suite makes ~464 fixture calls, which was ~37 of its ~40 minutes; the server
// pays that import once. It runs the same CLI commands, so behaviour is
// unchanged -- only the transport differs.
const { spawn, execFileSync } = require("child_process");
const crypto = require("crypto");
const path = require("path");

const PORT = Number(process.env.E2E_FIXTURE_PORT || 5099);
const BASE = `http://127.0.0.1:${PORT}/`;
const SERVER = path.join(__dirname, "..", "..", ".scripts", "e2e_fixture_server.py");
const READY_TIMEOUT_MS = 40000;

let started = false;

/** Fingerprint of the database this process expects, without its credentials. */
function expectedFingerprint() {
  return crypto
    .createHash("sha256")
    .update(process.env.DATABASE_URL || "")
    .digest("hex")
    .slice(0, 12);
}

/** @returns {{ok: boolean, database: string}|null} null when nothing answers. */
function health() {
  try {
    return JSON.parse(
      execFileSync("curl", ["-sS", "--fail", "-m", "2", `${BASE}health`], {
        encoding: "utf8",
        stdio: ["ignore", "pipe", "pipe"],
      })
    );
  } catch (error) {
    return null;
  }
}

function ensureServer() {
  if (started) return;

  // Reuse a server that is already up -- but only if it is attached to the same
  // database. Every fixture command truncates every table, so silently talking to
  // a server left over from another run would wipe the wrong database.
  const expected = expectedFingerprint();
  const existing = health();

  if (existing) {
    if (existing.database !== expected) {
      throw new Error(
        `A fixture server is already running on port ${PORT}, but it is attached to a ` +
          `different database (${existing.database}, expected ${expected}).\n` +
          `Stop it, or set E2E_FIXTURE_PORT to use another port.`
      );
    }
    started = true;
    return;
  }

  const child = spawn("python", [SERVER, "--port", String(PORT)], {
    stdio: ["ignore", "inherit", "inherit"],
  });
  const stop = () => child.kill();
  process.on("exit", stop);
  process.on("SIGINT", stop);
  process.on("SIGTERM", stop);

  const deadline = Date.now() + READY_TIMEOUT_MS;
  while (Date.now() < deadline) {
    if (child.exitCode !== null) {
      throw new Error(`Fixture server exited with code ${child.exitCode} before becoming ready`);
    }

    const status = health();
    if (status) {
      if (status.database !== expected) {
        throw new Error(
          `Fixture server is attached to the wrong database ` +
            `(${status.database}, expected ${expected})`
        );
      }
      started = true;
      return;
    }

    execFileSync("sleep", ["0.25"]);
  }

  child.kill();
  throw new Error(`Fixture server did not become ready within ${READY_TIMEOUT_MS}ms`);
}

/**
 * Run `flask <args>` and return its stdout.
 *
 * @param {string[]} args
 * @returns {string}
 */
function run(args) {
  ensureServer();

  let raw;
  try {
    raw = execFileSync(
      "curl",
      ["-sS", "--fail", "-X", "POST", "--data-binary", JSON.stringify({ args }), BASE],
      { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] }
    );
  } catch (error) {
    throw new Error(
      `Could not reach the fixture server for "flask ${args.join(" ")}".\n` +
        `It may have exited; check the output above.\n${error.message}`
    );
  }

  const result = JSON.parse(raw);

  if (!result.ok) {
    // SOURCE: cypress/support/commands.js:1-12 (error message format)
    throw new Error(`Execution of "flask ${args.join(" ")}" failed
          Exit code: ${result.exit_code}
          Stdout:\n${result.output || ""}
          Stderr:\n${result.error}`);
  }

  return result.output;
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
