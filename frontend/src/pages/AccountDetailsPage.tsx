import { Fragment, useCallback, useEffect, useId, useRef, useState, type CSSProperties, type MutableRefObject, type ReactNode } from "react";
import { Badge, DemoChip, MpIcon, PageHeader, SafetyStrip, type MpTone } from "../components/shared/mp";
import { LoadingSkeleton, ErrorState, EmptyState } from "../components/shared/StateViews";
import { useAccountContext } from "../context/useAccountContext";
import { accountDetailsApi } from "../api/accountDetails";
import { ApiRequestError } from "../api/client";
import type {
  AccountDetailsRead,
  AccountDetailAccountRead,
  AccountDetailsSyncStatus,
  SelectedAccountDetailsRead,
  AccountCashDisplayRowRead,
  AccountEquityPositionDisplayRowRead,
  AccountOptionPositionDisplayRowRead,
  AccountTaxLotDisplayRowRead,
  AccountTaxLotPaginationRead,
  AccountDetailsReadinessCaveatRead,
  ReviewAccountCandidateRead,
  AccountScopeRole,
} from "../types/accountDetails";
import type { ReadinessSnapshotStatus } from "../types/portfolioContext";

/**
 * AccountDetailsPage — private Account Details workspace (P27A-T5).
 *
 * Backend-backed via the reviewed P27A-T1 contract:
 *   GET /api/users/{uid}/account-details  →  AccountDetailsRead
 *
 * Helps a user understand connected accounts, snapshot freshness, high-level
 * exposure labels, and the portfolio/review scope used for portfolio-aware
 * review. It is NOT broker management: no raw private identifiers,
 * performance surface, or broker-action controls.
 *
 * Safety:
 *   - Every account label renders verbatim from the backend; the frontend
 *     never invents or computes financial values.
 *   - Privacy: when an account's privacy_display_mode is "amounts_hidden",
 *     monetary labels are omitted (never replaced with invented values); only
 *     qualitative cash state, position counts, freshness, and scope remain.
 *   - No localStorage/sessionStorage, no provider/SnapTrade call, no LLM/agent
 *     use, and no trading-action wording. Failures stay local to the page.
 */

type LoadStatus = "idle" | "loading" | "success" | "error";
type DetailLoadStatus = LoadStatus;

/**
 * Selected-account sync (P27B-T19) — local UI state for the opaque
 * Account Details refresh bridge:
 *   - "idle":   no sync requested yet (the button is offered as-is)
 *   - "syncing": POST in flight
 *   - "succeeded" / "partially_succeeded" / "failed": last finished status
 *   - "running": backend reported 409 (a sync is already in progress)
 *   - "error":  network/parse error outside the sanitized status set
 * The frontend never invents the status text; the backend message is shown
 * verbatim, with a quiet local fallback for the network/conflict cases.
 */
type SyncUiStatus = "idle" | "syncing" | AccountDetailsSyncStatus | "error";

interface SyncUiState {
  status: SyncUiStatus;
  message: string | null;
}

const INITIAL_SYNC_STATE: SyncUiState = { status: "idle", message: null };

interface LoadOptions {
  quiet?: boolean;
}

function errMsg(err: unknown): string {
  if (err instanceof ApiRequestError) return err.detail;
  if (err instanceof Error) return err.message;
  return "Request failed.";
}

function restoreScrollPositionIfNeeded(scrollRef: MutableRefObject<number | null>) {
  const y = scrollRef.current;
  if (y == null) return;
  scrollRef.current = null;
  window.requestAnimationFrame(() => window.scrollTo({ top: y, left: window.scrollX, behavior: "auto" }));
}

function dataModeBadge(mode: AccountDetailsRead["data_mode"]): { tone: MpTone; label: string; title: string } | null {
  switch (mode) {
    case "private_real_source":
      return { tone: "info", label: "Private source", title: "Private real-source account details" };
    case "unavailable":
      return { tone: "mute", label: "Unavailable", title: "Account details unavailable" };
    case "synthetic_demo":
      return null; // shown via DemoChip instead
    default:
      return { tone: "mute", label: mode, title: mode };
  }
}

function freshnessTone(status: ReadinessSnapshotStatus): MpTone {
  switch (status) {
    case "fresh": return "live";
    case "manual_review": return "stale";
    case "stale": return "block";
    case "unknown":
    case "unavailable": return "mute";
    default: return "mute";
  }
}

function scopeRoleMeta(role: AccountScopeRole): { label: string; tone: MpTone } {
  switch (role) {
    case "review_account": return { label: "Review account", tone: "accent" };
    case "included_in_scope": return { label: "In scope", tone: "live" };
    case "excluded_from_scope": return { label: "Excluded", tone: "mute" };
    default: return { label: role, tone: "mute" };
  }
}

export default function AccountDetailsPage() {
  const { selectedUser } = useAccountContext();
  const userId = selectedUser?.id ?? null;

  const [status, setStatus] = useState<LoadStatus>("idle");
  const [data, setData] = useState<AccountDetailsRead | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedAccountRef, setSelectedAccountRef] = useState<string | null>(null);
  const [detailStatus, setDetailStatus] = useState<DetailLoadStatus>("idle");
  const [selectedDetail, setSelectedDetail] = useState<SelectedAccountDetailsRead | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [detailReloadKey, setDetailReloadKey] = useState(0);
  const [syncState, setSyncState] = useState<SyncUiState>(INITIAL_SYNC_STATE);
  const selectedDetailRef = useRef<SelectedAccountDetailsRead | null>(null);
  const selectedAccountRefRef = useRef<string | null>(null);
  const detailAccountRef = useRef<string | null>(null);
  const restoreScrollYRef = useRef<number | null>(null);

  const load = useCallback((uid: string, options: LoadOptions = {}) => {
    if (!options.quiet) setStatus("loading");
    setError(null);
    return accountDetailsApi
      .get(uid)
      .then((res) => { setData(res); setStatus("success"); })
      .catch((err) => {
        if (!options.quiet) {
          setError(errMsg(err));
          setStatus("error");
        }
      });
  }, []);

  useEffect(() => {
    if (userId) load(userId);
  }, [userId, load]);

  useEffect(() => {
    if (status !== "success" || !data) return;
    if (data.accounts.length === 0) {
      setSelectedAccountRef(null);
      return;
    }
    const selectedStillExists = selectedAccountRef
      ? data.accounts.some((acc) => acc.account_reference === selectedAccountRef)
      : false;
    if (selectedStillExists) return;
    const defaultAccount =
      data.accounts.find((acc) => acc.scope_roles.includes("included_in_scope")) ??
      data.accounts.find((acc) => acc.scope_roles.includes("review_account")) ??
      data.accounts[0];
    setSelectedAccountRef(defaultAccount.account_reference);
  }, [data, selectedAccountRef, status]);

  // Reset the sync UI state when the selected account changes so a prior
  // refresh's outcome never carries over to a different account.
  useEffect(() => {
    selectedAccountRefRef.current = selectedAccountRef;
    setSyncState(INITIAL_SYNC_STATE);
  }, [selectedAccountRef]);

  const refreshSelectedAccount = useCallback(async () => {
    if (!userId || !selectedAccountRef) return;
    restoreScrollYRef.current = window.scrollY;
    setSyncState({ status: "syncing", message: null });
    try {
      const res = await accountDetailsApi.sync(userId, selectedAccountRef);
      if (selectedAccountRefRef.current !== selectedAccountRef) return;
      setSyncState({ status: res.status, message: res.message });
      if (res.status === "succeeded" || res.status === "partially_succeeded") {
        void load(userId, { quiet: true });
        setDetailReloadKey((prev) => prev + 1);
      } else {
        restoreScrollPositionIfNeeded(restoreScrollYRef);
      }
    } catch (err) {
      if (selectedAccountRefRef.current !== selectedAccountRef) return;
      if (err instanceof ApiRequestError && err.status === 409) {
        setSyncState({ status: "running", message: "Sync already in progress." });
        restoreScrollPositionIfNeeded(restoreScrollYRef);
        return;
      }
      setSyncState({ status: "error", message: errMsg(err) });
      restoreScrollPositionIfNeeded(restoreScrollYRef);
    }
  }, [load, selectedAccountRef, userId]);

  useEffect(() => {
    if (!userId || !selectedAccountRef) {
      setDetailStatus("idle");
      setSelectedDetail(null);
      selectedDetailRef.current = null;
      detailAccountRef.current = null;
      setDetailError(null);
      return;
    }

    let cancelled = false;
    const accountChanged = detailAccountRef.current !== selectedAccountRef;
    const hasCurrentDetail = selectedDetailRef.current?.account_reference === selectedAccountRef;
    setDetailStatus("loading");
    if (accountChanged || !hasCurrentDetail) {
      setSelectedDetail(null);
      selectedDetailRef.current = null;
    }
    detailAccountRef.current = selectedAccountRef;
    setDetailError(null);
    accountDetailsApi
      .getSelected(userId, selectedAccountRef)
      .then((res) => {
        if (cancelled) return;
        setSelectedDetail(res);
        selectedDetailRef.current = res;
        setDetailStatus("success");
        restoreScrollPositionIfNeeded(restoreScrollYRef);
      })
      .catch((err) => {
        if (cancelled) return;
        setDetailError(errMsg(err));
        setDetailStatus("error");
        restoreScrollPositionIfNeeded(restoreScrollYRef);
      });

    return () => { cancelled = true; };
  }, [detailReloadKey, selectedAccountRef, userId]);

  // P32A-T5: after a nickname save/clear the backend returns the refreshed
  // candidate (the authoritative display label). Apply it as the source of
  // truth to the overview row, the scope review-account label, and the open
  // selected-detail header — no extra fetch needed; only display_label moves.
  const handleNicknameUpdated = useCallback((updated: ReviewAccountCandidateRead) => {
    setData((prev) =>
      prev
        ? {
            ...prev,
            accounts: prev.accounts.map((a) =>
              a.account_reference === updated.account_reference
                ? { ...a, display_label: updated.display_label }
                : a,
            ),
            review_account:
              prev.review_account &&
              prev.review_account.account_reference === updated.account_reference
                ? { ...prev.review_account, display_label: updated.display_label }
                : prev.review_account,
          }
        : prev,
    );
    setSelectedDetail((prev) => {
      if (prev && prev.account_reference === updated.account_reference) {
        const next = { ...prev, display_label: updated.display_label };
        selectedDetailRef.current = next;
        return next;
      }
      return prev;
    });
  }, []);

  /* ── No user ─────────────────────────────────────────────────────────── */
  if (!userId) {
    return (
      <div className="mp-surface" style={styles.page}>
        <PageHeader
          eyebrow="Data sources · account details"
          title="Account Details"
          sub="Select a user from the developer account selector to load private account details."
        />
        <EmptyState title="No user selected" body="Select a user from the developer account selector to load account details." />
        <AccountDetailsSafetyStrip />
      </div>
    );
  }

  const isDemo = status === "success" && data?.data_mode === "synthetic_demo";
  const isUnavailable = status === "success" && data?.data_mode === "unavailable";
  const badge = data ? dataModeBadge(data.data_mode) : null;
  const selectedAccount = data && selectedAccountRef
    ? data.accounts.find((acc) => acc.account_reference === selectedAccountRef) ?? null
    : null;

  return (
    <div className="mp-surface" style={styles.page}>
      <PageHeader
        eyebrow="Data sources · account details"
        title="Account Details"
        sub="Connected account detail, snapshot freshness, exposure labels, and private display rows. Read-only."
        right={
          isDemo ? <DemoChip /> :
          badge ? <Badge tone={badge.tone} dot title={badge.title}>{badge.label}</Badge> :
          undefined
        }
      />

      {status === "loading" && <LoadingSkeleton rows={6} label="Loading account details…" />}

      {status === "error" && (
        <ErrorState message={error ?? "Failed to load account details."} onRetry={() => load(userId)} />
      )}

      {status === "success" && data && (
        isUnavailable ? (
          <EmptyState
            title="Account details unavailable"
            body={data.demo_notice ?? "No account-detail snapshot is currently available."}
          />
        ) : (
          <>
            <AccountWorkspace
              userId={userId}
              accounts={data.accounts}
              selectedAccount={selectedAccount}
              selectedDetail={selectedDetail}
              detailStatus={detailStatus}
              detailError={detailError}
              selectedAccountRef={selectedAccountRef}
              onSelect={setSelectedAccountRef}
              onRetrySelected={() => setDetailReloadKey((prev) => prev + 1)}
              syncState={syncState}
              onRefreshSelected={() => { void refreshSelectedAccount(); }}
              onNicknameUpdated={handleNicknameUpdated}
            />

            {/* Provenance + top-level data notes — shown once, not per card */}
            <div style={styles.provenance}>
              <span style={styles.provText}>{data.source_label}</span>
              <span style={styles.provDot} aria-hidden="true">·</span>
              <span style={styles.provText}>Generated {formatGeneratedAt(data.generated_at)}</span>
              {data.privacy_display_mode === "amounts_hidden" && (
                <Badge tone="mute" dot title="Backend privacy mode — monetary amounts are hidden">amounts hidden</Badge>
              )}
            </div>
            {data.caveat_codes.length > 0 && <CaveatDisclosure codes={data.caveat_codes} />}
          </>
        )
      )}

      <AccountDetailsSafetyStrip />
    </div>
  );
}

