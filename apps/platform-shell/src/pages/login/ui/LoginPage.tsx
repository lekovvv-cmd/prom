import { Header } from "@prom/layout";
import { LoginForm } from "@prom/auth/login";
import { Link } from "react-router-dom";

export function LoginPage() {
  return (
    <>
      <Header />
      <main className="login-page">
        <section className="login-shell" aria-labelledby="login-title">
          <div className="login-copy">
            <h1 id="login-title">Вход в PROM</h1>
            <p>
              Выберите демонстрационную роль или введите корпоративный адрес
              электронной почты.
            </p>
            <Link className="button button-secondary" to="/">
              Выбрать сервис
            </Link>
          </div>
          <LoginForm />
        </section>
      </main>
    </>
  );
}
