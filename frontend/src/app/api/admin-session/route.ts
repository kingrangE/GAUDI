import { timingSafeEqual } from "node:crypto";

import { NextResponse, type NextRequest } from "next/server";

import { ADMIN_COOKIE, SESSION_SECONDS, createAdminSession } from "@/lib/adminSession";

export async function POST(request: NextRequest) {
  if (request.headers.get("origin") !== request.nextUrl.origin) {
    return new NextResponse("Forbidden", { status: 403 });
  }
  const form = await request.formData();
  const secret = process.env.ADMIN_TOKEN;
  const input = form.get("token");
  const actual = Buffer.from(typeof input === "string" ? input : "");
  const expected = Buffer.from(secret ?? "");
  const valid = secret && actual.length === expected.length && timingSafeEqual(actual, expected);
  const response = NextResponse.redirect(new URL(valid ? "/admin" : "/admin/login?error=1", request.url), 303);
  if (valid) {
    response.cookies.set(ADMIN_COOKIE, await createAdminSession(secret), {
      httpOnly: true, secure: process.env.NODE_ENV === "production", sameSite: "strict",
      path: "/", maxAge: SESSION_SECONDS,
    });
  }
  return response;
}

export async function DELETE(request: NextRequest) {
  if (request.headers.get("origin") !== request.nextUrl.origin) {
    return new NextResponse("Forbidden", { status: 403 });
  }
  const response = new NextResponse(null, { status: 204 });
  response.cookies.set(ADMIN_COOKIE, "", { httpOnly: true, path: "/", maxAge: 0 });
  return response;
}
