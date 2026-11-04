<script setup lang="ts">
import { BModal, BTab, BTabs } from "bootstrap-vue-next";
import { useI18n } from "vue-i18n";

// The embed instructions of the widgets page (the old German-only Installation modal).
const props = defineProps<{
  organizationId: number;
  loaderUrl: string;
  iframeUrl: string;
}>();
const show = defineModel<boolean>({ default: false });

const { t } = useI18n();

const headSnippet = () =>
  `<!-- Event calendar widget -->\n<script>(function(w,d,s,o,f,js,fjs){w['EventCallyWidget']=o;w[o]=w[o]||function(){(w[o].q=w[o].q||[]).push(arguments)};js=d.createElement(s),fjs=d.getElementsByTagName(s)[0];js.id=o;js.src=f;js.async=1;fjs.parentNode.insertBefore(js,fjs);}(window,document,'script','eventcally','${props.loaderUrl}'));<\/script>\n<!-- End event calendar widget -->`;

const bodySnippet = () =>
  `<div class="eventcally-widget" data-widget-organization-id="${props.organizationId}" data-widget-width="100%" data-widget-height="400px" data-widget-resize="true" data-widget-google-tag-manager="false"></div>`;

const iframeSnippet = () => `<iframe src="${props.iframeUrl}"></iframe>`;
</script>

<template>
  <BModal v-model="show" :title="t('Installation')" size="lg" centered hide-footer>
    <BTabs content-class="py-3">
      <BTab :title="t('Standard')" active>
        <p>{{ t("Copy the code below and paste it into your website.") }}</p>
        <p>{{ t("Paste the following code into the <head> of the page.") }}</p>
        <textarea
          class="form-control font-monospace"
          style="font-size: 0.7rem"
          disabled
          rows="6"
          data-test="head-snippet"
          :value="headSnippet()"
        ></textarea>
        <p class="mt-3">
          {{
            t(
              "Paste the following code into the <body> of the page where the widget should be displayed.",
            )
          }}
        </p>
        <textarea
          class="form-control font-monospace"
          style="font-size: 0.7rem"
          disabled
          rows="3"
          data-test="body-snippet"
          :value="bodySnippet()"
        ></textarea>
        <p class="mt-3">{{ t("The widget can be configured with the following attributes:") }}</p>
        <ul>
          <li>
            <var>data-widget-organization-id</var>: {{ t("ID of the organization") }}
          </li>
          <li><var>data-widget-width</var>: {{ t("iFrame width (CSS)") }}</li>
          <li><var>data-widget-height</var>: {{ t("iFrame height (CSS)") }}</li>
          <li><var>data-widget-resize</var>: {{ t("Adjust the iFrame size automatically") }}</li>
          <li>
            <var>data-widget-google-tag-manager</var>:
            {{ t("Write events to window.dataLayer for Google Tag Manager.") }}
            <ul>
              <li>
                {{
                  t("Event %(name)s with parameter %(parameter)s", {
                    name: "eventcallyWidget.pageView",
                    parameter: "url",
                  })
                }}
              </li>
              <li>
                {{
                  t("Event %(name)s with parameter %(parameter)s", {
                    name: "eventcallyWidget.linkClick",
                    parameter: "url",
                  })
                }}
              </li>
            </ul>
          </li>
        </ul>
      </BTab>
      <BTab :title="t('Alternative iFrame')">
        <p>
          {{
            t(
              "As an alternative to embedding by script, the widget can be embedded directly as an iFrame.",
            )
          }}
        </p>
        <p>
          {{ t("Copy the code below and paste it into your website.") }}
          {{
            t(
              "Paste the following code into the <body> of the page where the widget should be displayed.",
            )
          }}
        </p>
        <textarea
          class="form-control font-monospace"
          style="font-size: 0.7rem"
          disabled
          data-test="iframe-snippet"
          :value="iframeSnippet()"
        ></textarea>
      </BTab>
    </BTabs>
  </BModal>
</template>
