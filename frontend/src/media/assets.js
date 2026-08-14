/**
 * media/assets.js — Cầu nối tới kho ảnh/video/brochure nằm trong src/media/local/ (~180 MB).
 *
 * Vite quét sẵn toàn bộ thư mục local/ lúc build (import.meta.glob) rồi đóng gói vào dist,
 * nên file này KHÔNG tải gì từ mạng. Đây là kho ảnh của các trang marketing.
 *
 * Phân biệt 2 nguồn ảnh trong dự án — hay nhầm:
 * - Ảnh CATALOGUE XE  → backend trả URL /media/... (phải publish sang backend/data/media).
 * - Ảnh MARKETING     → file này, nhúng thẳng vào bundle, luôn hiển thị được.
 *
 * 3 thư mục nguồn: local/vehicle-media/ (ảnh+video theo mẫu xe) · local/common/ (logo, ViVi,
 * ảnh dùng chung) · local/brochures/ (PDF).
 *
 * Hàm chính:
 * - vehicleImage(path) · vehicleVideo(path): lấy 1 file theo đường dẫn tương đối.
 * - vehicleAssetByName(folder, ten): tìm file trong 1 thư mục con, ví dụ "Trạm sạc".
 * - vehicleAssetsIn(...folders): lấy TẤT CẢ ảnh trong nhiều thư mục (dùng cho gallery).
 * - brochureByKeyword(tu): tìm PDF theo từ khoá trong tên file.
 * - commonMedia: object liệt kê sẵn các ảnh dùng chung (logo, viviAvatar, vf9Studio…).
 *
 * Thứ tự ưu tiên khi lấy ảnh (mới nhất thắng):
 *   1. local/by-model/<mã xe>/<slot>.*  — lớp ghi đè, xem local/by-model/README.md
 *   2. CDN, nếu có đặt VITE_MEDIA_BASE_URL
 *   3. File trong local/vehicle-media/ hoặc local/common/
 *
 * Tên file tiếng Việt được chuẩn hoá Unicode NFC — đừng bỏ bước này, macOS lưu khác Windows.
 * Bảng "mẫu xe nào dùng ảnh nào" nằm ở ./vehicle-media-map.js.
 */
import { vehicleMediaMap } from './vehicle-media-map'

const vehicleImageModules = import.meta.glob('./local/vehicle-media/**/*.{png,jpg,jpeg,webp,svg}', {
  eager: true,
  query: '?url',
  import: 'default',
})

const vehicleVideoModules = import.meta.glob('./local/vehicle-media/**/*.{mp4,mov}', {
  eager: true,
  query: '?url',
  import: 'default',
})

// Cloudflare Pages Direct Upload accepts files up to 25 MiB. The VF 8 new
// generation brochure is larger, and the live detail page already receives
// its canonical R2 URL from the backend catalogue, so do not bundle that
// source PDF into the frontend deployment.
const brochureModules = import.meta.glob([
  './local/brochures/*.pdf',
  '!./local/brochures/VF 8 The he moi All News_Brochure_final 20.05.pdf',
], {
  eager: true,
  query: '?url',
  import: 'default',
})

const commonImageModules = import.meta.glob('./local/common/*.{png,jpg,jpeg,webp,svg}', {
  eager: true,
  query: '?url',
  import: 'default',
})

// Lớp ghi đè theo mã xe: bỏ file vào local/by-model/<mã xe>/studio.png là ảnh đó thắng ảnh
// trong kho cũ, không cần sửa dòng code nào. Xem local/by-model/README.md.
const overrideModules = import.meta.glob('./local/by-model/*/*.{png,jpg,jpeg,webp,svg,mp4,mov}', {
  eager: true,
  query: '?url',
  import: 'default',
})

// Xe trưng bày (Lạc Hồng) — ảnh đã tách nền, không thuộc catalogue backend.
const showcaseModules = import.meta.glob('./local/showcase/*/*.{png,jpg,jpeg,webp}', {
  eager: true,
  query: '?url',
  import: 'default',
})

const mediaBaseUrl = (import.meta.env.VITE_MEDIA_BASE_URL || '').replace(/\/+$/, '')
const normalizePath = (path) => path.normalize('NFC').replace(/^\/+/, '')
const encodePath = (path) => normalizePath(path).split('/').map(encodeURIComponent).join('/')
const cdnUrl = (scope, relativePath) =>
  mediaBaseUrl ? `${mediaBaseUrl}/${scope}/${encodePath(relativePath)}` : ''

const normalizeModules = (modules) =>
  Object.fromEntries(Object.entries(modules).map(([key, url]) => [key.normalize('NFC'), url]))

const vehicleImages = normalizeModules(vehicleImageModules)
const vehicleVideos = normalizeModules(vehicleVideoModules)
const brochures = normalizeModules(brochureModules)
const commonImages = normalizeModules(commonImageModules)

const localAsset = (modules, root, relativePath) =>
  modules[`${root}/${normalizePath(relativePath)}`.normalize('NFC')] || ''

const overrides = normalizeModules(overrideModules)

