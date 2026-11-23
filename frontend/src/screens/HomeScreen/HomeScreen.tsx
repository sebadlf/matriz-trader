import { Alert, Flex, Result, Spin } from "antd";

import { useGetHealth } from "@/api/generated/health/health";

export function HomeScreen() {
  const { data, isPending, isError } = useGetHealth();

  if (isPending) {
    return (
      <Flex justify="center" style={{ padding: 48 }}>
        <Spin size="large" aria-label="Cargando estado del backend" />
      </Flex>
    );
  }

  if (isError) {
    return (
      <Alert
        type="error"
        showIcon
        title="No se pudo conectar con el backend"
        description="Verificá que el servicio esté en ejecución y volvé a intentar."
      />
    );
  }

  return (
    <Result status="success" title="matriz-trader" subTitle={`Backend: ${data.data.status}`} />
  );
}
