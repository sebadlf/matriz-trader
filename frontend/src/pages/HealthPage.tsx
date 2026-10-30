import { Alert, Descriptions, Layout, Spin, Tag, Typography } from 'antd';
import { type getHealthResponse, useGetHealth } from '../api/generated/matriz';
import { ApiError } from '../api/http';

function describeError(error: Error): string {
  if (error instanceof ApiError) {
    if (error.status === 503) {
      return 'HTTP 503 — database: unavailable';
    }
    return `HTTP ${error.status}`;
  }
  return 'El backend no responde';
}

function HealthContent() {
  const { data, error, isPending } = useGetHealth<getHealthResponse, Error>();

  if (isPending) {
    return (
      <div data-testid="health-loading">
        <Spin size="large" />
        <Typography.Text style={{ marginLeft: 16 }}>
          Consultando estado del backend…
        </Typography.Text>
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        data-testid="health-error"
        type="error"
        showIcon
        message="No se pudo obtener el estado del backend"
        description={describeError(error)}
      />
    );
  }

  const health = data.data;
  return (
    <Descriptions title="Estado del sistema" bordered column={1}>
      <Descriptions.Item label="status">
        <Tag color={health.status === 'ok' ? 'green' : 'orange'} data-testid="health-status">
          {health.status}
        </Tag>
      </Descriptions.Item>
      <Descriptions.Item label="database">
        <Tag color={health.database === 'ok' ? 'green' : 'red'} data-testid="health-database">
          {health.database}
        </Tag>
      </Descriptions.Item>
    </Descriptions>
  );
}

export function HealthPage() {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Layout.Content style={{ padding: 24 }}>
        <Typography.Title level={2}>Matriz Trader</Typography.Title>
        <HealthContent />
      </Layout.Content>
    </Layout>
  );
}
