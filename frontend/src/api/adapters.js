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
