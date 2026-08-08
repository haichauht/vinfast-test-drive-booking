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
