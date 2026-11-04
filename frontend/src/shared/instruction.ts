// The markers a translated instruction text carries for its link: they replace the
// `%(search_open)s` / `%(search_close)s` placeholders of the msgid, so no markup is ever
// taken from a translation (see `InstructionText.vue`).
export const LINK_OPEN = "\u0001";
export const LINK_CLOSE = "\u0002";
