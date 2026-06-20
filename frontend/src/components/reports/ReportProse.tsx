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
  /** Render in the serif display face for the editorial "memo" feel (used by
   *  the final synthesis and the primary role narratives). */
  display?: boolean;
  /** Override the body text color (e.g. stronger ink for the synthesis lede). */
  color?: string;
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

export default function ReportProse({ text, display = false, color }: ReportProseProps) {
  const blocks = parseBlocks(text);
  if (blocks.length === 0) return null;

  const paraStyle: React.CSSProperties = {
    ...styles.paragraph,
    ...(display ? styles.paragraphDisplay : undefined),
    ...(color ? { color } : undefined),
  };
  const itemStyle: React.CSSProperties = {
    ...styles.listItem,
    ...(display ? styles.paragraphDisplay : undefined),
    ...(color ? { color } : undefined),
  };

  return (
    <div style={styles.prose}>
      {blocks.map((block, index) =>
        block.kind === "p" ? (
          <p key={index} style={paraStyle}>
            {block.text}
          </p>
        ) : (
          <ul key={index} style={styles.list}>
            {block.items.map((item, itemIndex) => (
              <li key={itemIndex} style={itemStyle}>
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
  paragraphDisplay: {
    fontFamily: "var(--mp-font-display)",
    fontSize: "var(--font-size-md)",
    lineHeight: 1.62,
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
