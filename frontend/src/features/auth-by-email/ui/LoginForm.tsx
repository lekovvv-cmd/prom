import { LogIn } from "lucide-react";
import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../../../app/providers/AppProviders";
import { Button } from "../../../shared/ui/Button";
import { Input } from "../../../shared/ui/Input";
import { isUtmnEmail, normalizeEmail } from "../../../shared/lib/email";
import { requestCode, verifyCode } from "../api/authApi";

const demoUsers = [
  { label: "Админ", email: "admin@utmn.ru", description: "проекты, отклики, статистика" },
  { label: "Руководитель", email: "manager@utmn.ru", description: "ведение проектов и откликов" },
  { label: "Сотрудник", email: "employee@utmn.ru", description: "витрина и отклик" }
];

export function LoginForm() {
  const navigate = useNavigate();
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
      navigate("/projects");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось войти");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="form-panel login-form" onSubmit={handleSubmit}>
      <div className="role-switcher" aria-label="Демо-роли">
        {demoUsers.map((user) => (
          <button
            type="button"
            key={user.email}
            className={email === user.email ? "role-option role-option-active" : "role-option"}
            onClick={() => setEmail(user.email)}
          >
            <strong>{user.label}</strong>
            <span>{user.email}</span>
            <small>{user.description}</small>
          </button>
        ))}
      </div>
      <Input
        label="Email"
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
