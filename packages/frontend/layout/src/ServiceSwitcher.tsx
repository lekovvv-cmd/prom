import { Check, ChevronDown } from "lucide-react";
import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { Link, useLocation } from "react-router-dom";

export type ServiceNavigationItem = {
  id: string;
  title: string;
  basePath: string;
  routePrefixes: readonly string[];
};

const ServiceNavigationContext = createContext<
  readonly ServiceNavigationItem[]
>([]);
export function ServiceNavigationProvider({
  services,
  children,
}: {
  services: readonly ServiceNavigationItem[];
  children: ReactNode;
}) {
  return (
    <ServiceNavigationContext.Provider value={services}>
      {children}
    </ServiceNavigationContext.Provider>
  );
}

export function ServiceSwitcher({
  services,
}: {
  services: readonly ServiceNavigationItem[];
}) {
  const { pathname } = useLocation();
  const [open, setOpen] = useState(false);
  const container = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const current = services
    .flatMap((service) =>
      service.routePrefixes.map((prefix) => ({ service, prefix })),
    )
    .filter(
      ({ prefix }) => pathname === prefix || pathname.startsWith(`${prefix}/`),
    )
    .sort((a, b) => b.prefix.length - a.prefix.length)[0]?.service;

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: PointerEvent) => {
      if (!container.current?.contains(event.target as Node)) setOpen(false);
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false);
        trigger.current?.focus();
      }
    };
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  return (
    <div
      className="service-switcher"
      ref={container}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false);
      }}
    >
      <button
        ref={trigger}
        type="button"
        className="service-switcher-trigger"
        aria-label={`Сервисы: ${current?.title ?? "Все сервисы"}`}
        aria-expanded={open}
        aria-controls="service-navigation"
        onClick={() => setOpen((value) => !value)}
      >
        <span>{current?.title ?? "Сервисы"}</span>
        <ChevronDown size={16} aria-hidden="true" />
      </button>
      {open && (
        <nav
          id="service-navigation"
          className="service-switcher-list"
          aria-label="Сервисы"
        >
          <span className="service-switcher-label">Сервисы PROM</span>
          {services.map((service) => (
            <Link
              key={service.id}
              to={service.basePath}
              aria-current={current?.id === service.id ? "true" : undefined}
              onClick={() => {
                setOpen(false);
                trigger.current?.focus();
              }}
            >
              <span>{service.title}</span>
              {current?.id === service.id && (
                <Check size={16} aria-hidden="true" />
              )}
            </Link>
          ))}
          <Link
            className="service-switcher-all"
            to="/"
            onClick={() => {
              setOpen(false);
              trigger.current?.focus();
            }}
          >
            Все сервисы
          </Link>
        </nav>
      )}
    </div>
  );
}

export function useServiceNavigation() {
  return useContext(ServiceNavigationContext);
}
