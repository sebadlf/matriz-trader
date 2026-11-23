import { QueryClientProvider, type QueryClient } from "@tanstack/react-query";
import { App as AntdApp, ConfigProvider } from "antd";
import { useState, type ReactNode } from "react";

import { createQueryClient } from "@/api/queryClient";

import { theme } from "./theme";

type AppProvidersProps = {
  children: ReactNode;
  queryClient?: QueryClient;
};

export function AppProviders({ children, queryClient }: AppProvidersProps) {
  const [defaultClient] = useState(createQueryClient);
  const client = queryClient ?? defaultClient;

  return (
    <ConfigProvider theme={theme}>
      <AntdApp>
        <QueryClientProvider client={client}>{children}</QueryClientProvider>
      </AntdApp>
    </ConfigProvider>
  );
}
