import { BarChart3, ClipboardList, FileStack, LayoutDashboard, Settings } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import { AdminToolbar } from "./AdminToolbar";
import styles from "./AdminShell.module.css";

type AdminSection = "dashboard" | "problem-sets" | "sessions" | "results" | "settings";

type AdminShellProps = {
  active: AdminSection;
  eyebrow: string;
  title: string;
  children: ReactNode;
};

const navItems = [
  { key: "dashboard", label: "대시보드", href: "/admin", icon: LayoutDashboard },
  { key: "problem-sets", label: "문제 세트", href: "/admin/problem-sets", icon: FileStack },
  { key: "sessions", label: "평가 세션", href: "/admin/sessions", icon: ClipboardList },
  { key: "results", label: "결과 리포트", href: "/admin/results", icon: BarChart3 },
  { key: "settings", label: "권한/설정", href: "/admin", icon: Settings },
] satisfies Array<{
  key: AdminSection;
  label: string;
  href: string;
  icon: typeof LayoutDashboard;
}>;

export function AdminShell({ active, eyebrow, title, children }: AdminShellProps) {
  return (
    <main className={styles.shell}>
      <aside className={styles.sidebar} aria-label="관리자 메뉴">
        <div className={styles.brand}>
          <div className={styles.brandMark}>A</div>
          <div>
            <strong>and-you</strong>
            <span>Evaluation Admin</span>
          </div>
        </div>

        <nav className={styles.navList}>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                className={item.key === active ? styles.navItemActive : styles.navItem}
                href={item.href}
                key={item.key}
              >
                <Icon aria-hidden="true" size={18} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </aside>

      <section className={styles.workspace}>
        <header className={styles.topbar}>
          <div>
            <p className={styles.eyebrow}>{eyebrow}</p>
            <h1>{title}</h1>
          </div>
          <AdminToolbar />
        </header>

        {children}
      </section>
    </main>
  );
}
