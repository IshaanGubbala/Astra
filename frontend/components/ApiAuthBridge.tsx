"use client";

import { useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { setApiAuthProvider } from "@/lib/api";

export default function ApiAuthBridge() {
  const { getToken, userId } = useAuth();

  useEffect(() => {
    setApiAuthProvider(async () => ({
      token: await getToken(),
      userId,
    }));
    return () => setApiAuthProvider(null);
  }, [getToken, userId]);

  return null;
}
