const mockUsers = [
  { id: 1, name: "Alice Carter", email: "alice@example.com", role: "customer", status: "active" },
  { id: 2, name: "Ben Ortiz", email: "ben@example.com", role: "customer", status: "active" },
  { id: 3, name: "Clara Singh", email: "clara@example.com", role: "admin", status: "active" },
];

export function UserManagementTable() {
  return (
    <section className="rounded-2xl bg-white p-6 shadow-md">
      <header className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold text-brand-primary">User management</h2>
        <button className="rounded-md border border-brand-accent px-4 py-2 text-xs font-semibold text-brand-accent hover:bg-emerald-50">
          Invite user
        </button>
      </header>
      <div className="mt-4 overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-brand-muted">Name</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-brand-muted">Email</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-brand-muted">Role</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-brand-muted">Status</th>
              <th className="px-3 py-2 text-right text-xs font-semibold uppercase tracking-wide text-brand-muted">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {mockUsers.map((user) => (
              <tr key={user.id}>
                <td className="px-3 py-2 font-medium text-brand-primary">{user.name}</td>
                <td className="px-3 py-2">{user.email}</td>
                <td className="px-3 py-2 uppercase">{user.role}</td>
                <td className="px-3 py-2 capitalize">{user.status}</td>
                <td className="px-3 py-2 text-right">
                  <button className="rounded-md border border-slate-200 px-3 py-1 text-xs font-semibold text-brand-primary hover:border-brand-accent">
                    Disable
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
