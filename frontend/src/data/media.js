import factoryFilm from '../../Ảnh xe vinfast/Video chính.mp4?url'
import limoInteriorFilm from '../../Ảnh xe vinfast/Dịch vụ_Limo Green/Limo Green_Spacious Interior.mp4?url'
// Dùng trực tiếp ảnh ViVi gốc 447 px thay cho bản PNG cũ chỉ còn 223 px.
// CSS ở từng bề mặt chịu trách nhiệm hoà nền trắng vào studio để không lộ khung ảnh.
import viviPortrait from '../../Ảnh xe vinfast/Ảnh ViVi.jpeg?url'
import viviAvatar from '../assets/vivi-avatar.png'
import roadBanner from '../assets/vinfast-road-banner.webp'
import factoryAerial from '../../Ảnh xe vinfast/nha-may-vinfast.jpg?url'
import vf9Sculpture from '../../Ảnh xe vinfast/about-us.png.webp?url'

// TODO [BACKEND/CDN]: Replace bundled marketing media with the published media
// payload from GET /api/v1/content/home and GET /api/v1/vehicles/{id}/media.
// Video records must include url, posterUrl, mimeType, width, height, duration,
// autoplayAllowed and revision; image records need alt, focalPoint and revision.
// Keep these local imports as the offline/build-time fallback.
export {
  factoryAerial,
  factoryFilm,
  limoInteriorFilm,
  roadBanner,
  vf9Sculpture,
  viviAvatar,
  viviPortrait,
}
