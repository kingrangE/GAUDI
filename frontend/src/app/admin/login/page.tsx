import { Button, Panel } from "@/components/ui";

export default async function AdminLogin({ searchParams }: {
  searchParams: Promise<{ error?: string }>;
}) {
  const { error } = await searchParams;
  return (
    <main className="grid min-h-screen place-items-center bg-paper px-6">
      <Panel className="w-full max-w-md">
        <h1 className="text-xl font-bold">관리자 로그인</h1>
        <form action="/api/admin-session" method="post" className="mt-6 grid gap-4">
          <label htmlFor="admin-token">관리자 비밀번호</label>
          <input id="admin-token" name="token" type="password" required autoComplete="current-password"
            className="rounded border border-line bg-paper p-2" />
          {error && <p role="alert" className="text-bad-600">로그인 정보를 확인해 주세요.</p>}
          <Button type="submit">로그인</Button>
        </form>
      </Panel>
    </main>
  );
}
