import { Header } from "@prom/layout";
import { LoginForm } from "@prom/auth/login";
import { Link } from "react-router-dom";

export function LoginPage() {
  const isPilot = import.meta.env.VITE_PLATFORM_ENVIRONMENT === "pilot";
  return (
    <>
      <Header />
      <main className="login-page">
        <section className="login-shell" aria-labelledby="login-title">
          <div className="login-copy">
            <h1 id="login-title">Вход в PROM</h1>
            <p>
              {isPilot
                ? "Пилотное тестирование PROM для сотрудников ТюмГУ."
                : "Выберите демонстрационную роль или введите корпоративный адрес электронной почты."}
            </p>
            <Link className="button button-secondary" to="/">
              {isPilot ? "Перейти в PROM" : "Выбрать сервис"}
            </Link>
          </div>
          <LoginForm />
        </section>
      </main>
    </>
  );
}
