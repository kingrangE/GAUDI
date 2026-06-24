import { AdminShell } from "@/components/admin/AdminShell";
import { SessionsPanel } from "@/components/admin/SessionsPanel";

export const dynamic = "force-dynamic";

export default function SessionsPage() {
  return (
    <AdminShell active="sessions" eyebrow="평가 운영" title="평가 세션">
      <SessionsPanel />
    </AdminShell>
  );
}
