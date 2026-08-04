import { IdealReferenceFace } from "@/components/methodology/ideal-reference-face-verified";
import styles from "./reference-face.module.css";

export default function Page() {
  return (
    <main className={styles.referencePage}>
      <IdealReferenceFace />
    </main>
  );
}
