import React from 'react';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null, errorInfo: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true };
    }

    componentDidCatch(error, errorInfo) {
        console.error("Uncaught error:", error, errorInfo);
        this.setState({ error, errorInfo });
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="p-8 max-w-2xl mx-auto mt-10 bg-red-50 border border-red-200 rounded-xl">
                    <h1 className="text-2xl font-bold text-red-700 mb-4">Something went wrong.</h1>
                    <div className="bg-white p-4 rounded-lg border border-red-100 font-mono text-sm overflow-auto text-red-600 mb-4">
                        {this.state.error && this.state.error.toString()}
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 font-mono text-xs overflow-auto h-64 text-gray-600">
                        {this.state.errorInfo && this.state.errorInfo.componentStack}
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
