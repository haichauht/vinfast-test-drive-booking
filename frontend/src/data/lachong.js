/**
 * Nội dung chương Lạc Hồng trên trang chủ.
 *
 * COPY CONTRACT: ưu tiên kể về năng lực và bản sắc VinFast; không biến khối này thành
 * bảng thông số hoặc CTA bán xe. Lạc Hồng chưa nằm trong catalogue và không dẫn vào booking.
 * MEDIA CONTRACT: ảnh hero/emerge phải là PNG/WebP alpha thật, không ghép nền studio.
 */
import { showcaseImage } from '../media/assets'
import { showcaseMediaMap } from '../media/vehicle-media-map'

const spinFrames = showcaseMediaMap['lac-hong-900lx'].spin.map((path) => showcaseImage(path))

export const lacHongSpin = {
  id: 'lac-hong-900lx',
  name: 'Lạc Hồng 900 LX',
  frames: spinFrames,
}

export const lacHongModels = [
  {
    id: 'lac-hong-900lx',
    name: 'Lạc Hồng 900 LX',
    ordinal: 'LX',
    body: 'SUV nguyên thủ',
    image: showcaseImage('lac-hong-900lx/hero-v2.png'),
    narrative: 'Năng lực chế tác',
    headline: 'VinFast biến tinh thần Việt thành ngôn ngữ chế tác.',
    copy: 'Năng lực phát triển sản phẩm theo những yêu cầu riêng về tỷ lệ, vật liệu và không gian cho thấy VinFast đang làm chủ nhiều lớp giá trị hơn một phương tiện di chuyển. Đây là một dấu ấn thương hiệu, không phải mẫu đang mở bán.',
    meta: [
      { label: 'Ngôn ngữ', value: 'Bản sắc Việt' },
      { label: 'Vai trò', value: 'Dấu ấn VinFast' },
    ],
  },
  {
    id: 'lac-hong-900s',
    name: 'Lạc Hồng 900S',
    ordinal: '900S',
    body: 'Sedan hạng sang',
    image: showcaseImage('lac-hong-900s/hero-v2.png'),
    narrative: 'Tư duy thiết kế',
    headline: 'VinFast mở rộng một ngôn ngữ nhất quán qua nhiều hình thái.',
    copy: 'Từ tỷ lệ bề thế của SUV đến dáng sedan liền mạch, cùng một tư duy thiết kế vẫn giữ được dấu ấn nhận diện và tinh thần chế tác Việt. Sự nhất quán ấy là cách VinFast xây dựng một thương hiệu có chiều sâu.',
    meta: [
      { label: 'Phạm vi', value: 'Từ SUV đến sedan' },
      { label: 'Tinh thần', value: 'Chế tác tại Việt Nam' },
    ],
  },
]

/** Ảnh xe lớn ở đầu trang chủ. */
export const lacHongHero = {
  src: showcaseImage('lac-hong-900lx/hero-v2.png'),
  alt: 'Lạc Hồng 900 LX, ảnh studio nền trong suốt',
  name: 'Lạc Hồng 900 LX',
}

/** Ảnh đầu xe dùng cho khối "xe tiến ra từ chiều sâu". Ảnh gốc 768 px nên chỉ dùng ở cỡ vừa. */
export const lacHongEmerge = {
  src: showcaseImage('lac-hong-900lx/front-emerge-v2.png'),
  alt: 'Lạc Hồng nhìn chính diện trên nền trong suốt',
}

export const lacHongDisclaimer =
  'Hình ảnh thuộc phiên bản tiền thương mại, chỉ mang tính minh hoạ và có thể thay đổi trong quá trình phát triển.'
