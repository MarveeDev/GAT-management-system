const ACCESS_TOKEN_KEY = 'gae_access_token'

/**
 * Access-token storage strategy.
 *
 * The access token is kept in sessionStorage (cleared when the tab closes)
 * rather than localStorage to reduce the window for token theft via XSS and
 * to avoid long-lived persistence across sessions.
 *
 * Never store passwords, refresh tokens, or backend secrets here. Only the
 * short-lived access token issued by the backend is persisted.
 */
export function getAccessToken(): string | null {
  return sessionStorage.getItem(ACCESS_TOKEN_KEY)
}

export function setAccessToken(token: string): void {
  sessionStorage.setItem(ACCESS_TOKEN_KEY, token)
}

export function clearAccessToken(): void {
  sessionStorage.removeItem(ACCESS_TOKEN_KEY)
}
