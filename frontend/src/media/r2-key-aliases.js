// Cloudflare rejects R2 object keys with path-like `..` segments.  Keep the
// original source filenames intact, but use these stable public object keys.
export const r2KeyAliases = {
  'vehicle-media/VF3/1..webp': 'vehicle-media/VF3/1.webp',
  'vehicle-media/VF3/2..png': 'vehicle-media/VF3/exterior.png',
  'vehicle-media/VF3/3..jpg': 'vehicle-media/VF3/cockpit.jpg',
  'vehicle-media/VF3/4..png': 'vehicle-media/VF3/rear.png',
  'vehicle-media/VF5/1..webp': 'vehicle-media/VF5/1.webp',
  'vehicle-media/VF5/3..webp': 'vehicle-media/VF5/3.webp',
  'vehicle-media/VF5/4..webp': 'vehicle-media/VF5/4.webp',
  'vehicle-media/VF5/5..webp': 'vehicle-media/VF5/5.webp',
}

export const r2ObjectKey = (key) => r2KeyAliases[key] || key
