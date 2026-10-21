import { LogIn } from "lucide-react";
import { useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../../index";
import { pilotLogin } from "../api/authApi";

const accounts = [
  {
    title: "Администраторы PROM",
    role: "Администратор",
    prefix: "admin",
    count: 2,
  },
  {
    title: "Проектные менеджеры ТюмГУ",
    role: "Менеджер проектов",
    prefix: "pm",
    count: 5,
  },
  {
    title: "Сотрудники ТюмГУ",
    role: "Сотрудник",
    prefix: "employee",
    count: 5,
  },
];

function safeNext(value: string | null): string {
  return value &&
    value.startsWith("/") &&
    !value.startsWith("//") &&
    !value.startsWith("/login")
    ? value
    : "/projects";
}

export function PilotAccountSelector() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const requestInFlight = useRef(false);
  const [pendingEmail, setPendingEmail] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function chooseAccount(email: string) {
    if (requestInFlight.current) return;
    requestInFlight.current = true;
    setPendingEmail(email);
    setError(null);
    try {
      const session = await pilotLogin(email);
      login(session);
      navigate(safeNext(new URLSearchParams(location.search).get("next")), {
        replace: true,
      });
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Не удалось войти. Попробуйте ещё раз.",
      );
      requestInFlight.current = false;
      setPendingEmail(null);
    }
  }

  return (
    <section
      className="form-panel login-form pilot-login"
      aria-label="Выбор пилотной учётной записи"
      aria-busy={pendingEmail !== null}
    >
      <div className="login-form-heading">
        <h2>Выберите учётную запись</h2>
        <p>Для входа нажмите на карточку. Коды и пароли не нужны.</p>
      </div>
      {accounts.map((group) => (
        <section
          className="pilot-account-group"
          key={group.prefix}
          aria-labelledby={`pilot-${group.prefix}`}
        >
          <h3 id={`pilot-${group.prefix}`}>{group.title}</h3>
          <div className="pilot-account-grid">
            {Array.from({ length: group.count }, (_, index) => {
              const email = `pilot.${group.prefix}${String(index + 1).padStart(2, "0")}@utmn.ru`;
              const isPending = pendingEmail === email;
              return (
                <button
                  type="button"
                  className="role-option pilot-account-option"
                  key={email}
                  disabled={pendingEmail !== null}
                  onClick={() => void chooseAccount(email)}
                  aria-label={`${group.role} ${index + 1}`}
                >
                  <span className="role-option-title">
                    {isPending ? "Входим…" : `${group.role} ${index + 1}`}
                  </span>
                  <span className="role-option-email">{email}</span>
                  {isPending && (
                    <span className="pilot-account-loading">
                      <LogIn size={16} aria-hidden="true" /> Создаём сессию
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </section>
      ))}
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}
