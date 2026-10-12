/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL of the Folderly backend, e.g. http://127.0.0.1:5000 */
  readonly VITE_API_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
