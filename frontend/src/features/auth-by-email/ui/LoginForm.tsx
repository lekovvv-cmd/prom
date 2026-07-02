import { LogIn } from "lucide-react";
import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../../../app/providers/AppProviders";
import { Button } from "../../../shared/ui/Button";
import { Input } from "../../../shared/ui/Input";
import { requestCode, verifyCode } from "../api/authApi";

export function LoginForm() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState("admin@utmn.ru");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const normalizedEmail = email.trim().toLowerCase();
    if (!normalizedEmail.endsWith("@utmn.ru")) {
      setError("Введите email на домене @utmn.ru");
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
