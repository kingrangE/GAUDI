import { NextResponse, type NextRequest } from "next/server";

import { ADMIN_COOKIE, validAdminSession } from "./lib/adminSession";

export async function middleware(request: NextRequest) {
  if (request.nextUrl.pathname === "/admin/login") return NextResponse.next();
  if (await validAdminSession(request.cookies.get(ADMIN_COOKIE)?.value, process.env.ADMIN_TOKEN)) {
    return NextResponse.next();
  }
  return NextResponse.redirect(new URL("/admin/login", request.url));
}

export const config = { matcher: ["/admin/:path*"] };
