"use client"
import React, { Component, ReactNode } from 'react'

interface Props {
  children: ReactNode;
  fallbackMessage: ReactNode;
  onRetry?: () => void;
}

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(_: Error): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="w-full h-full flex flex-col items-center justify-center p-4 bg-red-900/10 border border-red-900/30 text-red-400 text-xs text-center rounded-[6px]">
          <svg className="w-6 h-6 mb-2 opacity-80" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <div className="font-medium text-red-300 mb-2">{this.props.fallbackMessage}</div>
          {this.props.onRetry && (
            <button 
              onClick={() => {
                this.setState({ hasError: false })
                this.props.onRetry!()
              }}
              className="text-[10px] bg-red-900/40 hover:bg-red-900/60 transition-colors px-3 py-1.5 rounded"
            >
              点击重试
            </button>
          )}
        </div>
      );
    }
    return this.props.children;
  }
}
