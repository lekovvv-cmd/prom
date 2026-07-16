import { LogIn } from "lucide-react";
import { FormEvent, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../../../app/providers/AppProviders";
import { Button } from "../../../shared/ui/Button";
import { Input } from "../../../shared/ui/Input";
import { isUtmnEmail, normalizeEmail } from "../../../shared/lib/email";
import { requestCode, verifyCode } from "../api/authApi";

const demoUsers = [
  { label: "Сотрудник", email: "employee@utmn.ru", description: "Проекты, отклики и личный кабинет" },
  { label: "Руководитель проектов", email: "project.manager@utmn.ru", description: "Управление проектами и отчётностью" },
  { label: "Менеджер Service Desk", email: "sd.manager@utmn.ru", description: "каталог, заявки и рабочее место" },
  { label: "Администратор Service Desk", email: "sd.admin@utmn.ru", description: "Каталог, настройки и заявки" },
  { label: "Администратор платформы", email: "admin@utmn.ru", description: "Полный доступ к обоим модулям" }
];

export function LoginForm() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [email, setEmail] = useState("admin@utmn.ru");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const normalizedEmail = normalizeEmail(email);
    if (!isUtmnEmail(normalizedEmail)) {
      setError("Введите корректный email на домене @utmn.ru");
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      await requestCode(normalizedEmail);
      const response = await verifyCode(normalizedEmail, "000000");
      login(response.access_token, response.user);
      const next = new URLSearchParams(location.search).get("next");
      const target = next && next.startsWith("/") && !next.startsWith("//") && !next.startsWith("/login") ? next : "/projects";
      navigate(target, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось войти");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="form-panel login-form" onSubmit={handleSubmit}>
      <div className="login-form-heading">
        <h2>Выберите учётную запись</h2>
        <p>Для демо используется код подтверждения <strong>000000</strong>.</p>
      </div>
      <div className="role-switcher" role="group" aria-label="Демонстрационные роли">
        {demoUsers.map((user) => (
          <button
            type="button"
            key={user.email}
            className={email === user.email ? "role-option role-option-active" : "role-option"}
            onClick={() => setEmail(user.email)}
            aria-pressed={email === user.email}
          >
            <span className="role-option-title">{user.label}</span>
            <span className="role-option-email">{user.email}</span>
            <span className="role-option-description">{user.description}</span>
          </button>
        ))}
      </div>
      <Input
        label="Электронная почта"
        name="email"
        type="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        placeholder="admin@utmn.ru"
        required
      />
      {error && <p className="form-error">{error}</p>}
      <Button type="submit" disabled={isSubmitting}>
        <LogIn size={18} />
        {isSubmitting ? "Входим" : "Войти"}
      </Button>
    </form>
  );
}
