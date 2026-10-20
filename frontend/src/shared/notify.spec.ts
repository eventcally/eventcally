import { describe, expect, it, vi } from "vitest";

const create = vi.fn();
vi.mock("bootstrap-vue-next", () => ({ useToast: () => ({ create }) }));

import { useNotify } from "./notify";

describe("useNotify", () => {
  it("creates a success toast", () => {
    useNotify().success("Saved");

    expect(create).toHaveBeenCalledWith(
      expect.objectContaining({ body: "Saved", variant: "success", position: "top-end" }),
    );
  });

  it("creates a danger toast", () => {
    useNotify().error("Boom");

    expect(create).toHaveBeenCalledWith(expect.objectContaining({ body: "Boom", variant: "danger" }));
  });
});