/* ── Account workspace ────────────────────────────────────────────────── */

function AccountWorkspace({
  userId,
  accounts,
  selectedAccount,
  selectedDetail,
  detailStatus,
  detailError,
  selectedAccountRef,
  onSelect,
  onRetrySelected,
  syncState,
  onRefreshSelected,
  onNicknameUpdated,
}: {
  userId: string;
  accounts: AccountDetailAccountRead[];
  selectedAccount: AccountDetailAccountRead | null;
  selectedDetail: SelectedAccountDetailsRead | null;
  detailStatus: DetailLoadStatus;
  detailError: string | null;
  selectedAccountRef: string | null;
  onSelect: (accountRef: string) => void;
  onRetrySelected: () => void;
  syncState: SyncUiState;
  onRefreshSelected: () => void;
  onNicknameUpdated: (updated: ReviewAccountCandidateRead) => void;
}) {
  if (accounts.length === 0) {
    return (
      <EmptyState
        title="No connected accounts"
        body="No accounts are present in this scope yet."
      />
    );
  }

  return (
    <section className="account-details-workspace" style={styles.workspace} aria-label="Account details workspace">
      <aside style={styles.selectorPane}>
        <div style={styles.selectorHead}>
          <div>
            <span style={styles.sectionLabel}>Accounts</span>
            <p style={styles.selectorSub}>Browse one private account at a time.</p>
          </div>
          <span style={styles.sectionCount}>{accounts.length}</span>
        </div>
        <div style={styles.accountList} role="list" aria-label="Connected accounts">
          {accounts.map((acc) => (
            <AccountSelectorItem
              key={acc.account_reference}
              acc={acc}
              selected={acc.account_reference === selectedAccountRef}
              onSelect={() => onSelect(acc.account_reference)}
            />
          ))}
        </div>
      </aside>

      <main style={styles.detailPane}>
        <AccountWorkspaceTopBar
          syncState={syncState}
          onRefresh={onRefreshSelected}
        />
        <div style={styles.detailCanvas}>
          {selectedAccount ? (
            <SelectedAccountDetail
              userId={userId}
              acc={selectedAccount}
              detail={selectedDetail}
              status={detailStatus}
              error={detailError}
              onRetry={onRetrySelected}
              onNicknameUpdated={onNicknameUpdated}
            />
          ) : (
            <EmptyState
              title="Select an account"
              body="Choose an account from the list to inspect its private detail summary."
            />
          )}
        </div>
      </main>
    </section>
  );
}

// Founder-demo navigation. Dashboard is the only built surface, so it is the
// current view and the rest are honestly disabled "Soon" — no fake tab system,
// no incomplete tablist/tabpanel ARIA. Rendered as a simple segmented nav.
const ACCOUNT_NAV_ITEMS = ["Dashboard", "Analytics", "Reports", "Settings"] as const;

function AccountWorkspaceTopBar({
  syncState,
  onRefresh,
}: {
  syncState: SyncUiState;
  onRefresh: () => void;
}) {
  const isSyncing = syncState.status === "syncing";
  const isRunning = syncState.status === "running";
  const disabled = isSyncing;
  const label = isSyncing ? "Refreshing" : "Refresh snapshot";
  const title = isRunning
    ? "Sync already in progress. You can try again later."
    : "Request a fresh broker snapshot for this account.";

  return (
    <header style={styles.workspaceTopBar}>
      <nav style={styles.workspaceTabs} aria-label="Account workspace navigation">
        {ACCOUNT_NAV_ITEMS.map((item) =>
          item === "Dashboard" ? (
            <span
              key={item}
              className="account-details-top-tab"
              style={{ ...styles.workspaceTab, ...styles.workspaceTabActive }}
              data-active="true"
              aria-current="page"
            >
              {item}
            </span>
          ) : (
            <button
              key={item}
              type="button"
              className="account-details-top-tab"
              style={{ ...styles.workspaceTab, ...styles.workspaceTabDisabled }}
              disabled
              title="Coming soon"
            >
              {item}
              <span style={styles.soonTag}>Soon</span>
            </button>
          ),
        )}
      </nav>
      <div style={styles.workspaceActions}>
        <div style={styles.topRefreshGroup}>
          <button
            type="button"
            className="account-details-refresh-button"
            onClick={onRefresh}
            disabled={disabled}
            aria-label={label}
            title={title}
            style={{
              ...styles.topRefreshBtn,
              opacity: disabled ? 0.62 : 1,
              cursor: isSyncing ? "wait" : "pointer",
            }}
          >
            <span>{label}</span>
            <MpIcon name="refresh" size={13} style={isSyncing ? styles.refreshIconSpin : undefined} />
          </button>
          <RefreshSnapshotStatus syncState={syncState} />
        </div>
        <span style={styles.profileAvatar} aria-label="User profile" role="img">
          <MpIcon name="agent" size={16} />
        </span>
      </div>
    </header>
  );
}

function AccountSelectorItem({
  acc,
  selected,
  onSelect,
}: {
  acc: AccountDetailAccountRead;
  selected: boolean;
  onSelect: () => void;
}) {
  const primaryRole = primaryScopeRole(acc.scope_roles);
  const stripeMeta = primaryRole ? scopeRoleMeta(primaryRole) : null;
  const roleMeta = primaryRole && primaryRole !== "included_in_scope" ? scopeRoleMeta(primaryRole) : null;
  const totalLabel = acc.total_value_label ?? "Value label unavailable";

  return (
    <button
      type="button"
      className="account-details-selector-button"
      aria-pressed={selected}
      onClick={onSelect}
      style={{
        ...styles.selectorButton,
        ...(selected ? styles.selectorButtonSelected : null),
      }}
    >
      <span
        style={{
          ...styles.selectorStripe,
          backgroundColor: selected
            ? "var(--mp-accent)"
            : (stripeMeta ? roleColor(stripeMeta.tone) : "var(--mp-rule-strong)"),
        }}
        aria-hidden="true"
      />
      <span style={styles.selectorBody}>
        <span style={styles.selectorTitleRow}>
          <span style={styles.selectorTitle}>{acc.display_label}</span>
          {roleMeta && <Badge tone={roleMeta.tone} dot={false}>{roleMeta.label}</Badge>}
        </span>
        <span style={styles.selectorKind}>{acc.account_kind_label}</span>
        <span style={styles.selectorMeta}>
          <span>{acc.source_label}</span>
          <span style={styles.metaDot} aria-hidden="true">·</span>
          <span>{acc.connection_status_label}</span>
        </span>
        <span style={styles.selectorBottom}>
          <span className="mp-mono" style={styles.selectorValue}>{totalLabel}</span>
        </span>
      </span>
    </button>
  );
}

