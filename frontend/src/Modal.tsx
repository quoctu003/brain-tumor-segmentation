import { useEffect, useRef, type ReactNode } from "react";

export default function Modal({
  children,
  labelledBy,
  onClose,
  busy = false,
  className = "",
}: {
  children: ReactNode;
  labelledBy: string;
  onClose: () => void;
  busy?: boolean;
  className?: string;
}) {
  const dialog = useRef<HTMLElement>(null);
  const previousFocus = useRef(
    document.activeElement instanceof HTMLElement
      ? document.activeElement
      : null,
  );
  const close = useRef(onClose);
  const locked = useRef(busy);
  close.current = onClose;
  locked.current = busy;
  useEffect(() => {
    const previous = previousFocus.current;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const focusable = () =>
      Array.from(
        dialog.current?.querySelectorAll<HTMLElement>(
          'button:not(:disabled), a[href], input:not(:disabled), [tabindex="0"]',
        ) ?? [],
      );
    if (!dialog.current?.contains(document.activeElement))
      (focusable()[0] ?? dialog.current)?.focus();
    function keydown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        if (!locked.current) close.current();
      }
      if (event.key !== "Tab") return;
      const items = focusable();
      const first = items[0],
        last = items.at(-1);
      if (!first) {
        event.preventDefault();
        dialog.current?.focus();
        return;
      }
      if (
        event.shiftKey &&
        (document.activeElement === first ||
          document.activeElement === dialog.current)
      ) {
        event.preventDefault();
        last?.focus();
      } else if (
        !event.shiftKey &&
        (document.activeElement === last ||
          document.activeElement === dialog.current)
      ) {
        event.preventDefault();
        first.focus();
      }
    }
    document.addEventListener("keydown", keydown);
    return () => {
      document.removeEventListener("keydown", keydown);
      document.body.style.overflow = overflow;
      previous?.focus();
    };
  }, []);
  return (
    <div className="modal-backdrop">
      <section
        ref={dialog}
        className={`modal ${className}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelledBy}
        aria-busy={busy}
        tabIndex={-1}
      >
        {children}
      </section>
    </div>
  );
}
