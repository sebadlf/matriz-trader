import { QueryClient, type QueryClientConfig } from "@tanstack/react-query";

export const createQueryClient = (overrides?: QueryClientConfig): QueryClient =>
  new QueryClient({
    ...overrides,
    defaultOptions: {
      ...overrides?.defaultOptions,
      queries: {
        staleTime: 30_000,
        retry: 1,
        ...overrides?.defaultOptions?.queries,
      },
    },
  });
