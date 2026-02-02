// src/auth/logout.ts
import { clearTokens } from "./tokenStore";

export function logout() {
  clearTokens();
}
