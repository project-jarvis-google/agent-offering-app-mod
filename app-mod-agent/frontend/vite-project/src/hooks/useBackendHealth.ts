import { useEffect, useState } from "react";

export function useBackendHealth(apiBaseUrl: string) {
  const [isBackendReady, setIsBackendReady] = useState(false);
  const [isCheckingBackend, setIsCheckingBackend] = useState(true);

  const checkBackendHealth = async () => {
    try {
      const response = await fetch(apiBaseUrl + `/docs`, { method: "GET" });
      return response.ok;
    } catch {
      return false;
    }
  };

  useEffect(() => {
    const checkBackend = async () => {
      setIsCheckingBackend(true);
      const maxAttempts = 60; 
      let attempts = 0;

      while (attempts < maxAttempts) {
        const isReady = await checkBackendHealth();
        if (isReady) {
          setIsBackendReady(true);
          setIsCheckingBackend(false);
          return;
        }
        attempts++;
        await new Promise((r) => setTimeout(r, 2000));
      }

      setIsCheckingBackend(false);
    };

    checkBackend();
  }, [apiBaseUrl]);

  return { isBackendReady, isCheckingBackend };
}
