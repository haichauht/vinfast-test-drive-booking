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
import { modelImage, vehicleImage } from '../media/assets'

const vehicleMediaPrefix = '/media/vehicle-media/'
const catalogueVehicleMediaPattern = /\/media\/vehicles\/([^/?]+)\/(?:thumbnail|studio)\.[^/?#]+/i

const resolveVehicleMedia = (url = '') => {
  const catalogueMatch = url.match(catalogueVehicleMediaPattern)
  if (catalogueMatch) {
    return modelImage(decodeURIComponent(catalogueMatch[1])) || url
  }

  const markerIndex = url.indexOf(vehicleMediaPrefix)
  if (markerIndex === -1) return url
  const relativePath = decodeURI(url.slice(markerIndex + vehicleMediaPrefix.length))
  return vehicleImage(relativePath) || url
}

const mediaView = (media) => ({
  src: resolveVehicleMedia(media?.url || ''),
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
  hero: mediaView(vehicle.thumbnail).src,
  heroMedia: mediaView(vehicle.thumbnail),
  intro: mediaView(vehicle.thumbnail).src,
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
  specs: (vehicle.specifications?.[0]?.items || vehicle.shortSpecs || []).map(({ label, value }) => ({ label, value })),
  colors: (vehicle.colors || []).map((color) => ({ ...color, image: resolveVehicleMedia(color.image?.url || '') })),
  chapters: (vehicle.chapters || []).map((chapter) => ({ ...chapter, src: resolveVehicleMedia(chapter.media?.url || '') })),
  gallery: (vehicle.gallery || []).map((media, index) => ({
    src: resolveVehicleMedia(media.url),
    alt: media.alt || '',
    label: `Góc nhìn ${String(index + 1).padStart(2, '0')}`,
  })),
  actionMedia: mediaView(vehicle.actionMedia),
  presentationFilm: vehicle.presentationFilm ? {
    src: vehicle.presentationFilm.url,
    poster: resolveVehicleMedia(vehicle.presentationFilm.posterUrl || ''),
    mimeType: vehicle.presentationFilm.mimeType,
    eyebrow: vehicle.presentationFilm.eyebrow,
    title: vehicle.presentationFilm.title,
    copy: vehicle.presentationFilm.copy,
  } : null,
  motionImage: resolveVehicleMedia(vehicle.motion?.imageUrl || ''),
})
