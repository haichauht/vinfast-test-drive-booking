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
 *   2. File trong local/vehicle-media/ hoặc local/common/ hoặc local/showcase/
 *   3. CDN, nếu có đặt VITE_MEDIA_BASE_URL
 *
 * Tên file tiếng Việt được chuẩn hoá Unicode NFC — đừng bỏ bước này, macOS lưu khác Windows.
 * Bảng "mẫu xe nào dùng ảnh nào" nằm ở ./vehicle-media-map.js.
 */
import { vehicleMediaMap } from './vehicle-media-map'
import { r2ObjectKey } from './r2-key-aliases'

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

const overrideModules = import.meta.glob('./local/by-model/*/*.{png,jpg,jpeg,webp,svg,mp4,mov}', {
  eager: true,
  query: '?url',
  import: 'default',
})

const showcaseModules = import.meta.glob('./local/showcase/*/*.{png,jpg,jpeg,webp}', {
  eager: true,
  query: '?url',
  import: 'default',
})

const mediaBaseUrl = (import.meta.env.VITE_MEDIA_BASE_URL || '').replace(/\/+$/, '')
const normalizePath = (path) => path.normalize('NFC').replace(/^\/+/, '')
const encodePath = (path) => normalizePath(path).split('/').map(encodeURIComponent).join('/')
const cdnUrl = (scope, relativePath) => {
  if (!mediaBaseUrl) return ''
  const objectKey = r2ObjectKey(`${scope}/${normalizePath(relativePath)}`)
  return `${mediaBaseUrl}/${encodePath(objectKey)}`
}

const normalizeModules = (modules) =>
  Object.fromEntries(Object.entries(modules).map(([key, url]) => [key.normalize('NFC'), url]))

const vehicleImages = normalizeModules(vehicleImageModules)
const vehicleVideos = normalizeModules(vehicleVideoModules)
const brochures = normalizeModules(brochureModules)
const commonImages = normalizeModules(commonImageModules)
const showcaseImages = normalizeModules(showcaseModules)

const localAsset = (modules, root, relativePath) =>
  modules[`${root}/${normalizePath(relativePath)}`.normalize('NFC')] || ''

const overrides = normalizeModules(overrideModules)

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
  localAsset(vehicleImages, './local/vehicle-media', relativePath) ||
  cdnUrl('vehicle-media', relativePath)

export const vehicleVideo = (relativePath) =>
  overrideForLegacyPath(relativePath) ||
  localAsset(vehicleVideos, './local/vehicle-media', relativePath) ||
  cdnUrl('vehicle-media', relativePath)

export const commonImage = (fileName) =>
  overrideForLegacyPath(fileName, 'common/') ||
  localAsset(commonImages, './local/common', fileName) ||
  cdnUrl('common', fileName)

export const modelImage = (vehicleId) => {
  const relativePath = vehicleMediaMap[vehicleId]?.thumbnail || ''

  if (!relativePath) return ''
  if (relativePath.startsWith('common/')) {
    return commonImage(relativePath.slice('common/'.length))
  }

  return vehicleImage(relativePath)
}

export const modelOverride = (vehicleId, slot) => overrideUrl(vehicleId, slot)

export const showcaseImage = (relativePath) => {
  const [modelId, fileName] = normalizePath(relativePath).split('/')
  const slot = fileName?.replace(/\.[^.]+$/, '')
  return (
    (modelId && slot ? overrideUrl(modelId, slot) : '') ||
    localAsset(showcaseImages, './local/showcase', relativePath) ||
    cdnUrl('showcase', relativePath)
  )
}

export const brochureByKeyword = (keyword) => {
  const entry = Object.entries(brochures).find(([path]) =>
    path.toLocaleLowerCase('vi').includes(keyword),
  )
  if (!entry) return ''
  const [path, local] = entry
  return local || cdnUrl('brochures', path.split('/').pop())
}

export const vehicleAssetByName = (folder, fileName) => {
  const prefix = `./local/vehicle-media/${normalizePath(folder)}/`
  const local = Object.entries(vehicleImages).find(([path]) =>
    path.startsWith(prefix.normalize('NFC')) && path.endsWith(fileName),
  )?.[1] || ''
  return local || cdnUrl('vehicle-media', `${normalizePath(folder)}/${fileName}`)
}

export const vehicleAssetsIn = (...folders) => Object.entries(vehicleImages)
  .filter(([key]) => folders.some((folder) => key.startsWith(`./local/vehicle-media/${folder}/`.normalize('NFC'))))
  .map(([key, src]) => {
    const path = key.replace('./local/vehicle-media/', '').normalize('NFC')
    return {
      src: src || cdnUrl('vehicle-media', path),
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
  viviPortrait: commonImage('vivi-portrait-cutout.png'),
}
