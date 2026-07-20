import type { ButtonHTMLAttributes } from "react";
import { cva, type VariantProps } from "class-variance-authority";

export const buttonVariants = cva("button", {
  variants: {
    variant: {
      primary: "button-primary",
      secondary: "button-secondary",
      ghost: "button-ghost",
      danger: "button-danger",
    },
    size: {
      sm: "button-sm",
      md: "button-md",
      lg: "button-lg",
    },
    density: {
      compact: "button-compact",
      comfortable: "button-comfortable",
    },
    state: {
      default: "",
      loading: "button-loading",
    },
  },
  defaultVariants: {
    variant: "primary",
    size: "md",
    density: "comfortable",
    state: "default",
  },
});

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants>;

export function Button({
  className,
  density,
  size,
  state,
  variant,
  ...props
}: ButtonProps) {
  return (
    <button
      className={buttonVariants({
        className,
        density,
        size,
        state,
        variant,
      })}
      {...props}
    />
  );
}