function SelectedAccountDetail({
  userId,
  acc,
  detail,
  status,
  error,
  onRetry,
  onNicknameUpdated,
}: {
  userId: string;
  acc: AccountDetailAccountRead;
  detail: SelectedAccountDetailsRead | null;
  status: DetailLoadStatus;
  error: string | null;
  onRetry: () => void;
  onNicknameUpdated: (updated: ReviewAccountCandidateRead) => void;
}) {
  const header = detail ?? acc;
  const caveatCodes = detail?.caveat_codes ?? acc.caveat_codes;
  const readinessCaveats = acc.readiness_caveats ?? [];
  const hasDetail = detail != null;
  const isRefreshingDetail = status === "loading" && hasDetail;
  const isStaleError = status === "error" && hasDetail;

  return (
      <article style={styles.detailArticle}>
        <header style={styles.detailHeader}>
          <div style={styles.detailTitleBlock}>
            <span style={styles.detailEyebrow}>Selected account</span>
            <NicknameEditableTitle
              userId={userId}
              accountReference={acc.account_reference}
              label={header.display_label}
              onUpdated={onNicknameUpdated}
            />
            <p style={styles.detailKind}>{header.account_kind_label}</p>
          </div>
          <RoleBadges roles={acc.scope_roles} />
        </header>

        <div style={styles.metaRow}>
          <span style={styles.metaItem}>{header.source_label}</span>
          <span style={styles.metaDot} aria-hidden="true">·</span>
          <span style={styles.metaItem}>{header.connection_status_label}</span>
          {header.last_successful_sync_label && (
            <>
              <span style={styles.metaDot} aria-hidden="true">·</span>
              <span style={styles.metaItem}>
                <MpIcon name="clock" size={11} style={{ color: "var(--mp-mute)", verticalAlign: "middle", marginRight: 3 }} />
                {header.last_successful_sync_label}
              </span>
            </>
          )}
        </div>

        {isRefreshingDetail && (
          <div style={styles.detailRefreshNotice} role="status" aria-live="polite">
            <MpIcon name="refresh" size={12} style={styles.refreshIconSpin} />
            <span>Updating selected detail…</span>
          </div>
        )}

        {isStaleError && (
          <div style={styles.detailRefreshNotice} role="status" aria-live="polite">
            <MpIcon name="alert" size={12} />
            <span>{error ?? "Could not update selected detail. Previous detail remains visible."}</span>
          </div>
        )}

        {status === "loading" && !hasDetail && (
          <LoadingSkeleton rows={5} label="Loading selected account details…" />
        )}

        {status === "error" && !hasDetail && (
          <ErrorState message={error ?? "Failed to load selected account details."} onRetry={onRetry} />
        )}

        {detail?.data_mode === "unavailable" && (
          <EmptyState
            title="Selected account details unavailable"
            body="This account does not currently have a private detail snapshot available."
          />
        )}

        {detail?.data_mode === "private_real_source" && (
          <>
            <AccountSummaryBand detail={detail} />
            <PositionReadinessRows detail={detail} />
            <ReadinessDisclosure
              caveats={readinessCaveats}
              caveatCodes={caveatCodes}
              limitations={detail.limitations}
            />
          </>
        )}
      </article>
  );
}

/**
 * P32A-T5: user-owned display-name editor for the selected account header.
 *
 * Collapsed, it shows the backend display label plus a small "Edit display
 * name" icon action. Editing reveals a compact inline input with Save / Clear /
 * Cancel. It sends only the opaque account_reference and the nickname text (or
 * null to clear) to PATCH /users/{uid}/account-details/{account_reference}/
 * nickname; the backend owns validation, normalization, allowed characters,
 * length, and private-token rejection. The refreshed candidate the backend
 * returns is the source of truth for the new label. No raw IDs, balances,
 * holdings, or provider data are sent or shown, and nothing is stored locally.
 */
function NicknameEditableTitle({
  userId,
  accountReference,
  label,
  onUpdated,
}: {
  userId: string;
  accountReference: string;
  label: string;
  onUpdated: (updated: ReviewAccountCandidateRead) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  // When the inline editor closes, return focus to the trigger so keyboard and
  // screen-reader users are not dropped to document.body as the input unmounts.
  const restoreFocusRef = useRef(false);
  const hintId = useId();

  useEffect(() => {
    if (!editing && restoreFocusRef.current) {
      restoreFocusRef.current = false;
      triggerRef.current?.focus();
    }
  }, [editing]);

  function closeEditor() {
    restoreFocusRef.current = true;
    setEditing(false);
    setError(null);
  }

  async function submit(nickname: string | null) {
    setSaving(true);
    setError(null);
    try {
      const updated = await accountDetailsApi.updateNickname(userId, accountReference, nickname);
      onUpdated(updated);
      restoreFocusRef.current = true;
      setEditing(false);
      setValue("");
    } catch (err) {
      setError(
        err instanceof ApiRequestError
          ? err.detail
          : err instanceof Error
            ? err.message
            : "Could not update the display name.",
      );
    } finally {
      setSaving(false);
    }
  }

  if (!editing) {
    return (
      <div style={styles.nicknameTitleRow}>
        <h2 className="mp-display" style={styles.detailTitle}>{label}</h2>
        <button
          ref={triggerRef}
          type="button"
          className="account-details-nickname-trigger"
          style={styles.nicknameEditBtn}
          aria-label="Edit account name"
          title="Edit account name"
          data-tooltip="Edit account name"
          onClick={() => {
            setValue("");
            setError(null);
            setEditing(true);
          }}
        >
          <MpIcon name="edit" size={15} strokeWidth={1.8} />
        </button>
      </div>
    );
  }

  const trimmed = value.trim();
  return (
    <div style={styles.nicknameEditor}>
      <div style={styles.nicknameInputRow}>
        <input
          style={styles.nicknameInput}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              if (!saving) submit(trimmed === "" ? null : trimmed);
            } else if (e.key === "Escape") {
              e.preventDefault();
              closeEditor();
            }
          }}
          placeholder="Display name"
          aria-label="Display name"
          aria-describedby={hintId}
          maxLength={60}
          autoFocus
          disabled={saving}
          autoComplete="off"
          spellCheck={false}
        />
        <button
          type="button"
          style={styles.nicknameSave}
          onClick={() => submit(trimmed === "" ? null : trimmed)}
          disabled={saving}
        >
          {saving ? "Saving…" : "Save"}
        </button>
        <button
          type="button"
          style={styles.nicknameGhost}
          onClick={() => submit(null)}
          disabled={saving}
        >
          Clear
        </button>
        <button
          type="button"
          style={styles.nicknameGhost}
          onClick={closeEditor}
          disabled={saving}
        >
          Cancel
        </button>
      </div>
      {error && (
        <p style={styles.nicknameError} role="alert">
          <MpIcon name="alert" size={11} style={{ verticalAlign: "middle", marginRight: 4 }} />
          {error}
        </p>
      )}
      <p id={hintId} style={styles.nicknameHint}>This changes only your Portfolio Copilot label.</p>
    </div>
  );
}

/**
 * Compact one-line status under the refresh button. Tone matches the
 * backend status; nothing is shown while the control is in its initial
 * idle state.
 */
function RefreshSnapshotStatus({ syncState }: { syncState: SyncUiState }) {
  if (syncState.status === "idle" || syncState.status === "syncing") return null;
  const tone = refreshStatusTone(syncState.status);
  const text = refreshStatusText(syncState);
  return (
    <span style={{ ...styles.refreshStatus, color: roleColor(tone) }} aria-live="polite">
      <span style={{ ...styles.statusDot, backgroundColor: roleColor(tone) }} aria-hidden="true" />
      <span>{text}</span>
    </span>
  );
}

function refreshStatusTone(status: SyncUiStatus): MpTone {
  switch (status) {
    case "succeeded": return "live";
    case "partially_succeeded": return "stale";
    case "running": return "info";
    case "failed":
    case "error": return "block";
    default: return "mute";
  }
}

function refreshStatusText(state: SyncUiState): string {
  if (state.status === "running") return state.message ?? "Sync already in progress.";
  if (state.status === "error") return state.message ?? "Refresh request failed.";
  // succeeded / partially_succeeded / failed — render the backend-owned
  // message verbatim when present, with a safe local fallback.
  if (state.message) return state.message;
  switch (state.status) {
    case "succeeded": return "Snapshot refreshed.";
    case "partially_succeeded": return "Snapshot refreshed with some unavailable data.";
    case "failed": return "Snapshot refresh failed.";
    default: return "";
  }
}

function RoleBadges({ roles }: { roles: AccountScopeRole[] }) {
  return (
    <div style={styles.roleBadges}>
      {roles.map((role) => {
        const m = scopeRoleMeta(role);
        return <Badge key={role} tone={m.tone} dot>{m.label}</Badge>;
      })}
    </div>
  );
}

/**
 * Compact account summary band — promotes the backend summary labels (total
 * value, exposures, cash, collateral) into the prime space above the position
 * tables, with one tight cash-detail line and a single muted two-scope
 * freshness line. Every value is a backend display label rendered verbatim;
 * null/placeholder-empty labels are dropped (self-describing "hidden"
 * placeholders in amounts_hidden mode are kept and shown as-is).
 */
function AccountSummaryBand({ detail }: { detail: SelectedAccountDetailsRead }) {
  const s = detail.summary_labels;
  const firstCash = detail.cash_rows[0] ?? null;
  const cashValue = s.cash_label ?? firstCash?.cash_amount_label ?? null;

  // Backend labels are self-describing (e.g. "Total value $142,428.26"); the
  // tile already carries the heading, so strip the redundant leading phrase and
  // show just the value text. Display-only cleanup; the value is otherwise verbatim.
  const tiles: { key: string; label: string; value: string; primary?: boolean }[] = [
    { key: "total", label: "Total value", value: stripLabelPrefix(s.total_value_label, ["Total value"]), primary: true },
    { key: "stock", label: "Stock / ETF exposure", value: stripLabelPrefix(s.stock_etf_exposure_label, ["Stock/ETF exposure", "Stock / ETF exposure"]) },
    { key: "options", label: "Options exposure", value: stripLabelPrefix(s.options_exposure_label, ["Options exposure"]) },
    { key: "cash", label: "Cash", value: stripLabelPrefix(cashValue, ["Cash"]) },
    { key: "collateral", label: "Collateral usage", value: stripLabelPrefix(s.collateral_usage_label, ["Collateral usage"]) },
  ].filter((t) => isPresentLabel(t.value));

  return (
    <section style={styles.summarySection} aria-label="Account summary">
      {tiles.length > 0 && (
        <div style={styles.summaryBand}>
          {tiles.map((t) => (
            <div key={t.key} style={{ ...styles.statTile, ...(t.primary ? styles.statTilePrimary : null) }}>
              <span style={styles.statTileLabel}>{t.label}</span>
              <span
                className="mp-mono"
                style={t.primary ? styles.statTileValuePrimary : styles.statTileValue}
              >
                {t.value}
              </span>
            </div>
          ))}
        </div>
      )}

      {detail.cash_rows.length > 0 && <CashDetailLines rows={detail.cash_rows} multi={detail.cash_rows.length > 1} />}

      <SnapshotFreshnessLine
        broker={detail.broker_snapshot_freshness}
        market={detail.market_quote_freshness}
      />
    </section>
  );
}

