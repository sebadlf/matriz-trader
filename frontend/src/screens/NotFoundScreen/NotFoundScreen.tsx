import { Result } from "antd";
import { Link } from "react-router";

import { ROUTES } from "@/constants/routes";

export function NotFoundScreen() {
  return (
    <Result
      status="404"
      title="404"
      subTitle="Página no encontrada"
      extra={<Link to={ROUTES.home}>Volver al inicio</Link>}
    />
  );
}
