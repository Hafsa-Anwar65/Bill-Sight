import { Component, type ReactNode } from "react";

interface State { error: Error | null }

/** Keeps a rendering bug from blanking the whole page. */
export default class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error) {
    console.error("Billsight UI error:", error);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="card pad crash">
        <h3>This view could not be displayed</h3>
        <p className="muted">Your bill data is safe. Reload the page or upload the bill again.</p>
        <button className="btn primary" onClick={() => location.reload()}>Reload page</button>
      </div>
    );
  }
}