function CashDetailLines({ rows, multi }: { rows: AccountCashDisplayRowRead[]; multi: boolean }) {
  return (
    <div style={styles.cashDetail} aria-label="Cash detail">
      {rows.map((row) => {
        const parts: string[] = [];
        // For multiple currencies, lead with the per-row amount so each line is
        // distinguishable; the single-row case shows its amount in the tile.
        if (multi && isMeaningfulDisplayLabel(row.cash_amount_label)) {
          parts.push(`${row.currency_label} ${row.cash_amount_label}`);
        } else {
          parts.push(row.currency_label);
        }
        parts.push(row.cash_state_label);
        if (isMeaningfulDisplayLabel(row.available_cash_label)) parts.push(`Available ${cleanCashPrefixLabel(row.available_cash_label, "Available cash")}`);
        if (isMeaningfulDisplayLabel(row.buying_power_label)) parts.push(`Buying power ${cleanBuyingPowerLabel(row.buying_power_label)}`);
        if (isMeaningfulDisplayLabel(row.balance_source_label)) parts.push(row.balance_source_label);
        return (
          <p key={row.row_reference} style={styles.cashDetailLine}>
            {parts.map((p, i) => (
              <Fragment key={i}>
                {i > 0 && <span style={styles.metaDot} aria-hidden="true">·</span>}
                <span>{p}</span>
              </Fragment>
            ))}
          </p>
        );
      })}
    </div>
  );
}

function SnapshotFreshnessLine({
  broker,
  market,
}: {
  broker: { status: ReadinessSnapshotStatus; display_label: string; as_of_label: string | null };
  market: { status: ReadinessSnapshotStatus; display_label: string; as_of_label: string | null } | null;
}) {
  return (
    <div style={styles.freshnessLine} aria-label="Snapshot freshness">
      <FreshnessScope freshness={broker} />
      <span style={styles.metaDot} aria-hidden="true">·</span>
      {market ? (
        <FreshnessScope freshness={market} />
      ) : (
        <span style={styles.freshnessScope}>
          <span style={{ ...styles.statusDot, backgroundColor: roleColor("mute") }} aria-hidden="true" />
          <span>Market quotes unavailable</span>
        </span>
      )}
    </div>
  );
}

function FreshnessScope({
  freshness,
}: {
  freshness: { status: ReadinessSnapshotStatus; display_label: string; as_of_label: string | null };
}) {
  // Backend display_label is self-describing (e.g. "Broker snapshot freshness
  // unknown") — render verbatim with a small status-tone dot as a secondary,
  // non-color-only cue. Broker vs market scopes stay distinct. as_of is omitted
  // here: the header already shows "Last successful sync" once, and an
  // unavailable scope's as_of just echoes its own label.
  return (
    <span style={styles.freshnessScope}>
      <span style={{ ...styles.statusDot, backgroundColor: roleColor(freshnessTone(freshness.status)) }} aria-hidden="true" />
      <span>{compactFreshnessLabel(freshness.display_label)}</span>
    </span>
  );
}

function PositionReadinessRows({ detail }: { detail: SelectedAccountDetailsRead }) {
  const hasPositionRows = detail.equity_position_rows.length > 0 || detail.option_position_rows.length > 0;
  return (
    <section style={styles.readinessSection} aria-label="Position detail">
      <header style={styles.readinessSectionHeader}>
        <span style={styles.readinessSectionTitle}>Positions</span>
        <span className="mp-mono" style={styles.rowSectionCount}>
          {detail.equity_position_rows.length + detail.option_position_rows.length}
        </span>
      </header>
      {hasPositionRows ? (
        <div style={styles.rowsStack}>
          {detail.equity_position_rows.length > 0 && <EquityRows rows={detail.equity_position_rows} />}
          {detail.option_position_rows.length > 0 && <OptionRows rows={detail.option_position_rows} />}
        </div>
      ) : (
        <p style={styles.readinessNoteText}>Position detail is limited while latest-sync membership is verified.</p>
      )}
    </section>
  );
}

function EquityRows({ rows }: { rows: AccountEquityPositionDisplayRowRead[] }) {
  const [expandedRows, setExpandedRows] = useState<Set<string>>(() => new Set());
  const showLastPrice = rows.some((row) => isMeaningfulDisplayLabel(row.last_price_label));
  const showMarketValue = rows.some((row) => isMeaningfulDisplayLabel(row.market_value_label));
  const showAverageCost = rows.some((row) => isMeaningfulDisplayLabel(row.average_cost_label));
  const showCostBasis = rows.some((row) => isMeaningfulDisplayLabel(row.cost_basis_label));
  const showTotalGainLoss = rows.some((row) => isMeaningfulDisplayLabel(row.total_gain_loss_label));
  const showGainLossPercent = rows.some((row) => isMeaningfulDisplayLabel(row.gain_loss_percent_label));
  const columnCount = 2 +
    Number(showLastPrice) +
    Number(showMarketValue) +
    Number(showAverageCost) +
    Number(showCostBasis) +
    Number(showTotalGainLoss) +
    Number(showGainLossPercent);
  const toggleRow = (rowReference: string) => {
    setExpandedRows((current) => {
      const next = new Set(current);
      if (next.has(rowReference)) next.delete(rowReference);
      else next.add(rowReference);
      return next;
    });
  };

  return (
    <RowSection title="Stock / ETF / fund positions" count={rows.length} empty="No equity position display rows are available for this account.">
      {rows.length > 0 && (
        <div style={styles.tableScroller}>
          <table style={{ ...styles.dataTable, minWidth: tableMinWidth(columnCount) }}>
            <thead>
              <tr>
                <th className="mp-sticky-col" style={styles.thStickyLeft}>Symbol</th>
                {showLastPrice && <th style={styles.th}>Last price</th>}
                {showMarketValue && <th style={styles.th}>Current value</th>}
                {showTotalGainLoss && <th style={styles.th}>Total gain/loss</th>}
                {showGainLossPercent && <th style={styles.th}>Gain/loss %</th>}
                <th style={styles.th}>Quantity</th>
                {showAverageCost && <th style={styles.th}>Avg cost</th>}
                {showCostBasis && <th style={styles.th}>Cost basis</th>}
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const canExpand = hasEquityExpandedDetail(row);
                const expanded = expandedRows.has(row.row_reference);
                return (
                <Fragment key={row.row_reference}>
                  <tr
                    className={canExpand ? "mp-row-expandable" : undefined}
                    onClick={canExpand ? () => toggleRow(row.row_reference) : undefined}
                    style={canExpand ? styles.expandableTableRow : undefined}
                    aria-expanded={canExpand ? expanded : undefined}
                  >
                    <td className="mp-sticky-col" style={styles.tdStickyStrong}>
                      <span style={styles.symbolStack}>
                        <span style={styles.symbolMain}>
                          <span>{row.symbol_label}</span>
                        </span>
                      </span>
                    </td>
                    {showLastPrice && <td style={styles.tdMono}>{row.last_price_label ?? "—"}</td>}
                    {showMarketValue && <td style={styles.tdMono}>{cleanMarketValueLabel(row.market_value_label) ?? "—"}</td>}
                    {showTotalGainLoss && <td style={gainLossCellStyle(row.total_gain_loss_label)}>{row.total_gain_loss_label ?? "—"}</td>}
                    {showGainLossPercent && <td style={gainLossCellStyle(row.gain_loss_percent_label)}>{row.gain_loss_percent_label ?? "—"}</td>}
                    <td style={styles.tdMono}>{cleanShareQuantityLabel(row.quantity_label)}</td>
                    {showAverageCost && <td style={styles.tdMono}>{row.average_cost_label ?? "—"}</td>}
                    {showCostBasis && <td style={styles.tdMono}>{row.cost_basis_label ?? "—"}</td>}
                  </tr>
                  {canExpand && expanded && (
                    <tr>
                      <td style={styles.tdLotCell} colSpan={columnCount}>
                        <PositionExpandedDetails row={row} />
                      </td>
                    </tr>
                  )}
                </Fragment>
              );})}
            </tbody>
          </table>
        </div>
      )}
    </RowSection>
  );
}

/**
 * Expansion is offered only when it adds something the row doesn't already
 * show. For equity that is the instrument name (the row shows just the ticker)
 * or purchase-history lots. Asset class alone is too thin to justify an
 * expansion, so it rides along as secondary metadata only when the panel is
 * already open. Tax lots are deferred upstream, so with no lots the panel is
 * just the compact name line — never raw IDs, payloads, or valuation source.
 */
function hasEquityExpandedDetail(row: AccountEquityPositionDisplayRowRead): boolean {
  return row.tax_lot_rows.length > 0 ||
    isMeaningfulDisplayLabel(row.instrument_name_label);
}

/**
 * Option rows already surface contract, type/side, strike, and expiration
 * inline, so the only expansion worth offering is purchase history. Multiplier
 * alone is low-value (and reads oddly for standard contracts), so it is shown
 * only as secondary metadata when lots open the panel — not as an expand
 * trigger.
 */
function hasOptionExpandedDetail(row: AccountOptionPositionDisplayRowRead): boolean {
  return row.tax_lot_rows.length > 0;
}

