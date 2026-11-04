import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";
import { defineComponent } from "vue";

const success = vi.hoisted(() => vi.fn());
vi.mock("@/shared/notify", () => ({ useNotify: () => ({ success, error: vi.fn() }) }));

import { useConfirmAction } from "./useConfirmAction";

const call = vi.fn();
const onDone = vi.fn();

function setup() {
  let result!: ReturnType<typeof useConfirmAction<{ id: number }>>;
  mount(
    defineComponent({
      setup() {
        result = useConfirmAction<{ id: number }>({ call, onDone });
        return () => null;
      },
    }),
    { global: { plugins: [createI18n({ legacy: false, locale: "en", messages: { en: {} } })] } },
  );
  return result;
}

describe("useConfirmAction", () => {
  beforeEach(() => [call, onDone, success].forEach((f) => f.mockReset()));

  it("opens for an item, runs the call, notifies, closes and reloads", async () => {
    call.mockResolvedValue({ data: { message: "Deleted" }, response: { ok: true } });
    const action = setup();

    action.open({ id: 4 });
    expect(action.show.value).toBe(true);
    await action.submit("Rathaus");
    await flushPromises();

    expect(call).toHaveBeenCalledWith({ id: 4 }, "Rathaus");
    expect(success).toHaveBeenCalledWith("Deleted");
    expect(action.show.value).toBe(false);
    expect(onDone).toHaveBeenCalledOnce();
  });

  it("closes without a toast when the answer has no message", async () => {
    call.mockResolvedValue({});
    const action = setup();

    action.open({ id: 4 });
    await action.submit();

    expect(success).not.toHaveBeenCalled();
    expect(action.show.value).toBe(false);
  });

  it("shows a 422 on the name field inside the modal", async () => {
    call.mockResolvedValue({
      error: { errors: [{ loc: ["name"], msg: "No match" }, { loc: ["x"], msg: "Other" }] },
      response: { ok: false },
    });
    const action = setup();

    action.open({ id: 4 });
    await action.submit("x");

    expect(action.nameError.value).toBe("No match");
    expect(action.error.value).toBe("Other");
    expect(action.show.value).toBe(true);
    expect(onDone).not.toHaveBeenCalled();
  });

  it("shows any other error and ignores a second submit while busy or without item", async () => {
    let resolve!: (v: unknown) => void;
    call.mockReturnValue(new Promise((r) => (resolve = r)));
    const action = setup();

    await action.submit();
    expect(call).not.toHaveBeenCalled();

    action.open({ id: 4 });
    const first = action.submit();
    await action.submit();
    expect(call).toHaveBeenCalledOnce();
    resolve({ error: { message: "Kaputt" }, response: { ok: false } });
    await first;

    expect(action.error.value).toBe("Kaputt");
    expect(action.busy.value).toBe(false);
  });
});
