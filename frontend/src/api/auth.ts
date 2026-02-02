import { api } from "./client";

export const AuthAPI = {
  // Email verification (dj-rest-auth)
  resendVerification: (email: string) =>
    api.post("/api/auth/registration/resend-email/", { email }),

  verifyEmail: (key: string) =>
    api.post("/api/auth/registration/verify-email/", { key }),

  // Password reset (dj-rest-auth)
  requestPasswordReset: (email: string) =>
    api.post("/api/auth/password/reset/", { email }),

  confirmPasswordReset: (payload: {
    uid: string;
    token: string;
    new_password1: string;
    new_password2: string;
  }) =>
    api.post("/api/auth/password/reset/confirm/", payload),
};

// Add these two so imports like { auth } or default imports won’t crash
export const auth = AuthAPI;
export default AuthAPI;
