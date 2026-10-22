/// <reference types="vite/client" />

declare module "*.vue" {
  import type { DefineComponent } from "vue";
  const component: DefineComponent<object, object, unknown>;
  export default component;
}

// iframeResizer 4.3.2 is loaded as a global by the Jinja shells (manage + widget).
interface IFrameResizerOptions {
  autoResize?: boolean;
  minHeight?: number | string;
  maxHeight?: number | string;
  scrolling?: boolean | "omit";
  onInit?: (iframe: HTMLIFrameElement) => void;
  onMessage?: (data: { iframe: HTMLIFrameElement; message: unknown }) => void;
}

interface IFrameResizerInstance {
  sendMessage: (message: unknown, targetOrigin?: string) => void;
  resize: () => void;
  removeListeners: () => void;
}

interface HTMLIFrameElement {
  iFrameResizer?: IFrameResizerInstance;
}

interface Window {
  iFrameResize?: (options: IFrameResizerOptions, target: HTMLIFrameElement | string) => unknown[];
  /** Set by the widget shell: the hooks the iframeResizer content window calls. */
  iFrameResizer?: {
    onReady?: () => void;
    onMessage?: (message: { type?: string; data?: unknown }) => void;
  };
  /** Set by the widget shell: settings received before the app mounted. */
  __eventcallyWidget?: {
    settings: Record<string, unknown> | null;
    ready: boolean;
  };
  parentIFrame?: {
    sendMessage: (message: unknown, targetOrigin?: string) => void;
    scrollToOffset: (x: number, y: number) => void;
  };
}
