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

const brochureModules = import.meta.glob('./local/brochures/*.pdf', {
  eager: true,
  query: '?url',
  import: 'default',
})

const commonImageModules = import.meta.glob('./local/common/*.{png,jpg,jpeg,webp,svg}', {
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

export const vehicleImage = (relativePath) =>
  cdnUrl('vehicle-media', relativePath) ||
  localAsset(vehicleImages, './local/vehicle-media', relativePath)

export const vehicleVideo = (relativePath) =>
  cdnUrl('vehicle-media', relativePath) ||
  localAsset(vehicleVideos, './local/vehicle-media', relativePath)

export const commonImage = (fileName) =>
  cdnUrl('common', fileName) ||
  localAsset(commonImages, './local/common', fileName)

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
}
