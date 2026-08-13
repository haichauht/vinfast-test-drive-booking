/**
 * components/Brand.jsx — Logo VinFast ở góc trái header, bấm vào là về trang chủ.
 *
 * Dùng ở: AppShell.jsx (mọi trang marketing) và BookingPage.jsx (header riêng của trang đặt lịch).
 * Prop `inverse`: bật khi header nằm trên nền tối, thêm class .brand--inverse để đảo màu logo.
 *
 * Ảnh logo lấy từ src/media/local/vehicle-media/. CSS dùng object-fit: contain nên logo
 * luôn hiện trọn khung, không bị cắt hay kéo méo. Style ở mục "Floating navigation" trong index.css.
 */
import { Link } from 'react-router-dom'
import { vehicleImage } from '../media/assets'

const vinfastLogo = vehicleImage('Vinfast-logo-new_NO_Tagline -2D-Horizontal black.png')

// Dùng trực tiếp logo ngang do chủ dự án cung cấp để đồng nhất nhận diện giữa
// website và ViVi. `object-fit: contain` trong CSS giữ nguyên toàn bộ chi tiết logo.
export function Brand({ inverse = false }) {
  return (
    <Link
      to="/"
      className={`brand ${inverse ? 'brand--inverse' : ''}`}
      aria-label="VinFast - về trang chủ"
    >
      <img className="brand__logo" src={vinfastLogo} alt="" aria-hidden="true" />
    </Link>
  )
}
