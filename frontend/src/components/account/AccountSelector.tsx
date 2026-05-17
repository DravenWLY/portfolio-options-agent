import { useEffect } from "react";
import { useUsers } from "../../hooks/useUsers";
import { useAccounts } from "../../hooks/useAccounts";
import { useAccountContext } from "../../context/useAccountContext";
import { type UserRead, type AccountRead } from "../../types/api";

/**
 * AccountSelector — local MVP developer-mode user/account picker.
 *
 * Safety notes:
 * - This is NOT a production authentication surface. No passwords, tokens,
 *   or credentials. The label "dev selector" is intentional.
 * - No localStorage/sessionStorage. Selection is in-memory only.
 * - On user change, the account selection resets automatically.
 */
export default function AccountSelector() {
  const { selectedUser, selectedAccount, setSelectedUser, setSelectedAccount } =
    useAccountContext();

  const { users, status: usersStatus, error: usersError } = useUsers();
  const { accounts, status: accountsStatus, error: accountsError } =
    useAccounts(selectedUser?.id ?? null);

  // Auto-select first user if only one exists
  useEffect(() => {
    if (usersStatus === "success" && users.length === 1 && selectedUser === null) {
      setSelectedUser(users[0]);
    }
  }, [usersStatus, users, selectedUser, setSelectedUser]);

  // Auto-select first account if only one exists
  useEffect(() => {
    if (
      accountsStatus === "success" &&
      accounts.length === 1 &&
      selectedAccount === null
    ) {
      setSelectedAccount(accounts[0]);
    }
  }, [accountsStatus, accounts, selectedAccount, setSelectedAccount]);

  return (
    <div style={styles.wrap} aria-label="Account selector (local dev mode)">
      <span style={styles.devBadge} title="Local MVP mode — not production auth">
        dev
      </span>

      {/* User picker */}
      <UserPicker
        users={users}
        status={usersStatus}
        error={usersError}
        selected={selectedUser}
        onSelect={(u) => setSelectedUser(u)}
      />

      {/* Account picker — only shown when a user is selected */}
      {selectedUser !== null && (
        <>
          <span style={styles.sep} aria-hidden="true">/</span>
          <AccountPicker
            accounts={accounts}
            status={accountsStatus}
            error={accountsError}
            selected={selectedAccount}
            onSelect={(a) => setSelectedAccount(a)}
          />
        </>
      )}
    </div>
  );
}

/* ── User picker ────────────────────────────────────────────────────────── */

function UserPicker({
  users,
  status,
  error,
  selected,
  onSelect,
}: {
  users: UserRead[];
  status: string;
  error: string | null;
  selected: UserRead | null;
  onSelect: (u: UserRead | null) => void;
}) {
  if (status === "loading") {
    return <span style={styles.loading}>loading users…</span>;
  }
  if (status === "error") {
    return (
      <span style={styles.errorText} title={error ?? undefined}>
        ⚠ user load failed
      </span>
    );
  }
  if (users.length === 0) {
    return <span style={styles.empty}>no users found</span>;
  }

  return (
    <select
      style={styles.select}
      aria-label="Select user"
      value={selected?.id ?? ""}
      onChange={(e) => {
        const found = users.find((u) => u.id === e.target.value) ?? null;
        onSelect(found);
      }}
    >
      <option value="" disabled>
        — user —
      </option>
      {users.map((u) => (
        <option key={u.id} value={u.id}>
          {u.display_name}
        </option>
      ))}
    </select>
  );
}

/* ── Account picker ─────────────────────────────────────────────────────── */

function AccountPicker({
  accounts,
  status,
  error,
  selected,
  onSelect,
}: {
  accounts: AccountRead[];
  status: string;
  error: string | null;
  selected: AccountRead | null;
  onSelect: (a: AccountRead | null) => void;
}) {
  if (status === "loading") {
    return <span style={styles.loading}>loading accounts…</span>;
  }
  if (status === "error") {
    return (
      <span style={styles.errorText} title={error ?? undefined}>
        ⚠ account load failed
      </span>
    );
  }
  if (status === "success" && accounts.length === 0) {
    return <span style={styles.empty}>no accounts</span>;
  }

  return (
    <select
      style={styles.select}
      aria-label="Select account"
      value={selected?.id ?? ""}
      onChange={(e) => {
        const found = accounts.find((a) => a.id === e.target.value) ?? null;
        onSelect(found);
      }}
    >
      <option value="" disabled>
        — account —
      </option>
      {accounts.map((a) => (
        <option key={a.id} value={a.id}>
          {a.display_name} ({a.broker_name})
        </option>
      ))}
    </select>
  );
}

/* ── Styles ─────────────────────────────────────────────────────────────── */

const styles: Record<string, React.CSSProperties> = {
  wrap: {
    display: "flex",
    alignItems: "center",
    gap: "var(--space-2)",
  },
  devBadge: {
    fontSize: "var(--font-size-xs)",
    color: "var(--color-text-muted)",
    backgroundColor: "var(--color-surface-2)",
    border: "1px solid var(--color-border)",
    borderRadius: "var(--radius-sm)",
    padding: "1px 6px",
    letterSpacing: "0.08em",
    textTransform: "uppercase",
    cursor: "default",
    userSelect: "none",
  },
  select: {
    backgroundColor: "var(--color-surface-2)",
    color: "var(--color-text-primary)",
    border: "1px solid var(--color-border)",
    borderRadius: "var(--radius-sm)",
    padding: "3px 8px",
    fontSize: "var(--font-size-sm)",
    fontFamily: "var(--font-family)",
    cursor: "pointer",
    outline: "none",
  },
  sep: {
    color: "var(--color-text-muted)",
    fontSize: "var(--font-size-sm)",
  },
  loading: {
    fontSize: "var(--font-size-sm)",
    color: "var(--color-text-muted)",
    fontStyle: "italic",
  },
  errorText: {
    fontSize: "var(--font-size-sm)",
    color: "var(--color-error)",
    cursor: "help",
  },
  empty: {
    fontSize: "var(--font-size-sm)",
    color: "var(--color-text-muted)",
    fontStyle: "italic",
  },
};
