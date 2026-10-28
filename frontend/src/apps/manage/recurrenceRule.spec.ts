import { describe, expect, it } from "vitest";
import {
  defaultRecurrence,
  describe as describeRule,
  parse,
  serialize,
  type RecurrenceValue,
} from "./recurrenceRule";

// Rules the legacy widget wrote (tests, seeder, e2e and hand-made legacy output).
const LEGACY_RULES = [
  "RRULE:FREQ=DAILY",
  "RRULE:FREQ=DAILY;COUNT=7",
  "RRULE:FREQ=DAILY;INTERVAL=2;COUNT=100",
  "RRULE:FREQ=DAILY;COUNT=10\nEXDATE:20300102T000000,20300104T000000\nRDATE:20300103T000000,20300105T000000",
  "RRULE:FREQ=DAILY;COUNT=12\nEXDATE:20301231T000000",
  "RRULE:FREQ=WEEKLY;BYDAY=MO,WE;COUNT=6",
  "RRULE:FREQ=WEEKLY;BYDAY=WE;UNTIL=20211231T000000",
  "RRULE:FREQ=WEEKLY;BYDAY=MO,WE;UNTIL=20301231T000000\nEXDATE:20301201T000000",
  "RRULE:FREQ=WEEKLY;INTERVAL=3;BYDAY=SU,MO,SA",
  "RRULE:FREQ=MONTHLY;BYMONTHDAY=15;COUNT=3",
  "RRULE:FREQ=MONTHLY;INTERVAL=2;BYDAY=-1FR",
  "RRULE:FREQ=MONTHLY",
  "RRULE:FREQ=YEARLY;BYMONTH=10;BYMONTHDAY=3",
  "RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=+2SU;UNTIL=20351231T000000",
];

const t = (key: string, named?: Record<string, unknown>) =>
  key.replace(/%\((\w+)\)s/g, (_m, name: string) => String(named?.[name]));

describe("recurrenceRule", () => {
  it.each(LEGACY_RULES)("round-trips %s", (rule) => {
    const value = parse(rule);

    expect(value).not.toBeNull();
    expect(serialize(value!)).toBe(rule);
  });

  it("accepts CRLF and surrounding whitespace", () => {
    expect(serialize(parse("RRULE:FREQ=WEEKLY;COUNT=5\r\nEXDATE:20260504T000000\n")!)).toBe(
      "RRULE:FREQ=WEEKLY;COUNT=5\nEXDATE:20260504T000000",
    );
  });

  it.each([
    "",
    "FREQ=DAILY",
    "RRULE:FREQ=NOPE",
    "RRULE:FREQ=DAILY;COUNT=7bad",
    "RRULE:FREQ=DAILY;COUNT=0",
    "RRULE:FREQ=DAILY;INTERVAL=x",
    "RRULE:FREQ=DAILY;COUNT",
    "RRULE:FREQ=DAILY;COUNT=1=2",
    "RRULE:FREQ=DAILY;COUNT=2;COUNT=3",
    "RRULE:FREQ=DAILY;UNTIL=20190310T010000Z",
    "RRULE:FREQ=DAILY;UNTIL=2019",
    "RRULE:FREQ=DAILY;BYDAY=MO",
    "RRULE:FREQ=WEEKLY;BYDAY=XX",
    "RRULE:FREQ=MONTHLY;BYMONTHDAY=32",
    "RRULE:FREQ=MONTHLY;BYDAY=+5MO",
    "RRULE:FREQ=MONTHLY;BYDAY=+1XX",
    "RRULE:FREQ=YEARLY;BYMONTH=13;BYMONTHDAY=1",
    "RRULE:FREQ=YEARLY;BYMONTH=3",
    // Not in the legacy order: kept raw rather than rewritten.
    "RRULE:FREQ=YEARLY;BYDAY=-1SU;BYMONTH=10",
    "RRULE:FREQ=WEEKLY;BYDAY=WE,MO",
    "RRULE:FREQ=WEEKLY;COUNT=5\nEXDATE:20260504",
    "RRULE:FREQ=WEEKLY;COUNT=5\nFOO:20260504T000000",
    "RRULE:FREQ=WEEKLY;COUNT=5\nEXDATE:20260505T000000,20260504T000000",
  ])("does not parse %j", (rule) => {
    expect(parse(rule)).toBeNull();
  });

  it("builds defaults from the start date", () => {
    // 2030-12-31 is a Tuesday.
    expect(defaultRecurrence("WEEKLY", "2030-12-31")).toMatchObject({
      freq: "WEEKLY",
      interval: 1,
      weekdays: ["TU"],
      monthlyType: null,
      end: { type: "until", until: "2030-12-31" },
    });
    expect(defaultRecurrence("YEARLY", "2030-12-31")).toMatchObject({
      monthlyType: "DAYOFMONTH",
      monthDay: 31,
      month: 12,
      weekday: "TU",
    });
    expect(serialize(defaultRecurrence("MONTHLY", "2030-12-31"))).toBe(
      "RRULE:FREQ=MONTHLY;BYMONTHDAY=31;UNTIL=20301231T000000",
    );
  });

  it("sorts EXDATE and RDATE values and leaves out empty lists", () => {
    const value: RecurrenceValue = {
      ...defaultRecurrence("DAILY", "2030-01-01"),
      end: { type: "count", count: 3 },
      exdates: ["20300103T000000", "20300102T000000"],
      rdates: [],
    };

    expect(serialize(value)).toBe(
      "RRULE:FREQ=DAILY;COUNT=3\nEXDATE:20300102T000000,20300103T000000",
    );
  });

  it.each([
    ["RRULE:FREQ=DAILY;INTERVAL=2;COUNT=7", "Every 2 day(s), ends after 7 occurrence(s)"],
    ["RRULE:FREQ=WEEKLY;BYDAY=MO,WE;COUNT=6", "Every 1 week(s), on Monday, Wednesday, ends after 6 occurrence(s)"],
    ["RRULE:FREQ=MONTHLY;BYMONTHDAY=15", "Every 1 month(s), on day 15"],
    ["RRULE:FREQ=MONTHLY;BYDAY=-1FR", "Every 1 month(s), on the last Friday"],
    ["RRULE:FREQ=YEARLY;BYMONTH=10;BYMONTHDAY=3", "Every 1 year(s), on 3 October"],
    [
      "RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=+2SU;UNTIL=20351231T000000",
      "Every 1 year(s), on the second Sunday of October, until Dec 31, 2035",
    ],
    [
      "RRULE:FREQ=DAILY;COUNT=10\nEXDATE:20300102T000000\nRDATE:20300103T000000",
      "Every 1 day(s), ends after 10 occurrence(s), including Jan 3, 2030, except Jan 2, 2030",
    ],
    ["RRULE:FREQ=WEEKLY", "Every 1 week(s)"],
  ])("describes %j", (rule, text) => {
    expect(describeRule(parse(rule)!, t, "en-US")).toBe(text);
  });
});
