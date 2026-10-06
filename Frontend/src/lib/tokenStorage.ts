const ACCESS_TOKEN_KEY = 'gat_access_token'
const LEGACY_ACCESS_TOKEN_KEY = 'gae_access_token'

/**
 * Access-token storage strategy.
 *
 * The access token is kept in sessionStorage (cleared when the tab closes)
 * rather than localStorage to reduce the window for token theft via XSS and
 * to avoid long-lived persistence across sessions.
 *
 * Never store passwords, refresh tokens, or backend secrets here. Only the
 * short-lived access token issued by the backend is persisted.
 *
 * A one-time migration reads the previous `gae_access_token` key (legacy
 * branding) and transparently moves it to the current key so existing
 * sessions are not invalidated.
 */
export function getAccessToken(): string | null {
  const current = sessionStorage.getItem(ACCESS_TOKEN_KEY)
  if (current !== null) return current

  const legacy = sessionStorage.getItem(LEGACY_ACCESS_TOKEN_KEY)
  if (legacy !== null) {
    sessionStorage.setItem(ACCESS_TOKEN_KEY, legacy)
    sessionStorage.removeItem(LEGACY_ACCESS_TOKEN_KEY)
    return legacy
  }

  return null
}

export function setAccessToken(token: string): void {
  sessionStorage.setItem(ACCESS_TOKEN_KEY, token)
  sessionStorage.removeItem(LEGACY_ACCESS_TOKEN_KEY)
}

export function clearAccessToken(): void {
  sessionStorage.removeItem(ACCESS_TOKEN_KEY)
  sessionStorage.removeItem(LEGACY_ACCESS_TOKEN_KEY)
}
