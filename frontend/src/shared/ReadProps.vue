<script setup lang="ts">
// The `ReadDisplay` of a read page as a definition list.
export interface ReadRow {
  label: string;
  value?: string | number | null;
  href?: string;
  list?: string[];
  hideWhenEmpty?: boolean;
}

const props = defineProps<{ rows: ReadRow[] }>();

const empty = (row: ReadRow) =>
  (row.value === undefined || row.value === null || row.value === "") && !row.list?.length;
const visible = () => props.rows.filter((row) => !(row.hideWhenEmpty && empty(row)));
</script>

<template>
  <dl class="row">
    <template v-for="row in visible()" :key="row.label">
      <dt class="col-sm-3">{{ row.label }}</dt>
      <dd class="col-sm-9">
        <ul v-if="row.list?.length" class="list-unstyled mb-0">
          <li v-for="entry in row.list" :key="entry">{{ entry }}</li>
        </ul>
        <a v-else-if="row.href && !empty(row)" :href="row.href">{{ row.value }}</a>
        <template v-else>{{ row.value }}</template>
      </dd>
    </template>
  </dl>
</template>
