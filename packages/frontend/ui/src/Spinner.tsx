import styles from "./Spinner.module.css";

export function Spinner({ label = "Загрузка" }: { label?: string }) {
  return (
    <div className={styles.container} role="status">
      <span className={styles.indicator} />
      <span>{label}</span>
    </div>
  );
}
