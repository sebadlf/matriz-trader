import { QueryClient } from '@tanstack/react-query';

// Peor caso hasta el error visible: 5 s de timeout + 1 s de espera + 5 s del reintento = 11 s < 15 s (AC-8).
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, retryDelay: 1000, refetchOnWindowFocus: false },
  },
});
