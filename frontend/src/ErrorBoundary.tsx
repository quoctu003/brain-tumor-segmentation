import { Component, type ErrorInfo, type ReactNode } from "react";
import { CircleAlert, RefreshCw } from "lucide-react";

export default class ErrorBoundary extends Component<
  { children: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Workspace rendering failed", error, info.componentStack);
  }
  render() {
    if (this.state.failed)
      return (
        <div className="panel error-boundary" role="alert">
          <CircleAlert size={30} />
          <h2>Không thể hiển thị nội dung</h2>
          <p>
            Dữ liệu đã lưu vẫn được giữ. Tải lại trang để kết nối lại workspace.
          </p>
          <button
            className="secondary-button"
            onClick={() => window.location.reload()}
          >
            <RefreshCw size={15} /> Tải lại ứng dụng
          </button>
        </div>
      );
    return this.props.children;
  }
}
