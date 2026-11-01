// The glue to the embedding page. The Jinja shell buffers what iframeResizer delivers before
// this module has mounted (`window.__eventcallyWidget`) and dispatches window events after it.
import { onBeforeUnmount, onMounted, ref, type Ref } from "vue";

const SETTINGS_EVENT = "eventcally:settings";
const READY_EVENT = "eventcally:ready";
const ANALYTICS_MESSAGE = "EVENTCALLY_ANALYTICS_EVENT";

/** The settings of the widget; `null` until the embedding page has sent them. */
export function useWidgetSettings<T extends object>(): Ref<T | null> {
  const settings = ref(null) as Ref<T | null>;
  const buffered = window.__eventcallyWidget?.settings;
  if (buffered) settings.value = { ...buffered } as T;

  // The first message creates the settings, later ones update them key by key.
  const onSettings = (event: Event) => {
    const data = (event as CustomEvent).detail as Partial<T> | undefined;
    settings.value = { ...(settings.value ?? {}), ...data } as T;
  };
  window.addEventListener(SETTINGS_EVENT, onSettings);
  onBeforeUnmount(() => window.removeEventListener(SETTINGS_EVENT, onSettings));

  return settings;
}

export function trackAnalytics(data: { event: string; url: string }): void {
  if (window.parentIFrame) {
    window.parentIFrame.sendMessage({ type: ANALYTICS_MESSAGE, data });
  }
}

export function scrollToTop(): void {
  window.scrollTo(0, 0);
  window.parentIFrame?.scrollToOffset(0, 0);
}

/**
 * Reports one `pageView` once the page is mounted and iframeResizer is ready. `href` says which
 * URL it is: the iframe page reports the URL it was loaded with, before the router tidied it.
 */
export function usePageViewTracking(href: () => string = () => document.location.href): void {
  let sent = false;
  const report = () => {
    if (sent || !window.__eventcallyWidget?.ready) return;
    sent = true;
    trackAnalytics({ event: "pageView", url: href() });
  };

  onMounted(() => {
    report();
    window.addEventListener(READY_EVENT, report);
  });
  onBeforeUnmount(() => window.removeEventListener(READY_EVENT, report));
}
