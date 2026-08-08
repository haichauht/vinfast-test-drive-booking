import { commonMedia, vehicleImage, vehicleVideo } from '../media/assets'

const factoryFilm = vehicleVideo('Video chính.mp4')
const limoInteriorFilm = vehicleVideo('Dịch vụ_Limo Green/Limo Green_Spacious Interior.mp4')
// Dùng trực tiếp ảnh ViVi gốc 447 px thay cho bản PNG cũ chỉ còn 223 px.
// CSS ở từng bề mặt chịu trách nhiệm hoà nền trắng vào studio để không lộ khung ảnh.
const viviPortrait = vehicleImage('Ảnh ViVi.jpeg')
const viviAvatar = commonMedia.viviAvatar
const roadBanner = commonMedia.vinfastRoadBanner
const factoryAerial = vehicleImage('nha-may-vinfast.jpg')
const vf9Sculpture = vehicleImage('about-us.png.webp')

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
