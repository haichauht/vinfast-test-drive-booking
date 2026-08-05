import { Component } from 'react'

export class AppErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    console.error('Application render failed', error, info)
  }

  render() {
    if (!this.state.error) return this.props.children
    return (
      <main className="backend-gate backend-gate--error">
        <div>
          <span>Không thể hiển thị giao diện</span>
          <h1>Frontend gặp lỗi khi render.</h1>
          <p>{this.state.error.message || 'Lỗi không xác định.'}</p>
          <button type="button" onClick={() => window.location.reload()}>Tải lại trang</button>
        </div>
      </main>
    )
  }
}
