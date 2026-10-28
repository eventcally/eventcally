<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from "vue";
import { useI18n } from "vue-i18n";

interface Option {
  id: number;
  name: string;
}

const props = defineProps<{
  fetch: (keyword: string) => Promise<Option[]>;
  placeholder?: string;
  disabled?: boolean;
  inputId?: string;
  // Characters needed before a lookup. With 0 (the default) focusing the empty field
  // already lists the suggestions.
  minLength?: number;
}>();
const model = defineModel<Option | null>({ default: null });

const { t } = useI18n();
const input = ref<HTMLInputElement | null>(null);
const text = ref(model.value?.name ?? "");
const options = ref<Option[]>([]);
const active = ref(-1);
const searched = ref(false);
let timer: ReturnType<typeof setTimeout> | undefined;
let request = 0;
// Set when this component changes the model itself, so the watcher leaves the text alone.
let ownChange = false;

const DEBOUNCE_MS = 250;

function setModel(value: Option | null) {
  if (model.value === value) return;
  ownChange = true;
  model.value = value;
}

function reset() {
  clearTimeout(timer);
  request++;
  options.value = [];
  active.value = -1;
  searched.value = false;
}

function canSearch(keyword: string) {
  return keyword.length >= (props.minLength ?? 0);
}

function onInput(event: Event) {
  const keyword = (event.target as HTMLInputElement).value;
  text.value = keyword;
  // Typing invalidates a picked option.
  setModel(null);
  reset();

  if (!canSearch(keyword.trim())) return;
  timer = setTimeout(() => search(keyword.trim()), DEBOUNCE_MS);
}

function onFocus() {
  if (options.value.length || props.disabled) return;
  // A picked option shows its name: list all suggestions, not just that one.
  const keyword = model.value ? "" : text.value.trim();
  if (!canSearch(keyword)) return;
  reset();
  search(keyword);
}

async function search(keyword: string) {
  const current = ++request;
  const result = await props.fetch(keyword);
  // A newer lookup (or a pick) has superseded this one.
  if (current !== request) return;
  options.value = result;
  searched.value = true;
}

function pick(option: Option) {
  reset();
  text.value = option.name;
  setModel(option);
}

function clear() {
  reset();
  text.value = "";
  setModel(null);
  // The button keeps the focus in the field: list the suggestions again.
  if (document.activeElement === input.value) onFocus();
  else input.value?.focus();
}

function onKeydown(event: KeyboardEvent) {
  if (!options.value.length) return;
  if (event.key === "ArrowDown") {
    event.preventDefault();
    active.value = (active.value + 1) % options.value.length;
  } else if (event.key === "ArrowUp") {
    event.preventDefault();
    active.value = (active.value - 1 + options.value.length) % options.value.length;
  } else if (event.key === "Enter" && active.value >= 0) {
    event.preventDefault();
    pick(options.value[active.value]);
  } else if (event.key === "Escape") {
    event.stopPropagation();
    reset();
  }
}

// The parent may set or clear the value (URL navigation, a dependent field).
watch(model, (value) => {
  if (ownChange) {
    ownChange = false;
    return;
  }
  reset();
  text.value = value?.name ?? "";
});

onBeforeUnmount(() => clearTimeout(timer));
</script>

<template>
  <div class="app-typeahead position-relative">
    <div class="input-group">
      <input
        :id="inputId"
        ref="input"
        :value="text"
        type="text"
        class="form-control"
        :placeholder="placeholder"
        :aria-label="placeholder"
        :disabled="disabled"
        autocomplete="off"
        @input="onInput"
        @keydown="onKeydown"
        @focus="onFocus"
        @blur="reset"
      />
      <button
        v-if="text && !disabled"
        type="button"
        class="btn btn-outline-secondary"
        :title="t('Reset')"
        data-test="clear"
        @mousedown.prevent
        @click="clear"
      >
        <i class="fa fa-times"></i>
      </button>
    </div>
    <div
      v-if="options.length"
      class="list-group position-absolute w-100 shadow"
      style="z-index: 1060"
      role="listbox"
    >
      <button
        v-for="(option, index) in options"
        :key="option.id"
        type="button"
        class="list-group-item list-group-item-action"
        :class="{ active: index === active }"
        role="option"
        data-test="option"
        @mousedown.prevent
        @click="pick(option)"
      >
        {{ option.name }}
      </button>
    </div>
    <div v-else-if="searched" class="form-text" data-test="no-results">
      {{ t("No results") }}
    </div>
  </div>
</template>
