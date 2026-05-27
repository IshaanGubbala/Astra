import { Suspense } from "react";
import AppHome from "@/components/AppHome";

export default function HomePage() {
  return (
    <Suspense>
      <AppHome />
    </Suspense>
  );
}
