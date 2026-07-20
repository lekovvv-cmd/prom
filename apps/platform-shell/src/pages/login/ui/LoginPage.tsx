import { Header } from "@prom/layout";
import { LoginForm } from "@prom/auth/login";

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
          </div>
          <LoginForm />
        </section>
      </main>
    </>
  );
}
