import { Header } from "../../../widgets/header/ui/Header";
import { LoginForm } from "../../../features/auth-by-email/ui/LoginForm";

export function LoginPage() {
  return (
    <>
      <Header />
      <main className="login-page">
        <section>
          <h1>Вход в витрину проектов</h1>
          <p>Для MVP используется email на домене @utmn.ru и dev-код 000000.</p>
          <LoginForm />
        </section>
      </main>
    </>
  );
}
