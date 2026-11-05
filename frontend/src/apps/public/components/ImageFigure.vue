<script setup lang="ts">
import type { components } from "@/api/schema";

type PublicImage = components["schemas"]["PublicImage"];

// Image with the copyright / licence caption (`render_image`).
defineProps<{ image: PublicImage; imgClass?: string; maxWidth?: string; alt?: string }>();
</script>

<template>
  <figure class="figure mx-auto">
    <img
      :src="image.url"
      :class="['figure-img', 'img-fluid', imgClass]"
      :style="{ maxWidth: maxWidth ?? '100%' }"
      :alt="alt ?? 'image'"
    />
    <figcaption v-if="image.copyright_text || image.license_code" class="figure-caption">
      <template v-if="image.copyright_text">&copy; {{ image.copyright_text }}</template>
      <template v-if="image.license_code">
        {{ " " }}<a :href="image.license_url ?? undefined" target="_blank" rel="noopener noreferrer">{{
          image.license_code
        }}</a>
      </template>
    </figcaption>
  </figure>
</template>
