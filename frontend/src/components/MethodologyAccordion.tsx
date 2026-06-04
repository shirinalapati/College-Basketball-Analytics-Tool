import { ReactNode, useEffect, useState } from 'react';

interface Props {
  title: string;
  children: ReactNode;
  defaultOpen?: boolean;
  /** Primary anchor on the accordion card (optional) */
  id?: string;
  /** Additional /methodology#ids that open this accordion and scroll into view */
  hashTargets?: string[];
}

export function MethodologyAccordion({
  title,
  children,
  defaultOpen = false,
  id,
  hashTargets,
}: Props) {
  const [open, setOpen] = useState(defaultOpen);
  const targets = [...new Set([...(id ? [id] : []), ...(hashTargets ?? [])])];

  useEffect(() => {
    if (!targets.length) return;
    const openForHash = () => {
      const hash = window.location.hash.slice(1);
      if (hash && targets.includes(hash)) setOpen(true);
    };
    openForHash();
    window.addEventListener('hashchange', openForHash);
    return () => window.removeEventListener('hashchange', openForHash);
  }, [targets.join('|')]);

  // Scroll after accordion content mounts (nested #ids are not in DOM while collapsed)
  useEffect(() => {
    if (!open || !targets.length) return;
    const hash = window.location.hash.slice(1);
    if (!hash || !targets.includes(hash)) return;
    const id = window.setTimeout(() => {
      document.getElementById(hash)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 0);
    return () => clearTimeout(id);
  }, [open, targets.join('|')]);

  return (
    <div id={id} className="card overflow-hidden scroll-mt-24">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between gap-3 text-left py-1"
        aria-expanded={open}
      >
        <h3 className="font-display text-lg font-semibold text-illini-orange">{title}</h3>
        <span
          className={`text-gray-500 text-sm shrink-0 transition-transform ${open ? 'rotate-180' : ''}`}
          aria-hidden
        >
          ▼
        </span>
      </button>
      {open ? (
        <div className="mt-4 pt-4 border-t border-surface-border space-y-4 text-sm text-gray-300 leading-relaxed">
          {children}
        </div>
      ) : null}
    </div>
  );
}
