type RuntimeConfig = {
  apiBaseUrl?: string;
  staticBaseUrl?: string;
  backendOrigin?: string;
};

declare global {
  interface Window {
    __TRUEVISION_CONFIG__?: RuntimeConfig;
  }
}

const runtimeConfig =
  typeof window !== 'undefined' ? window.__TRUEVISION_CONFIG__ ?? {} : {};

const browserOrigin =
  typeof window !== 'undefined' ? window.location.origin : 'http://localhost:4200';

const defaultBackendOrigin =
  browserOrigin.includes(':4200') ? 'http://localhost:5000' : browserOrigin;

const backendOrigin = runtimeConfig.backendOrigin ?? defaultBackendOrigin;

export const API_BASE_URL = runtimeConfig.apiBaseUrl ?? `${backendOrigin}/api`;
export const STATIC_BASE_URL =
  runtimeConfig.staticBaseUrl ?? `${backendOrigin}/static`;
