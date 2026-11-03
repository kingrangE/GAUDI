export const ADMIN_COOKIE = "gaudi-admin";
export const SESSION_SECONDS = 8 * 60 * 60;

async function key(secret: string) {
  return crypto.subtle.importKey(
    "raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" }, false,
    ["sign", "verify"],
  );
}

export async function createAdminSession(secret: string, now = Date.now()): Promise<string> {
  const expires = String(Math.floor(now / 1000) + SESSION_SECONDS);
  const signature = await crypto.subtle.sign("HMAC", await key(secret), new TextEncoder().encode(expires));
  const hex = Array.from(new Uint8Array(signature), (b) => b.toString(16).padStart(2, "0")).join("");
  return `${expires}.${hex}`;
}

export async function validAdminSession(value: string | undefined, secret: string | undefined,
                                        now = Date.now()): Promise<boolean> {
  if (!secret || !value) return false;
  const match = /^(\d+)\.([a-f0-9]{64})$/.exec(value);
  if (!match || Number(match[1]) <= now / 1000) return false;
  const signature = Uint8Array.from(match[2].match(/../g)!, (v) => parseInt(v, 16));
  return crypto.subtle.verify("HMAC", await key(secret), signature, new TextEncoder().encode(match[1]));
}
