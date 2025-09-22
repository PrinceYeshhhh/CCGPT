/// <reference types="vitest/globals" />

declare global {
  interface Window {
    gtag: (command: string, targetId: string, config?: any) => void;
  }

  namespace NodeJS {
    interface Timeout {
      ref(): Timeout;
      unref(): Timeout;
    }
  }

  var global: typeof globalThis;
}

export {};
