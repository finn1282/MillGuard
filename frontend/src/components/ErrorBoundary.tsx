import { Component, type ReactNode } from "react";

// Keeps one broken page from blanking the whole demo.
export class ErrorBoundary extends Component<{ children: ReactNode; resetKey?: string }, { error?: Error }> {
  state: { error?: Error } = {};
  static getDerivedStateFromError(error: Error) { return { error }; }
  componentDidUpdate(prev: { resetKey?: string }) {
    if (prev.resetKey !== this.props.resetKey && this.state.error) this.setState({ error: undefined });
  }
  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div role="alert" className="m-4 lg:m-10 bg-card border border-rule rounded p-5">
        <p className="m-0 font-bold text-lg">Something went wrong on this page. / Ralat pada halaman ini.</p>
        <p className="m-0 mt-1 font-num text-sm text-muted break-words">{this.state.error.message}</p>
        <button className="btn btn-outline mt-3" onClick={() => this.setState({ error: undefined })}>Try again / Cuba lagi</button>
      </div>
    );
  }
}
