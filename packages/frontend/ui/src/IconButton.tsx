import type { ButtonProps } from "./Button";
import { Button } from "./Button";

export function IconButton({
  "aria-label": ariaLabel,
  children,
  ...props
}: ButtonProps & { "aria-label": string }) {
  return (
    <Button
      {...props}
      aria-label={ariaLabel}
      className={`size-10 p-0 ${props.className ?? ""}`}
    >
      {children}
    </Button>
  );
}