function OptionRows({ rows }: { rows: AccountOptionPositionDisplayRowRead[] }) {
  const [expandedRows, setExpandedRows] = useState<Set<string>>(() => new Set());
  const showLastPrice = rows.some((row) => isMeaningfulDisplayLabel(row.last_price_label));
  const showMarketValue = rows.some((row) => isMeaningfulDisplayLabel(row.market_value_label));
  const showAverageCost = rows.some((row) => isMeaningfulDisplayLabel(row.average_cost_label));
  const showCostBasis = rows.some((row) => isMeaningfulDisplayLabel(row.cost_basis_label));
  const showTotalGainLoss = rows.some((row) => isMeaningfulDisplayLabel(row.total_gain_loss_label));
  const showGainLossPercent = rows.some((row) => isMeaningfulDisplayLabel(row.gain_loss_percent_label));
  const columnCount = 5 +
    Number(showLastPrice) +
    Number(showMarketValue) +
    Number(showAverageCost) +
    Number(showCostBasis) +
    Number(showTotalGainLoss) +
    Number(showGainLossPercent);
  const toggleRow = (rowReference: string) => {
    setExpandedRows((current) => {
      const next = new Set(current);
      if (next.has(rowReference)) next.delete(rowReference);
      else next.add(rowReference);
      return next;
    });
  };

  return (
    <RowSection title="Option positions" count={rows.length} empty="No option position display rows are available for this account.">
      {rows.length > 0 && (
        <div style={styles.tableScroller}>
          <table style={{ ...styles.dataTable, minWidth: tableMinWidth(columnCount) }}>
            <thead>
              <tr>
                <th className="mp-sticky-col" style={styles.thStickyLeft}>Contract</th>
                <th style={styles.thLeft}>Type / side</th>
                <th style={styles.th}>Strike</th>
                <th style={styles.thLeft}>Expiration</th>
                {showLastPrice && <th style={styles.th}>Last price</th>}
                {showMarketValue && <th style={styles.th}>Market value</th>}
                {showTotalGainLoss && <th style={styles.th}>Total gain/loss</th>}
                {showGainLossPercent && <th style={styles.th}>Gain/loss %</th>}
                <th style={styles.th}>Quantity</th>
                {showAverageCost && <th style={styles.th}>Avg cost</th>}
                {showCostBasis && <th style={styles.th}>Cost basis</th>}
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const canExpand = hasOptionExpandedDetail(row);
                const expanded = expandedRows.has(row.row_reference);
                return (
                <Fragment key={row.row_reference}>
                  <tr
                    className={canExpand ? "mp-row-expandable" : undefined}
                    onClick={canExpand ? () => toggleRow(row.row_reference) : undefined}
                    style={canExpand ? styles.expandableTableRow : undefined}
                    aria-expanded={canExpand ? expanded : undefined}
                  >
                    <td className="mp-sticky-col" style={styles.tdStickyStrong}>
                      <span style={styles.symbolStack}>
                        <span style={styles.symbolMain}>{row.underlying_symbol_label}</span>
                        <span style={styles.symbolSub}>{row.contract_label}</span>
                      </span>
                    </td>
                    <td style={styles.td}>{row.option_type_label} · {row.side_label}</td>
                    <td style={styles.tdMono}>{row.strike_label}</td>
                    <td style={styles.td}>{row.expiration_label}</td>
                    {showLastPrice && <td style={styles.tdMono}>{row.last_price_label ?? "—"}</td>}
                    {showMarketValue && <td style={styles.tdMono}>{cleanMarketValueLabel(row.market_value_label) ?? "—"}</td>}
                    {showTotalGainLoss && <td style={gainLossCellStyle(row.total_gain_loss_label)}>{row.total_gain_loss_label ?? "—"}</td>}
                    {showGainLossPercent && <td style={gainLossCellStyle(row.gain_loss_percent_label)}>{row.gain_loss_percent_label ?? "—"}</td>}
                    <td style={styles.tdMono}>{cleanContractQuantityLabel(row.quantity_label)}</td>
                    {showAverageCost && <td style={styles.tdMono}>{row.average_cost_label ?? "—"}</td>}
                    {showCostBasis && <td style={styles.tdMono}>{row.cost_basis_label ?? "—"}</td>}
                  </tr>
                  {canExpand && expanded && (
                    <tr>
                      <td style={styles.tdLotCell} colSpan={columnCount}>
                        <OptionExpandedDetails row={row} />
                      </td>
                    </tr>
                  )}
                </Fragment>
              );})}
            </tbody>
          </table>
        </div>
      )}
    </RowSection>
  );
}

/**
 * Compact contextual-metadata line for an expanded position panel. Renders the
 * primary identity label (instrument name / contract) a touch stronger, then
 * dot-separated secondary labels in muted text — left-aligned, inline, sized
 * like metadata rather than a panel header. Every entry is a backend label
 * rendered verbatim; null/placeholder fields are dropped by the caller.
 */
function ExpandedMeta({ primary, secondary }: { primary: string | null; secondary: string[] }) {
  if (!primary && secondary.length === 0) return null;
  const parts: { text: string; primary: boolean }[] = [
    ...(primary ? [{ text: primary, primary: true }] : []),
    ...secondary.map((text) => ({ text, primary: false })),
  ];
  return (
    <p style={styles.expandedMeta}>
      {parts.map((part, i) => (
        <Fragment key={`${part.text}-${i}`}>
          {i > 0 && <span style={styles.metaDot} aria-hidden="true">·</span>}
          <span style={part.primary ? styles.expandedMetaPrimary : styles.expandedMetaSecondary}>{part.text}</span>
        </Fragment>
      ))}
    </p>
  );
}

function PositionExpandedDetails({ row }: { row: AccountEquityPositionDisplayRowRead }) {
  // Instrument name leads as compact contextual metadata (the row shows only
  // the ticker); asset class trails as secondary text. Valuation source is
  // intentionally omitted per P27B-T21 display policy (no provider/account
  // internals). All labels are backend-verbatim.
  const primary = isMeaningfulDisplayLabel(row.instrument_name_label) ? row.instrument_name_label : null;
  const secondary = isMeaningfulDisplayLabel(row.asset_class_label) ? [row.asset_class_label] : [];

  return (
    <div style={styles.expandedRowPanel} data-account-expanded-row="true">
      <ExpandedMeta primary={primary} secondary={secondary} />
      <PurchaseHistoryBlock
        lots={row.tax_lot_rows}
        pagination={row.tax_lot_pagination}
      />
    </div>
  );
}

function OptionExpandedDetails({ row }: { row: AccountOptionPositionDisplayRowRead }) {
  // Contract identity leads as compact contextual metadata; multiplier trails
  // as secondary text (it's low-value for standard contracts, so it only shows
  // when lots have already opened the panel). Valuation source is omitted per
  // P27B-T21 display policy.
  const secondary = isMeaningfulDisplayLabel(row.multiplier_label) ? [row.multiplier_label] : [];
  return (
    <div style={styles.expandedRowPanel} data-account-expanded-row="true">
      <ExpandedMeta primary={row.contract_label} secondary={secondary} />
      <PurchaseHistoryBlock
        lots={row.tax_lot_rows}
        pagination={row.tax_lot_pagination}
      />
    </div>
  );
}

/**
 * Brokerage-style "Purchase history" table shared by equity and option
 * row expansions (P27B-T21).
 *
 * Columns follow Fidelity-inspired ordering: Acquired → Term → Total
 * gain/loss → Gain/loss % → Current value → Quantity → Avg cost → Cost basis.
 * Headers are display-only renames; every cell is rendered verbatim from
 * backend lot labels. Gain/loss tone is purely glyph-driven so color stays
 * supplementary. The frontend never computes a financial value here.
 *
 * When `lots` is empty the block renders nothing — purchase history is
 * deferred while the provider snapshot does not supply tax lots, and the
 * expansion must not advertise a missing feature.
 *
 * `lot_reference` is used only as a React key and is never displayed.
 */
