import { Layout } from "antd";
import { Outlet } from "react-router";

export function RootLayout() {
  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Layout.Content>
        <Outlet />
      </Layout.Content>
    </Layout>
  );
}
