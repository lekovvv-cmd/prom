import { cva, type VariantProps } from "class-variance-authority";

const badgeVariants = cva("badge", {
  variants: {
    tone: {
      danger: "badge-danger",
      info: "badge-info",
      muted: "badge-muted",
      neutral: "badge-neutral",
      success: "badge-success",
      warning: "badge-warning",
    },
    density: {
      compact: "badge-compact",
      comfortable: "badge-comfortable",
    },
  },
  defaultVariants: {
    tone: "neutral",
    density: "comfortable",
  },
});

export type BadgeTone = NonNullable<VariantProps<typeof badgeVariants>["tone"]>;

export function Badge({
  children,
  className,
  density,
  tone,
}: {
  children: React.ReactNode;
  className?: string;
} & VariantProps<typeof badgeVariants>) {
  return (
    <span className={badgeVariants({ className, density, tone })}>
      {children}
    </span>
  );
}
