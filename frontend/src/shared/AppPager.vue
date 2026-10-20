<script setup lang="ts">
import { useI18n } from "vue-i18n";

const props = defineProps<{ page: number; pages: number; total: number }>();
const emit = defineEmits<{ "update:page": [page: number] }>();

const { t } = useI18n();

function go(target: number) {
  if (target >= 1 && target <= props.pages && target !== props.page) {
    emit("update:page", target);
  }
}
</script>

<template>
  <!-- Single-bar pager like the Jinja pages: first, previous, "Page x of y", next, last. -->
  <nav :aria-label="t('Page %(page)d of %(pages)d (%(total)d total)', { page, pages, total })">
    <ul class="pagination">
      <li class="page-item" :class="{ disabled: page <= 1 }">
        <button type="button" class="page-link" aria-label="First page" @click="go(1)">
          <i class="fas fa-angle-double-left"></i>
        </button>
      </li>
      <li class="page-item" :class="{ disabled: page <= 1 }">
        <button type="button" class="page-link" aria-label="Previous page" @click="go(page - 1)">
          <i class="fas fa-angle-left"></i>
        </button>
      </li>
      <li class="page-item disabled">
        <span class="page-link">
          {{ t("Page %(page)d of %(pages)d (%(total)d total)", { page, pages, total }) }}
        </span>
      </li>
      <li class="page-item" :class="{ disabled: page >= pages }">
        <button type="button" class="page-link" aria-label="Next page" @click="go(page + 1)">
          <i class="fas fa-angle-right"></i>
        </button>
      </li>
      <li class="page-item" :class="{ disabled: page >= pages }">
        <button type="button" class="page-link" aria-label="Last page" @click="go(pages)">
          <i class="fas fa-angle-double-right"></i>
        </button>
      </li>
    </ul>
  </nav>
</template>
