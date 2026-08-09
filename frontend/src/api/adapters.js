/**
 * api/adapters.js — Phiên dịch dữ liệu backend sang đúng tên trường mà giao diện đang dùng.
 *
 * Lý do tồn tại: backend trả `bodyType`, `displayPrice`, `thumbnail.url`… còn các trang được
 * viết từ trước với `body`, `price`, `hero`. File này ngồi giữa để KHÔNG phải sửa lại JSX.
 * Backend đổi tên trường thì chỉ cần sửa ở đây, không cần đụng vào các trang.
 *
 * Chứa gì:
 * - mediaView(): gom một ảnh thành { src, alt, focalPoint, aspectRatio, fit } cho <SmartImage>.
 * - vehicleSummaryToCar(): dữ liệu xe rút gọn → thẻ xe ở trang chủ, menu, bảng đổi xe.
 * - vehicleDetailToCar(): thêm mô tả, brochure, bảng màu, chapters, gallery, video giới thiệu,
 *   ảnh motion (ảnh tách nền dùng cho animation xe chạy ở trang chi tiết).
 *
 * Sửa ở đây khi: giao diện thiếu một trường dữ liệu, hoặc backend đổi tên trường trong API.
 */
const mediaView = (media) => ({
  src: media?.url || '',
  alt: media?.alt || '',
  focalPoint: media?.focalPoint || '50% 50%',
  aspectRatio: media?.aspectRatio,
  fit: media?.fit,
})

export const vehicleSummaryToCar = (vehicle) => ({
  id: vehicle.id,
  name: vehicle.name,
  navName: vehicle.navName,
  category: vehicle.category,
  body: vehicle.bodyType,
  seats: `${vehicle.seats} chỗ`,
  price: vehicle.displayPrice,
  tagline: vehicle.tagline,
  hero: vehicle.thumbnail?.url || '',
  heroMedia: mediaView(vehicle.thumbnail),
  intro: vehicle.thumbnail?.url || '',
  studioShot: {
    ...mediaView(vehicle.studioImage),
    mode: vehicle.studioImage?.mode || 'photo',
  },
  specs: (vehicle.shortSpecs || []).map(({ label, value }) => ({ label, value })),
  featured: vehicle.featured,
  testDriveEligible: vehicle.testDriveEligible,
  sortOrder: vehicle.sortOrder,
})

export const vehicleDetailToCar = (vehicle) => ({
  ...vehicleSummaryToCar(vehicle),
  description: vehicle.description,
  brochure: vehicle.brochure,
  colors: (vehicle.colors || []).map((color) => ({ ...color, image: color.image?.url || '' })),
  chapters: (vehicle.chapters || []).map((chapter) => ({ ...chapter, src: chapter.media?.url || '' })),
  gallery: (vehicle.gallery || []).map((media) => media.url),
  presentationFilm: vehicle.presentationFilm ? {
    src: vehicle.presentationFilm.url,
    poster: vehicle.presentationFilm.posterUrl,
    mimeType: vehicle.presentationFilm.mimeType,
  } : null,
  motionImage: vehicle.motion?.imageUrl || '',
})