// Bảng tra ngược: đường dẫn ảnh cũ -> mã xe + tên slot. Nhờ bảng này mà mọi chỗ đang gọi
// vehicleImage('VF8/product-CE18.webp') tự nhận ảnh ghi đè, không phải sửa lại chỗ gọi.
const slotByLegacyPath = Object.entries(vehicleMediaMap).reduce((index, [id, entry]) => {
  if (entry.thumbnail) {
    index[entry.thumbnail.normalize('NFC')] = { id, slots: ['thumbnail', 'studio'] }
  }
  if (entry.video) index[entry.video.normalize('NFC')] = { id, slots: ['video'] }
  return index
}, {})

const overrideUrl = (vehicleId, slot) => {
  const prefix = `./local/by-model/${vehicleId}/${slot}.`.normalize('NFC')
  const match = Object.keys(overrides).filter((key) => key.startsWith(prefix)).sort()[0]
  return match ? overrides[match] : ''
}

// `scope` phân biệt 2 gốc đường dẫn trong sổ tra cứu: '' cho vehicle-media, 'common/' cho common.
const overrideForLegacyPath = (relativePath, scope = '') => {
  const entry = slotByLegacyPath[`${scope}${normalizePath(relativePath)}`.normalize('NFC')]
  if (!entry) return ''
  for (const slot of entry.slots) {
    const url = overrideUrl(entry.id, slot)
    if (url) return url
  }
  return ''
}

export const vehicleImage = (relativePath) =>
  overrideForLegacyPath(relativePath) ||
  cdnUrl('vehicle-media', relativePath) ||
  localAsset(vehicleImages, './local/vehicle-media', relativePath)

export const vehicleVideo = (relativePath) =>
  overrideForLegacyPath(relativePath) ||
  cdnUrl('vehicle-media', relativePath) ||
  localAsset(vehicleVideos, './local/vehicle-media', relativePath)

export const commonImage = (fileName) =>
  overrideForLegacyPath(fileName, 'common/') ||
  cdnUrl('common', fileName) ||
  localAsset(commonImages, './local/common', fileName)

/** Resolve a catalogue vehicle id to the image already bundled with the frontend. */
export const modelImage = (vehicleId) => {
  const relativePath = vehicleMediaMap[vehicleId]?.thumbnail || ''

  if (!relativePath) return ''
  if (relativePath.startsWith('common/')) {
    return commonImage(relativePath.slice('common/'.length))
  }

  return vehicleImage(relativePath)
}

/** Lấy thẳng ảnh ghi đè theo mã xe, không qua đường dẫn cũ. Trả '' nếu chưa có file ghi đè. */
export const modelOverride = (vehicleId, slot) => overrideUrl(vehicleId, slot)

const showcaseImages = normalizeModules(showcaseModules)

/**
 * Ảnh xe trưng bày đã tách nền, ví dụ showcaseImage('lac-hong-900lx/hero.png').
 * Vẫn cho phép ghi đè qua by-model/<id>/ để đổi ảnh mà không phải sửa code.
 */
export const showcaseImage = (relativePath) => {
  const [modelId, fileName] = normalizePath(relativePath).split('/')
  const slot = fileName?.replace(/\.[^.]+$/, '')
  return (
    (modelId && slot ? overrideUrl(modelId, slot) : '') ||
    cdnUrl('showcase', relativePath) ||
    localAsset(showcaseImages, './local/showcase', relativePath)
  )
}

export const brochureByKeyword = (keyword) => {
  const entry = Object.entries(brochures).find(([path]) =>
    path.toLocaleLowerCase('vi').includes(keyword),
  )
  if (!entry) return ''
  const [path, local] = entry
  return cdnUrl('brochures', path.split('/').pop()) || local
}

export const vehicleAssetByName = (folder, fileName) => {
  const prefix = `./local/vehicle-media/${normalizePath(folder)}/`
  const local = Object.entries(vehicleImages).find(([path]) =>
    path.startsWith(prefix.normalize('NFC')) && path.endsWith(fileName),
  )?.[1] || ''
  return cdnUrl('vehicle-media', `${normalizePath(folder)}/${fileName}`) || local
}

export const vehicleAssetsIn = (...folders) => Object.entries(vehicleImages)
  .filter(([key]) => folders.some((folder) => key.startsWith(`./local/vehicle-media/${folder}/`.normalize('NFC'))))
  .map(([key, src]) => {
    const path = key.replace('./local/vehicle-media/', '').normalize('NFC')
    return {
      src: cdnUrl('vehicle-media', path) || src,
      path,
    }
  })

export const commonMedia = {
  afterSalesConsultation: commonImage('after-sales-consultation.webp'),
  afterSalesHero: commonImage('after-sales-hero.webp'),
  limoGreenStudio: commonImage('limo-green-studio.webp'),
  nerioGreenStudio: commonImage('nerio-green-studio.png'),
  vfMpv7ModelCutout: commonImage('vf-mpv-7-model-cutout.png'),
  vf6FrontModelCutout: commonImage('vf6-front-model-cutout.png'),
  vf6ModelCutout: commonImage('vf6-model-cutout.png'),
  vf6Studio: commonImage('vf6-studio.webp'),
  vf9Studio: commonImage('vf9-studio.png'),
  vinfastLogo: commonImage('vinfast-logo.png'),
  vinfastRoadBanner: commonImage('vinfast-road-banner.webp'),
  viviAvatar: commonImage('vivi-avatar.png'),
  // Bản chân dung lớn có alpha thật: dùng trực tiếp trên nền trang, không bọc thẻ trắng.
  viviPortrait: commonImage('vivi-portrait-cutout.png'),
}
