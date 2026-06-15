/**
 * ReportProse — render pre-sanitized report narrative as readable prose.
 *
 * The Agent Team `summary_markdown` / `final_synthesis_markdown` are validated
 * and sanitized server-side (no advice/execution wording, no private values, no
 * generated metrics). This renderer treats the text as plain prose: it splits
 * blank-line-separated paragraphs and simple `- `/`* `/`• ` bullet lines. It
 * never injects HTML (no dangerouslySetInnerHTML), so React escapes all text.
 */
interface ReportProseProps {
  text: string;
}

type Block =
  | { kind: "p"; text: string }
  | { kind: "ul"; items: string[] };

function parseBlocks(text: string): Block[] {
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  const blocks: Block[] = [];
  let paragraph: string[] = [];
  let bullets: string[] = [];

  const flushParagraph = () => {
    if (paragraph.length > 0) {
      blocks.push({ kind: "p", text: paragraph.join(" ").trim() });
      paragraph = [];
    }
  };
  const flushBullets = () => {
    if (bullets.length > 0) {
      blocks.push({ kind: "ul", items: bullets });
      bullets = [];
    }
  };

  for (const raw of lines) {
    const line = raw.trim();
    if (line === "") {
      flushParagraph();
      flushBullets();
      continue;
    }
    const bulletMatch = line.match(/^([-*•])\s+(.*)$/);
    if (bulletMatch) {
      flushParagraph();
      bullets.push(bulletMatch[2].trim());
      continue;
    }
    flushBullets();
    paragraph.push(line);
  }
  flushParagraph();
  flushBullets();
  return blocks;
}

export default function ReportProse({ text }: ReportProseProps) {
  const blocks = parseBlocks(text);
  if (blocks.length === 0) return null;

  return (
    <div style={styles.prose}>
      {blocks.map((block, index) =>
        block.kind === "p" ? (
          <p key={index} style={styles.paragraph}>
            {block.text}
          </p>
        ) : (
          <ul key={index} style={styles.list}>
            {block.items.map((item, itemIndex) => (
              <li key={itemIndex} style={styles.listItem}>
                {item}
              </li>
            ))}
          </ul>
        ),
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  prose: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-3)",
    minWidth: 0,
  },
  paragraph: {
    margin: 0,
    color: "var(--mp-ink-2)",
    fontSize: "var(--font-size-base)",
    lineHeight: 1.7,
    overflowWrap: "anywhere",
  },
  list: {
    margin: 0,
    paddingLeft: "var(--space-5)",
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-2)",
  },
  listItem: {
    color: "var(--mp-ink-2)",
    fontSize: "var(--font-size-base)",
    lineHeight: 1.6,
    overflowWrap: "anywhere",
  },
};
