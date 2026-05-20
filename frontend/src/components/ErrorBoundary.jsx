import { Component } from "react";

/**
 * ErrorBoundary — catches render errors in any child page component.
 * Prevents white-screen crashes when API data shape mismatches or
 * component throws during render.
 */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error("[ErrorBoundary]", error.message, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
          <div className="w-16 h-16 rounded-full bg-furnace-red/10 flex items-center justify-center">
            <svg className="w-8 h-8 text-furnace-red" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="text-lg font-bold text-furnace-text">頁面載入發生錯誤</h2>
          <p className="text-sm text-furnace-muted max-w-md text-center">
            {this.state.error?.message || "未知錯誤。請嘗試重新整理頁面。"}
          </p>
          <button
            onClick={() => {
              this.setState({ hasError: false, error: null });
              window.location.reload();
            }}
            className="px-4 py-2 bg-furnace-green text-white rounded-lg text-sm hover:bg-furnace-green/90 transition-colors"
          >
            重新整理
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}