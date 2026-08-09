import { Link } from 'react-router-dom'

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="section-frame site-footer__inner">
        <div>
          <strong>VINFAST</strong>
          <p>Thiết kế trải nghiệm xem xe và đặt lịch lái thử.</p>
        </div>
        <nav aria-label="Liên kết cuối trang">
          <a href="/#models">Ô tô</a>
          <a href="/#technology">Công nghệ</a>
          <Link to="/after-sales">Hậu mãi</Link>
          <Link to="/charging">Pin & trạm sạc</Link>
          <Link to="/booking">Đặt lịch</Link>
          <Link to="/agent">Trợ lý ViVi</Link>
        </nav>
        <p className="site-footer__legal">
          Thông số được tổng hợp từ brochure chính thức và có thể thay đổi theo phiên bản, điều kiện vận hành hoặc chính sách của nhà sản xuất.
        </p>
      </div>
    </footer>
  )
}
