import { cva, type VariantProps } from "class-variance-authority";

const cardVariants = cva("card", {
  variants: {
    variant: {
      default: "card-default",
      elevated: "card-elevated",
      outlined: "card-outlined",
    },
    density: {
      compact: "card-compact",
      comfortable: "card-comfortable",
    },
  },
  defaultVariants: {
    variant: "default",
    density: "comfortable",
  },
});

export function Card({
  children,
  className,
  density,
  variant,
}: {
  children: React.ReactNode;
  className?: string;
} & VariantProps<typeof cardVariants>) {
  return (
    <section className={cardVariants({ className, density, variant })}>
      {children}
    </section>
  );
}