function PurchaseHistoryBlock({
  lots,
  pagination,
}: {
  lots: AccountTaxLotDisplayRowRead[];
  pagination: AccountTaxLotPaginationRead | null;
}) {
  // Tax-lot purchase history is deferred while the provider snapshot does not
  // include lots for connected accounts. Render nothing when lots are absent
  // so the expansion does not advertise a missing feature.
  if (lots.length === 0) return null;

  // Prefer the explicit average_cost_label per lot (P27B-T20 brokerage
  // semantics: per-share for equity, per-contract premium for options).
  // Fall back to purchase_price_label so older lot snapshots still render.
  const avgCostFor = (lot: AccountTaxLotDisplayRowRead): string | null =>
    isMeaningfulDisplayLabel(lot.average_cost_label) ? lot.average_cost_label
      : (isMeaningfulDisplayLabel(lot.purchase_price_label) ? lot.purchase_price_label : null);

  const showAcquired = lots.some((lot) => isMeaningfulDisplayLabel(lot.acquired_date_label));
  const showQuantity = lots.some((lot) => isMeaningfulDisplayLabel(lot.quantity_label));
  const showAvgCost = lots.some((lot) => isMeaningfulDisplayLabel(avgCostFor(lot)));
  const showCostBasis = lots.some((lot) => isMeaningfulDisplayLabel(lot.cost_basis_label));
  const showCurrentValue = lots.some((lot) => isMeaningfulDisplayLabel(lot.current_value_label));
  const showTotalGainLoss = lots.some((lot) => isMeaningfulDisplayLabel(lot.total_gain_loss_label));
  const showGainLossPercent = lots.some((lot) => isMeaningfulDisplayLabel(lot.gain_loss_percent_label));
  const columnCount = 2 +
    Number(showAcquired) +
    Number(showQuantity) +
    Number(showAvgCost) +
    Number(showCostBasis) +
    Number(showCurrentValue) +
    Number(showTotalGainLoss) +
    Number(showGainLossPercent);

  return (
    <div style={styles.lotBlock}>
      <div style={styles.lotBlockHeader}>
        <span style={styles.lotBlockTitle}>Purchase history</span>
        <span className="mp-mono" style={styles.lotCount}>{lots.length}</span>
      </div>
      {pagination?.has_more && (
        <p style={styles.lotNote}>
          Showing first {pagination.displayed_count} of {pagination.total_count} tax lots.
        </p>
      )}
      <div style={styles.tableScroller}>
        <table style={{ ...styles.lotTable, minWidth: tableMinWidth(columnCount) }}>
          <thead>
            <tr>
              {showAcquired && <th className="mp-sticky-col" style={styles.thStickyLeft}>Acquired</th>}
              <th className={showAcquired ? undefined : "mp-sticky-col"} style={showAcquired ? styles.thLeft : styles.thStickyLeft}>Term</th>
              {showTotalGainLoss && <th style={styles.th}>Total gain/loss</th>}
              {showGainLossPercent && <th style={styles.th}>Gain/loss %</th>}
              {showCurrentValue && <th style={styles.th}>Current value</th>}
              {showQuantity && <th style={styles.th}>Quantity</th>}
              {showAvgCost && <th style={styles.th}>Avg cost</th>}
              {showCostBasis && <th style={styles.th}>Cost basis</th>}
            </tr>
          </thead>
          <tbody>
            {lots.map((lot) => (
              <tr key={lot.lot_reference}>
                {showAcquired && <td className="mp-sticky-col" style={styles.tdStickyMuted}>{lot.acquired_date_label ?? "—"}</td>}
                <td className={showAcquired ? undefined : "mp-sticky-col"} style={showAcquired ? styles.td : styles.tdSticky}>{lot.term_label}</td>
                {showTotalGainLoss && <td style={gainLossCellStyle(lot.total_gain_loss_label)}>{lot.total_gain_loss_label ?? "—"}</td>}
                {showGainLossPercent && <td style={gainLossCellStyle(lot.gain_loss_percent_label)}>{lot.gain_loss_percent_label ?? "—"}</td>}
                {showCurrentValue && <td style={styles.tdMono}>{lot.current_value_label ?? "—"}</td>}
                {showQuantity && <td style={styles.tdMono}>{lot.quantity_label ?? "—"}</td>}
                {showAvgCost && <td style={styles.tdMono}>{avgCostFor(lot) ?? "—"}</td>}
                {showCostBasis && <td style={styles.tdMono}>{lot.cost_basis_label ?? "—"}</td>}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function RowSection({
  title,
  count,
  empty,
  children,
}: {
  title: string;
  count: number;
  empty: string;
  children: ReactNode;
}) {
  return (
    <section style={styles.rowSection}>
      <header style={styles.rowSectionHeader}>
        <span style={styles.rowSectionTitle}>{title}</span>
        <span className="mp-mono" style={styles.rowSectionCount}>{count}</span>
      </header>
      {count === 0 ? <span style={styles.quietText}>{empty}</span> : children}
    </section>
  );
}

function ReadinessDisclosure({
  caveats,
  caveatCodes,
  limitations,
}: {
  caveats: AccountDetailsReadinessCaveatRead[];
  caveatCodes: string[];
  limitations: string[];
}) {
  const hasDisclosure = caveats.length > 0 || caveatCodes.length > 0 || limitations.length > 0;

  if (!hasDisclosure) {
    return null;
  }

  return (
    <details style={styles.dataNotesDisclosure}>
      <summary style={styles.inlineSummary}>Data notes</summary>
      {caveats.length > 0 && (
        <ul style={styles.limitationList} aria-label="Selected-account data notes">
          {caveats.map((caveat) => (
            <li key={caveat.code} style={styles.limitationItem}>
              <strong>{caveat.title}</strong>: {caveat.message}
            </li>
          ))}
        </ul>
      )}
      {limitations.length > 0 && (
        <ul style={styles.limitationList} aria-label="Selected-account limitations">
          {limitations.map((limitation, i) => (
            <li key={`${limitation}-${i}`} style={styles.limitationItem}>{limitation}</li>
          ))}
        </ul>
      )}
      {caveatCodes.length > 0 && (
        <details style={styles.technicalDetails}>
          <summary style={styles.technicalSummary}>Technical codes</summary>
          <ul style={styles.caveatList} aria-label="Technical readiness codes">
            {caveatCodes.map((c) => (
              <li key={c} style={styles.caveatItem}>{c}</li>
            ))}
          </ul>
        </details>
      )}
    </details>
  );
}

function primaryScopeRole(roles: AccountScopeRole[]): AccountScopeRole | null {
  if (roles.includes("review_account")) return "review_account";
  if (roles.includes("included_in_scope")) return "included_in_scope";
  if (roles.includes("excluded_from_scope")) return "excluded_from_scope";
  return null;
}

function roleColor(tone: MpTone): string {
  switch (tone) {
    case "accent": return "var(--mp-accent)";
    case "live": return "var(--mp-live)";
    case "stale": return "var(--mp-stale)";
    case "block": return "var(--mp-block)";
    case "info": return "var(--mp-info)";
    case "mute":
    default: return "var(--mp-mute)";
  }
}

/**
 * A label worth rendering as a stat tile: non-null and not an em-dash/hyphen
 * placeholder. Unlike isMeaningfulDisplayLabel this KEEPS the self-describing
 * "…hidden" placeholders used in amounts_hidden mode, which are meant to show.
 */
function isPresentLabel(label: string | null | undefined): label is string {
  const t = label?.trim();
  return !!t && t !== "—" && t !== "-";
}

/**
 * Strip a redundant self-describing heading from a backend label so a stat tile
 * doesn't repeat its own title (e.g. "Total value $142,428.26" → "$142,428.26"
 * under the "TOTAL VALUE" tile). Case-insensitive; only leading whitespace / ":"
 * / "·" are trimmed after the prefix — never a sign — so negatives stay intact.
 * Falls back to the original label if stripping would leave nothing.
 */
function stripLabelPrefix(label: string | null | undefined, prefixes: string[]): string {
  const trimmed = label?.trim() ?? "";
  if (!trimmed) return "";
  const lower = trimmed.toLowerCase();
  for (const p of prefixes) {
    if (lower.startsWith(p.toLowerCase())) {
      const rest = trimmed.slice(p.length).replace(/^[\s:·]+/, "").trim();
      if (rest) return rest;
    }
  }
  return trimmed;
}

function isMeaningfulDisplayLabel(label: string | null | undefined): label is string {
  const normalized = label?.trim().toLowerCase();
  if (!normalized || normalized === "—" || normalized === "-") return false;
  return ![
    "not provided",
    "not available",
    "unavailable",
    "hidden",
    "limited",
    "not modeled",
  ].some((fragment) => normalized.includes(fragment));
}

function compactFreshnessLabel(label: string): string {
  const normalized = label.trim().toLowerCase();
  if (normalized === "cached") return "Available";
  return label;
}

function cleanMarketValueLabel(label: string | null): string | null {
  if (!label) return null;
  const trimmed = label.trim();
  for (const prefix of ["Market value: ", "Market value "]) {
    if (trimmed.startsWith(prefix)) return trimmed.slice(prefix.length);
  }
  return label;
}

function cleanBuyingPowerLabel(label: string): string {
  const trimmed = label.trim();
  for (const prefix of ["Buying power: ", "Buying power "]) {
    if (trimmed.startsWith(prefix)) return trimmed.slice(prefix.length);
  }
  return label;
}

function cleanCashPrefixLabel(label: string, prefix: string): string {
  const trimmed = label.trim();
  for (const candidate of [`${prefix}: `, `${prefix} `]) {
    if (trimmed.startsWith(candidate)) return trimmed.slice(candidate.length);
  }
  return label;
}

function cleanShareQuantityLabel(label: string): string {
  return label.replace(/\s+shares?$/i, "");
}

function cleanContractQuantityLabel(label: string): string {
  return label.replace(/\s+contracts?$/i, "");
}

/**
 * Read the gain/loss sign from a backend display label only — never by parsing
 * the numeric magnitude. Detection is purely glyph-based:
 *   - a "-"/Unicode-minus before any digit, or a parenthesised "($…)" → negative
 *   - an explicit leading "+" → positive
 *   - otherwise: positive iff a non-zero digit is present (gains arrive unsigned,
 *     e.g. "$403.33" / "4.98%"), so an unsigned non-zero gain reads green
 *   - all-zero ("$0.00" / "0.00%") or empty ("—") → neutral
 * Currency-prefixed negatives like "$-3,905.04" are caught (the minus precedes
 * the first digit). The presence/absence of the "-" glyph is also the non-color
 * cue, so color stays supplementary.
 */
function gainLossSign(label: string | null | undefined): "pos" | "neg" | "neutral" {
  const trimmed = label?.trim();
  if (!trimmed || trimmed === "—" || trimmed === "-") return "neutral";
  if (trimmed.startsWith("(")) return "neg"; // accounting-style negative, e.g. ($1,234)
  for (const ch of trimmed) {
    if (ch === "+") return "pos";
    if (ch === "-" || ch === "−") return "neg";
    if (ch >= "0" && ch <= "9") break; // a value digit reached before any sign glyph
  }
  return /[1-9]/.test(trimmed) ? "pos" : "neutral"; // unsigned non-zero magnitude → gain
}

function gainLossCellStyle(label: string | null): CSSProperties {
  const sign = gainLossSign(label);
  if (sign === "pos") return { ...styles.tdMono, color: "var(--mp-live)", fontWeight: 700 };
  if (sign === "neg") return { ...styles.tdMono, color: "var(--mp-block)", fontWeight: 700 };
  return styles.tdMono;
}

function tableMinWidth(columnCount: number): number {
  return Math.max(560, columnCount * 112);
}

function CaveatDisclosure({ codes }: { codes: string[] }) {
  return (
    <details style={styles.caveatDetails}>
      <summary style={styles.caveatSummary}>
        <MpIcon name="alert" size={12} />
        <span style={styles.caveatSummaryText}>
          {codes.length} {codes.length === 1 ? "data note" : "data notes"}
        </span>
      </summary>
      <ul style={styles.caveatList} aria-label="Account-details data notes">
        {codes.map((c) => (
          <li key={c} style={styles.caveatItem}>{c}</li>
        ))}
      </ul>
    </details>
  );
}

function formatGeneratedAt(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(parsed);
}

/* ── Safety strip ──────────────────────────────────────────────────────── */

function AccountDetailsSafetyStrip() {
  return (
    <SafetyStrip items={[
      "Read-only account context",
      "No broker actions from this app",
      "Backend-owned display labels",
      "Data freshness may affect review quality",
    ]} />
  );
}

/* ── Styles ───────────────────────────────────────────────────────────── */

const styles: Record<string, CSSProperties> = {
  page: {
    display: "flex", flexDirection: "column", gap: "var(--space-5)",
    maxWidth: 1440, margin: "0 auto", color: "var(--mp-ink)",
    fontFamily: "\"Hanken Grotesk\", var(--mp-font-sans)",
  },

  /* Scope panel */
  scopeHeadline: { margin: 0, fontSize: "var(--font-size-md)", fontWeight: 600, color: "var(--mp-ink)", lineHeight: 1.3 },
  scopeChips: { display: "flex", alignItems: "baseline", gap: "var(--space-3)", flexWrap: "wrap", paddingTop: "var(--space-2)" },
  scopeChipsLabel: {
    fontSize: "var(--font-size-xs)", color: "var(--mp-mute)",
    textTransform: "uppercase", letterSpacing: "0.06em", fontWeight: 600, minWidth: 64,
  },
  chipRow: { display: "flex", gap: "var(--space-1)", flexWrap: "wrap" },

  /* Account workspace */
  workspace: {
    display: "flex", alignItems: "stretch", gap: 0, minWidth: 0,
    border: "1px solid var(--mp-rule)", borderRadius: 4,
    backgroundColor: "var(--mp-card)", boxShadow: "var(--mp-shadow-sm)",
    overflow: "clip",
  },
  selectorPane: {
    flex: "0 0 280px", minWidth: 236, display: "flex", flexDirection: "column", gap: "var(--space-3)",
    alignSelf: "stretch", padding: "var(--space-4)", borderRight: "1px solid var(--mp-rule)",
    backgroundColor: "var(--mp-card)", position: "sticky", top: 0,
    maxHeight: "calc(100vh - var(--space-6))", overflow: "hidden",
  },
  detailPane: { flex: "1 1 720px", minWidth: 0, backgroundColor: "var(--mp-paper)", display: "flex", flexDirection: "column" },
  detailCanvas: {
    display: "flex", flexDirection: "column", gap: "var(--space-5)",
    padding: "var(--space-6)", minWidth: 0,
  },
  workspaceTopBar: {
    position: "sticky", top: 0, zIndex: 5,
    minHeight: 64, display: "flex", alignItems: "center", justifyContent: "space-between",
    gap: "var(--space-4)", padding: "0 var(--space-5)",
    borderBottom: "1px solid var(--mp-rule)", backgroundColor: "var(--mp-card)",
  },
  workspaceTabs: { display: "flex", alignItems: "center", gap: "var(--space-5)", minWidth: 0, overflowX: "auto" },
  workspaceTab: {
    position: "relative", display: "inline-flex", alignItems: "center", minHeight: 64,
    padding: 0, border: 0, backgroundColor: "transparent", cursor: "pointer",
    color: "var(--mp-mute)", textDecoration: "none", fontFamily: "\"Hanken Grotesk\", var(--mp-font-sans)",
    fontSize: "var(--font-size-sm)", fontWeight: 700, whiteSpace: "nowrap",
  },
  workspaceTabActive: { color: "var(--mp-accent)", cursor: "default" },
  workspaceTabDisabled: {
    color: "var(--mp-mute)", cursor: "default", gap: 6,
  },
  soonTag: {
    fontSize: 10, fontWeight: 700, letterSpacing: "0.04em", textTransform: "uppercase",
    color: "var(--mp-mute)", border: "1px solid var(--mp-rule)", borderRadius: 999,
    padding: "1px 6px", lineHeight: 1.4,
  },
  workspaceActions: { display: "flex", alignItems: "center", gap: "var(--space-3)", flexShrink: 0 },
  topRefreshGroup: { display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 3, minWidth: 0 },
  topRefreshBtn: {
    display: "inline-flex", alignItems: "center", gap: 7,
    minHeight: 32, padding: "5px 11px", borderRadius: 4,
    border: "1px solid var(--mp-accent)", backgroundColor: "var(--mp-accent-soft)",
    color: "var(--mp-accent)", fontFamily: "\"Hanken Grotesk\", var(--mp-font-sans)",
    fontSize: "var(--font-size-xs)", fontWeight: 800, whiteSpace: "nowrap",
  },
  profileAvatar: {
    width: 34, height: 34, borderRadius: "50%",
    display: "inline-flex", alignItems: "center", justifyContent: "center",
    color: "var(--mp-accent)", backgroundColor: "var(--mp-card-2)",
    border: "1px solid var(--mp-rule)",
  },
  selectorHead: { display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "var(--space-3)" },
  sectionLabel: {
    fontSize: "var(--font-size-xs)", color: "var(--mp-mute)",
    textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 600,
  },
  sectionCount: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", fontFamily: "var(--mp-font-mono)" },
  selectorSub: { margin: "2px 0 0", color: "var(--mp-mute)", fontSize: "var(--font-size-xs)", lineHeight: 1.35 },
  accountList: { display: "flex", flexDirection: "column", gap: 7, minWidth: 0, overflowY: "auto", paddingRight: 2 },
  selectorButton: {
    position: "relative", display: "flex", gap: "var(--space-2)", width: "100%", textAlign: "left",
    padding: "11px 12px 11px 13px", color: "var(--mp-ink)", backgroundColor: "var(--mp-card)",
    borderWidth: 1, borderStyle: "solid", borderColor: "var(--mp-rule)",
    borderRadius: 4, boxShadow: "none",
    cursor: "pointer", overflow: "hidden", minWidth: 0,
  },
  selectorButtonSelected: {
    backgroundColor: "var(--mp-accent-soft)",
    borderColor: "color-mix(in srgb, var(--mp-accent) 35%, var(--mp-rule))",
    boxShadow: "inset 0 0 0 1px color-mix(in srgb, var(--mp-accent) 24%, transparent)",
  },
  selectorStripe: {
    position: "absolute", left: 0, top: 0, bottom: 0, width: 4, borderRadius: "4px 0 0 4px",
  },
  selectorBody: { display: "flex", flexDirection: "column", gap: 3, minWidth: 0, width: "100%", paddingLeft: "var(--space-1)" },
  selectorTitleRow: { display: "flex", alignItems: "center", justifyContent: "space-between", gap: "var(--space-2)", minWidth: 0 },
  selectorTitle: { fontSize: "var(--font-size-sm)", fontWeight: 700, color: "var(--mp-ink)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" },
  selectorKind: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" },
  selectorMeta: { display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap", fontSize: "var(--font-size-xs)", color: "var(--mp-ink-2)" },
  selectorBottom: { display: "flex", alignItems: "center", justifyContent: "space-between", gap: "var(--space-2)", paddingTop: 0, minWidth: 0 },
  selectorValue: { fontSize: "var(--font-size-xs)", fontWeight: 700, color: "var(--mp-ink-2)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", minWidth: 0 },

  detailArticle: {
    display: "flex", flexDirection: "column", gap: "var(--space-4)", minWidth: 0,
    padding: "var(--space-5)", border: "1px solid var(--mp-rule)",
    borderRadius: 4, backgroundColor: "var(--mp-card)",
  },
  detailHeader: { display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "var(--space-4)", flexWrap: "wrap" },
  detailTitleBlock: { minWidth: 0 },
  detailEyebrow: {
    display: "block", marginBottom: "var(--space-1)",
    fontSize: "var(--font-size-xs)", color: "var(--mp-mute)",
    textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 800,
  },
  detailTitle: {
    margin: 0, fontSize: 36, fontWeight: 800, color: "var(--mp-ink)",
    lineHeight: 1.05, minWidth: 0, overflowWrap: "anywhere",
    fontFamily: "\"Hanken Grotesk\", var(--mp-font-sans)",
  },
  detailKind: { margin: "var(--space-1) 0 0", color: "var(--mp-mute)", fontSize: "var(--font-size-sm)" },

  /* ── Display-name (nickname) editor — P32A-T5 ── */
  nicknameTitleRow: { display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap", minWidth: 0 },
  nicknameEditBtn: {
    position: "relative", display: "inline-flex", alignItems: "center", justifyContent: "center",
    flexShrink: 0, width: 30, height: 30, padding: 0,
    border: "1px solid transparent", borderRadius: 4,
    backgroundColor: "transparent", color: "var(--mp-mute)", cursor: "pointer",
    opacity: 0.72,
  },
  nicknameEditor: { display: "flex", flexDirection: "column", gap: "var(--space-1)", minWidth: 0, maxWidth: 640 },
  nicknameInputRow: { display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap", minWidth: 0 },
  nicknameInput: {
    flex: "1 1 200px", minWidth: 0,
    padding: "7px 10px", minHeight: 32,
    border: "1px solid var(--mp-rule)", borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--mp-paper-2)", color: "var(--mp-ink)",
    fontFamily: "var(--mp-font-sans)", fontSize: "var(--font-size-sm)",
    boxSizing: "border-box",
  },
  nicknameSave: {
    display: "inline-flex", alignItems: "center", minHeight: 32, padding: "5px 13px",
    border: "1px solid var(--mp-accent)", borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--mp-accent)", color: "var(--mp-paper)",
    fontFamily: "var(--mp-font-sans)", fontSize: "var(--font-size-xs)", fontWeight: 700,
    cursor: "pointer", whiteSpace: "nowrap",
  },
  nicknameGhost: {
    display: "inline-flex", alignItems: "center", minHeight: 32, padding: "5px 10px",
    border: "1px solid var(--mp-rule)", borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--mp-paper)", color: "var(--mp-ink-2)",
    fontFamily: "var(--mp-font-sans)", fontSize: "var(--font-size-xs)", fontWeight: 600,
    cursor: "pointer", whiteSpace: "nowrap",
  },
  nicknameError: {
    display: "inline-flex", alignItems: "center", margin: 0,
    color: "var(--mp-block)", fontSize: "var(--font-size-xs)", fontWeight: 600, lineHeight: 1.4,
  },
  nicknameHint: { margin: 0, color: "var(--mp-mute)", fontSize: "var(--font-size-xs)", lineHeight: 1.4 },
  roleBadges: { display: "flex", gap: "var(--space-1)", flexWrap: "wrap", justifyContent: "flex-end" },

  /* Selected-account refresh control (P27B-T19). Kept quiet beside the
     title block — same icon+text idiom as Economic awareness. */
  refreshGroup: {
    display: "flex", flexDirection: "column", alignItems: "flex-end",
    gap: 4, minWidth: 0, flexShrink: 0,
  },
  refreshBtn: {
    display: "inline-flex", alignItems: "center", gap: 6,
    minHeight: 28, padding: "4px 10px",
    borderRadius: "var(--radius-sm)",
    border: "1px solid var(--mp-rule)",
    backgroundColor: "var(--mp-paper)",
    color: "var(--mp-ink-2)",
    fontFamily: "var(--mp-font-sans)",
    fontSize: "var(--font-size-xs)",
    fontWeight: 600,
    whiteSpace: "nowrap",
  },
  refreshIconSpin: { animation: "mp-spin 0.95s linear infinite" },
  refreshStatus: {
    display: "inline-flex", alignItems: "center", gap: 5,
    fontSize: "var(--font-size-xs)", lineHeight: 1.4, maxWidth: 260,
  },

  metaRow: { display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap", fontSize: "var(--font-size-xs)", color: "var(--mp-ink-2)" },
  metaItem: { color: "var(--mp-ink-2)" },
  metaDot: { color: "var(--mp-mute)" },
  detailRefreshNotice: {
    display: "inline-flex", alignItems: "center", gap: 6, alignSelf: "flex-start",
    padding: "4px 8px", borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--mp-card-2)",
    color: "var(--mp-mute)", fontSize: "var(--font-size-xs)", lineHeight: 1.4,
  },

  /* Account summary band — promoted stat tiles + cash detail + freshness line. */
  summarySection: { display: "flex", flexDirection: "column", gap: "var(--space-3)", minWidth: 0 },
  summaryBand: {
    display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(132px, 1fr))",
    gap: "var(--space-3)", minWidth: 0,
  },
  statTile: {
    minWidth: 0, display: "flex", flexDirection: "column", gap: 5,
    padding: "13px 14px", border: "1px solid var(--mp-rule)", borderRadius: 4,
    backgroundColor: "var(--mp-card)",
  },
  statTilePrimary: {
    borderLeft: "4px solid var(--mp-accent)",
    borderColor: "color-mix(in srgb, var(--mp-accent) 25%, var(--mp-rule))",
    backgroundColor: "var(--mp-accent-soft)",
  },
  statTileLabel: {
    fontSize: "var(--font-size-xs)", color: "var(--mp-mute)",
    textTransform: "uppercase", letterSpacing: "0.06em", fontWeight: 700,
  },
  statTileValue: { fontSize: "var(--font-size-md)", color: "var(--mp-ink)", fontWeight: 800, overflowWrap: "anywhere", lineHeight: 1.2 },
  statTileValuePrimary: { fontSize: "var(--font-size-lg)", color: "var(--mp-ink)", fontWeight: 900, overflowWrap: "anywhere", lineHeight: 1.15 },
  cashDetail: { display: "flex", flexDirection: "column", gap: 2, minWidth: 0 },
  cashDetailLine: {
    margin: 0, display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap",
    color: "var(--mp-mute)", fontSize: "var(--font-size-xs)", lineHeight: 1.5,
  },
  freshnessLine: {
    display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap",
    color: "var(--mp-mute)", fontSize: "var(--font-size-xs)",
  },
  freshnessScope: { display: "inline-flex", alignItems: "center", gap: 6, minWidth: 0 },
  statusDot: { width: 7, height: 7, borderRadius: "50%", flexShrink: 0 },
  quietText: { color: "var(--mp-mute)", fontSize: "var(--font-size-xs)", lineHeight: 1.5 },
  readinessSection: {
    display: "flex", flexDirection: "column", gap: "var(--space-3)", minWidth: 0,
    padding: "var(--space-4)", border: "1px solid var(--mp-rule)",
    borderRadius: 4, backgroundColor: "var(--mp-card)",
  },
  readinessSectionHeader: { display: "flex", alignItems: "center", justifyContent: "space-between", gap: "var(--space-3)", flexWrap: "wrap" },
  readinessSectionTitle: {
    fontSize: "var(--font-size-xs)", color: "var(--mp-mute)",
    textTransform: "uppercase", letterSpacing: "0.06em", fontWeight: 700,
  },
  readinessNoteText: { margin: 0, color: "var(--mp-ink-2)", fontSize: "var(--font-size-xs)", lineHeight: 1.55 },
  inlineSummary: {
    display: "inline-flex", alignItems: "center", gap: 5, cursor: "pointer",
    color: "var(--mp-mute)", fontWeight: 700, listStyle: "none",
  },
  technicalDetails: { marginTop: "var(--space-2)", color: "var(--mp-mute)", fontSize: "var(--font-size-xs)" },
  technicalSummary: { cursor: "pointer", color: "var(--mp-mute)", fontWeight: 700 },
  dataNotesDisclosure: {
    color: "var(--mp-mute)", fontSize: "var(--font-size-xs)", minWidth: 0,
    padding: "var(--space-2) var(--space-3)", border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)", backgroundColor: "color-mix(in srgb, var(--mp-card-2) 50%, transparent)",
  },
  rowsStack: { display: "flex", flexDirection: "column", gap: "var(--space-3)", minWidth: 0 },
  rowSection: {
    display: "flex", flexDirection: "column", gap: "var(--space-2)", minWidth: 0,
    border: 0, borderRadius: 4,
    backgroundColor: "transparent", padding: "var(--space-2) 0 0",
  },
  rowSectionHeader: { display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: "var(--space-3)" },
  rowSectionTitle: {
    fontSize: "var(--font-size-xs)", color: "var(--mp-mute)",
    textTransform: "uppercase", letterSpacing: "0.06em", fontWeight: 700,
  },
  rowSectionCount: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)" },
  tableScroller: { overflowX: "auto", minWidth: 0, borderRadius: 4 },
  dataTable: { width: "100%", minWidth: 760, borderCollapse: "collapse", fontSize: "var(--font-size-xs)" },
  expandableTableRow: { cursor: "pointer" },
  th: {
    padding: "9px 14px", textAlign: "right", color: "var(--mp-mute)",
    borderBottom: "1px solid var(--mp-rule-2)", fontWeight: 700,
    textTransform: "uppercase", letterSpacing: "0.05em", whiteSpace: "nowrap",
  },
  thLeft: {
    padding: "9px 14px", textAlign: "left", color: "var(--mp-mute)",
    borderBottom: "1px solid var(--mp-rule-2)", fontWeight: 700,
    textTransform: "uppercase", letterSpacing: "0.05em", whiteSpace: "nowrap",
  },
  thStickyLeft: {
    width: 144, minWidth: 144, maxWidth: 144,
    padding: "9px 14px", textAlign: "left", color: "var(--mp-mute)",
    borderBottom: "1px solid var(--mp-rule-2)", fontWeight: 700,
    textTransform: "uppercase", letterSpacing: "0.05em", whiteSpace: "nowrap",
  },
  symbolStack: { display: "flex", flexDirection: "column", gap: 2, minWidth: 0, maxWidth: 116 },
  symbolMain: { display: "inline-flex", alignItems: "center", gap: 6, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", fontWeight: 700 },
  symbolSub: { color: "var(--mp-mute)", fontSize: "var(--font-size-xs)", fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" },
  td: { padding: "9px 14px", color: "var(--mp-ink-2)", borderBottom: "1px solid var(--mp-rule)", verticalAlign: "middle" },
  tdSticky: {
    width: 144, minWidth: 144, maxWidth: 144,
    padding: "9px 14px", color: "var(--mp-ink-2)", borderBottom: "1px solid var(--mp-rule)",
    verticalAlign: "middle",
  },
  tdStickyStrong: {
    width: 144, minWidth: 144, maxWidth: 144,
    padding: "9px 14px", color: "var(--mp-ink)", borderBottom: "1px solid var(--mp-rule)",
    verticalAlign: "middle", fontWeight: 700,
  },
  tdMono: {
    padding: "9px 14px", color: "var(--mp-ink)", borderBottom: "1px solid var(--mp-rule)",
    verticalAlign: "middle", fontFamily: "var(--mp-font-mono)", fontVariantNumeric: "tabular-nums",
    whiteSpace: "nowrap", textAlign: "right",
  },
  tdStickyMuted: {
    width: 144, minWidth: 144, maxWidth: 144,
    padding: "9px 14px", color: "var(--mp-mute)", borderBottom: "1px solid var(--mp-rule)",
    verticalAlign: "middle",
  },
  tdLotCell: {
    padding: "8px", color: "var(--mp-ink-2)", borderBottom: "1px solid var(--mp-rule)",
    verticalAlign: "top", backgroundColor: "color-mix(in srgb, var(--mp-card) 62%, transparent)",
  },
  expandedRowPanel: {
    display: "flex", flexDirection: "column", gap: "var(--space-3)",
    border: "1px solid var(--mp-rule)", borderRadius: "var(--radius-sm)",
    backgroundColor: "var(--mp-card)", padding: "var(--space-3)",
  },
  expandedMeta: {
    margin: 0, display: "flex", alignItems: "baseline", flexWrap: "wrap",
    gap: "var(--space-2)", lineHeight: 1.45, minWidth: 0,
  },
  expandedMetaPrimary: {
    fontSize: "var(--font-size-sm)", fontWeight: 700, color: "var(--mp-ink)",
    overflowWrap: "anywhere",
  },
  expandedMetaSecondary: { fontSize: "var(--font-size-xs)", color: "var(--mp-mute)" },
  lotBlock: { display: "flex", flexDirection: "column", gap: "var(--space-2)", minWidth: 0 },
  lotBlockHeader: { display: "flex", alignItems: "center", gap: "var(--space-2)", color: "var(--mp-mute)" },
  lotBlockTitle: {
    fontSize: "var(--font-size-xs)", color: "var(--mp-mute)",
    textTransform: "uppercase", letterSpacing: "0.06em", fontWeight: 700,
  },
  lotCount: {
    color: "var(--mp-mute)", border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)", padding: "0 5px", fontSize: "var(--font-size-xs)",
  },
  lotNote: { margin: "var(--space-2) 0", color: "var(--mp-mute)", fontSize: "var(--font-size-xs)", lineHeight: 1.45 },
  lotTable: { width: "100%", borderCollapse: "collapse", fontSize: "var(--font-size-xs)" },

  /* Provenance + caveats */
  provenance: {
    display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap",
    fontSize: "var(--font-size-xs)", color: "var(--mp-mute)",
  },
  provText: { color: "var(--mp-mute)" },
  provDot: { color: "var(--mp-mute)" },
  caveatDetails: { color: "var(--mp-mute)", fontSize: "var(--font-size-xs)" },
  caveatSummary: {
    display: "inline-flex", alignItems: "center", gap: 5, cursor: "pointer",
    color: "var(--mp-mute)", listStyle: "none",
  },
  caveatSummaryText: { color: "var(--mp-mute)", fontWeight: 600 },
  caveatList: { listStyle: "none", margin: "var(--space-2) 0 0", padding: 0, display: "flex", flexWrap: "wrap", gap: "var(--space-1)" },
  caveatItem: {
    fontSize: "var(--font-size-xs)", color: "var(--mp-mute)",
    fontFamily: "var(--mp-font-mono)", border: "1px solid var(--mp-rule)",
    borderRadius: "var(--radius-sm)", padding: "1px 6px",
  },
  limitationList: { margin: "var(--space-2) 0 0", paddingLeft: "var(--space-4)", color: "var(--mp-mute)", fontSize: "var(--font-size-xs)" },
  limitationItem: { marginTop: 3, lineHeight: 1.5 },
};
