import { vehicleImage } from '../media/assets'

const vehicleMediaPrefix = '/media/vehicle-media/'

const resolveVehicleMedia = (url = '') => {
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
    poster: vehicle.presentationFilm.posterUrl,
    mimeType: vehicle.presentationFilm.mimeType,
    eyebrow: vehicle.presentationFilm.eyebrow,
    title: vehicle.presentationFilm.title,
    copy: vehicle.presentationFilm.copy,
  } : null,
  motionImage: vehicle.motion?.imageUrl || '',
})
