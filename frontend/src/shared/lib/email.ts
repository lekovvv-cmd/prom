export function normalizeEmail(email: string) {
  return email.trim().toLowerCase();
}

export function isUtmnEmail(email: string) {
  return /^[^\s@]+@utmn\.ru$/.test(normalizeEmail(email));
}
