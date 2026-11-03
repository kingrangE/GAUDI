import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { ADMIN_COOKIE, validAdminSession } from "./adminSession";

export async function requireAdminSession() {
  const jar = await cookies();
  if (!(await validAdminSession(jar.get(ADMIN_COOKIE)?.value, process.env.ADMIN_TOKEN))) {
    redirect("/admin/login");
  }
}
