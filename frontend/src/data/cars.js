import vf6StudioShot from '../assets/vf6-front-model-cutout.png'
import vfMpv7StudioShot from '../assets/vf-mpv-7-model-cutout.png'
import limoStudioShot from '../assets/limo-green-studio.webp'
import vf9StudioShot from '../assets/vf9-studio.png'
import nerioStudioShot from '../assets/nerio-green-studio.png'
import vf8PresentationFilm from '../../Ảnh xe vinfast/VF8/VF8.mp4?url'
import vf8NewPresentationFilm from '../../Ảnh xe vinfast/VF8 All the new/VF8.mp4?url'
import vf9PresentationFilm from '../../Ảnh xe vinfast/VF9/VF9.mp4?url'

const imageModules = import.meta.glob(
  '../../Ảnh xe vinfast/**/*.{png,jpg,jpeg,webp,svg}',
  { eager: true, query: '?url', import: 'default' },
)

const normalizedModules = Object.fromEntries(
  Object.entries(imageModules).map(([key, url]) => [key.normalize('NFC'), url]),
)

const image = (relativePath) =>
  normalizedModules[`../../Ảnh xe vinfast/${relativePath}`.normalize('NFC')] || ''

export const carImage = image

// Anh bi loai khoi luoi "Toan bo goc nhin": banner co chu quang cao, ma QR,
// logo roi hoac anh chup nham mau xe khac.
const excludedAssets = new Set([
  'VF3/1..webp',
  'VF5/1.webp',
  'VF6/VF6-banner.webp',
  'VF9/VF9 model.webp',
  'Dịch vụ_ EC Van/banner.webp',
  'Dịch vụ_EBus/ebus-img-05.webp',
  'Dịch vụ_EBus/ebus-img-06.webp',
  'Dịch vụ_Herio Green/Banner-new.webp',
  'Dịch vụ_Herio Green/E-bike.webp',
  'Dịch vụ_Herio Green/Hero-new.webp',
  'Dịch vụ_Limo Green/footer.webp',
  'Dịch vụ_Limo Green/limo-green-4.webp',
  'Dịch vụ_Limo Green/limo-green-section-3-logo.webp',
].map((path) => path.normalize('NFC')))

const relativeAsset = (key) => key.split('/').slice(3).join('/').normalize('NFC')

const assetsIn = (...folders) => Object.entries(imageModules)
  .filter(([key]) => folders.some((folder) => key.startsWith(`../../Ảnh xe vinfast/${folder}/`)))
  .filter(([key]) => !excludedAssets.has(relativeAsset(key)))
  .map(([, src]) => ({ src }))

const uniqueAssets = (assets) => {
  const seen = new Set()
  return assets.filter((asset) => {
    if (!asset?.src || seen.has(asset.src)) return false
    seen.add(asset.src)
    return true
  })
}

// TODO [BACKEND]: Replace this brochure-derived catalogue with GET /api/v1/vehicles.
// The response should preserve ids, variants, colors, image URLs, specifications,
// brochure revision dates and test-drive eligibility. Presentation fields are part
// of the contract because the UI/animation depends on them: studioImageUrl,
// studioImageMode, motionImageUrl, motionPreset, focalPoint, mediaType, tone,
// aspectRatio, alt and sortOrder. See ../../BACKEND_HANDOFF.md for the full schema.
const catalogue = [
  {
    id: 'vf3',
    name: 'VF 3',
    navName: 'VF 3',
    category: 'personal',
    body: 'Mini eSUV',
    seats: '4 chỗ',
    price: 'Giá niêm yết · 299.000.000 VNĐ',
    tagline: 'Chất riêng trên mọi nẻo đường.',
    description: 'Gọn để xoay trở trong phố, đủ khác biệt để mỗi hành trình mang dấu ấn riêng.',
    hero: image('VF3/2.png'),
    intro: image('VF3/xám.png'),
    gallery: [
      image('VF3/1..webp'),
      image('VF3/3..jpg'),
      image('VF3/4..png'),
    ],
    specs: [
      { value: '215 km', label: 'Quãng đường NEDC' },
      { value: '32 kW', label: 'Công suất tối đa' },
      { value: '36 phút', label: 'Sạc nhanh 10–70%' },
      { value: '191 mm', label: 'Khoảng sáng gầm' },
    ],
    colors: [
      { name: 'Xám Zenith Grey', hex: '#909396', image: image('VF3/xám.png') },
      { name: 'Hồng Rose Pink', hex: '#d9a2ad', image: image('VF3/hồng.png') },
      { name: 'Đỏ Crimson Red', hex: '#a3232d', image: image('VF3/đỏ.png') },
    ],
    brochure: 'Thông tin sản phẩm VinFast VF 3',
    featured: true,
  },
  {
    id: 'vf5',
    name: 'VF 5',
    navName: 'VF 5',
    category: 'personal',
    body: 'SUV hạng A',
    seats: '5 chỗ',
    price: 'Giá niêm yết · 529.000.000 VNĐ',
    tagline: 'Sống động từng nhịp phố.',
    description: 'Một chiếc SUV điện linh hoạt với không gian đủ dùng cho gia đình và nhịp vận hành đô thị.',
    hero: image('VF5/1..webp'),
    intro: image('VF5/trắng.webp'),
    gallery: [
      image('VF5/2.webp'),
      image('VF5/3..webp'),
      image('VF5/5..webp'),
    ],
    specs: [
      { value: '326 km', label: 'Quãng đường NEDC' },
      { value: '100 kW', label: 'Công suất tối đa' },
      { value: '135 Nm', label: 'Mô-men xoắn' },
      { value: '37,23 kWh', label: 'Pin khả dụng' },
    ],
    colors: [
      { name: 'Trắng Infinity Blanc', hex: '#ecece8', image: image('VF5/trắng.webp') },
      { name: 'Vàng Summer Yellow · nóc Jet Black', hex: '#d5ad28', image: image('VF5/vàng đen.webp') },
      { name: 'Xám Zenith Grey', hex: '#73777b', image: image('VF5/xám.webp') },
      { name: 'Đỏ Solar Ruby', hex: '#a31f2d', image: image('VF5/đỏ.webp') },
    ],
    brochure: 'VF 5 Brochure · bản sửa 29.01.2026',
    featured: true,
  },
  {
    id: 'vf6',
    name: 'VF 6',
    navName: 'VF 6',
    category: 'personal',
    body: 'SUV hạng B',
    seats: '5 chỗ',
    price: 'Giá niêm yết · 689.000.000 VNĐ',
    tagline: 'Mạnh mẽ và tinh tế.',
    description: 'Tỷ lệ thân xe chắc gọn, nội thất tập trung vào người lái và lực kéo đến ngay khi cần.',
    hero: image('VF6/VF6-Lifestyle-12.webp'),
    intro: image('VF6/VF6-Lifestyle-10.webp'),
    gallery: [
      image('VF6/VF6-Lifestyle-10.webp'),
      image('VF6/interior-vf6-1.jpg'),
      image('VF6/technology-vf6-3.jpg'),
    ],
    specs: [
      { value: '460 km', label: 'Quãng đường NEDC' },
      { value: '150 kW', label: 'Công suất tối đa' },
      { value: '310 Nm', label: 'Mô-men xoắn' },
      { value: '59,6 kWh', label: 'Pin khả dụng' },
    ],
    colors: [],
    brochure: 'VF 6 Brochure · thông số VF 6 Plus tại Việt Nam',
    featured: true,
  },
  {
    id: 'vf7',
    name: 'VF 7',
    navName: 'VF 7',
    category: 'personal',
    body: 'SUV hạng C',
    seats: '5 chỗ',
    price: 'Giá niêm yết · 799.000.000 VNĐ',
    tagline: 'Dẫn lối đam mê.',
    description: 'Một hình khối fastback táo bạo, khoang lái hướng người dùng và hiệu năng hai cầu ở bản Plus AWD.',
    hero: image('VF7/vf7-slide-in-croped.webp'),
    intro: image('VF7/vf7-hero-car.webp'),
    gallery: [
      image('VF7/vf7-passion.webp'),
      image('VF7/vf7-noi-that-overview.webp'),
      image('VF7/vf7-uu-diem-3.webp'),
    ],
    specs: [
      { value: '431 km', label: 'Quãng đường WLTP' },
      { value: '260 kW', label: 'Công suất bản Plus' },
      { value: '500 Nm', label: 'Mô-men xoắn bản Plus' },
      { value: 'AWD', label: 'Dẫn động bản Plus' },
    ],
    colors: [
      { name: 'Đen Jet Black', hex: '#202225', image: image('VF7/product-CE11.webp') },
      { name: 'Trắng Infinity Blanc', hex: '#ecece8', image: image('VF7/product-CE18.webp') },
      { name: 'Đỏ Solar Ruby', hex: '#a90e1a', image: image('VF7/product-CE1M.webp') },
      { name: 'Xám Zenith Grey', hex: '#808489', image: image('VF7/product-CE1V.webp') },
      { name: 'Xanh Urban Mint', hex: '#87957d', image: image('VF7/product-CE1W.webp') },
    ],
    brochure: 'VF 7 Brochure · Eco / Plus / Plus AWD',
    featured: true,
  },
  {
    id: 'vf-mpv-7',
    name: 'VF MPV 7',
    navName: 'VF MPV 7',
    category: 'personal',
    body: 'MPV điện gia đình',
    seats: '7 chỗ',
    price: 'Giá niêm yết · 750.000.000 VNĐ',
    tagline: 'Rộng rãi cho cả gia đình.',
    description: 'Không gian ba hàng ghế linh hoạt, chiều dài cơ sở 2.840 mm và hệ dẫn động cầu trước cho những hành trình gia đình thoải mái hơn.',
    hero: image('VF7 FMP/D_01.webp'),
    intro: vfMpv7StudioShot,
    gallery: [
      image('VF7 FMP/D_01.webp'),
      image('VF7 FMP/D_03.webp'),
      image('VF7 FMP/D_05.webp'),
    ],
    specs: [
      { value: '450 km', label: 'Quãng đường NEDC' },
      { value: '150 kW', label: 'Công suất tối đa' },
      { value: '280 Nm', label: 'Mô-men xoắn cực đại' },
      { value: '60,13 kWh', label: 'Pin khả dụng' },
    ],
    colors: [],
    brochure: 'VF MPV 7 · thông số chính thức VinFast Việt Nam',
    featured: true,
  },
  {
    id: 'vf8',
    name: 'VF 8',
    navName: 'VF 8',
    category: 'personal',
    body: 'SUV hạng D',
    seats: '5 chỗ',
    price: 'Giá niêm yết · 1.020.000.000 VNĐ',
    tagline: 'Cùng bạn bứt phá mọi giới hạn.',
    description: 'Không gian gia đình rộng rãi, hệ dẫn động AWD toàn thời gian và hệ thống hỗ trợ lái toàn diện.',
    hero: image('VF8/banner.webp'),
    intro: image('VF8/product-171V.webp'),
    gallery: [
      image('VF8/interior-img1.webp'),
      image('VF8/ai.webp'),
      image('VF8/hud.webp'),
    ],
    specs: [
      { value: '420 km', label: 'Quãng đường bản Eco' },
      { value: '300 kW', label: 'Công suất bản Plus' },
      { value: '620 Nm', label: 'Mô-men xoắn bản Plus' },
      { value: '82 kWh', label: 'Pin khả dụng' },
    ],
    colors: [
      { name: 'Đen Jet Black', hex: '#202225', image: image('VF8/product-CE11.webp') },
      { name: 'Trắng Brahminy White', hex: '#ecece8', image: image('VF8/product-CE18.webp') },
      { name: 'Đỏ Crimson Red', hex: '#a91e28', image: image('VF8/product-CE1M.webp') },
      { name: 'Xanh Deep Ocean', hex: '#254538', image: image('VF8/product-CE22.webp') },
      { name: 'Xám Neptune Grey · phối kim loại', hex: '#777c82', image: image('VF8/product-171V.webp') },
      { name: 'Trắng Brahminy · phối kim loại', hex: '#e6e7e4', image: image('VF8/product-1V18.webp') },
    ],
    brochure: 'VF 8 Brochure · Eco / Plus',
    featured: true,
  },
  {
    id: 'vf8-the-he-moi',
    name: 'VF 8 Thế hệ mới',
    navName: 'VF 8 mới',
    category: 'personal',
    body: 'SUV hạng D',
    seats: '5 chỗ',
    price: 'Giá công bố tại showroom',
    tagline: 'Tinh giản để đi xa hơn.',
    description: 'Cấu hình cầu trước gọn nhẹ, pin 60,13 kWh và giao diện cabin tập trung vào nhu cầu sử dụng hàng ngày.',
    hero: image('VF8 All the new/VF8PH-23.webp'),
    intro: image('VF8 All the new/VF8PH-23.webp'),
    gallery: [
      image('VF8 All the new/VF8PH-13.webp'),
      image('VF8 All the new/car-left.webp'),
      image('VF8 All the new/tech-t1.png'),
    ],
    specs: [
      { value: '480–500 km', label: 'Quãng đường NEDC' },
      { value: '170 kW', label: 'Công suất tối đa' },
      { value: '330 Nm', label: 'Mô-men xoắn' },
      { value: '60,13 kWh', label: 'Pin khả dụng' },
    ],
    colors: [],
    brochure: 'VF 8 Thế hệ mới · brochure 20.05',
    featured: false,
  },
  {
    id: 'vf9',
    name: 'VF 9',
    navName: 'VF 9',
    category: 'personal',
    body: 'SUV hạng E',
    seats: '6 hoặc 7 chỗ',
    price: 'Giá niêm yết · 1.499.000.000 VNĐ',
    tagline: 'Rộng mở chất riêng.',
    description: 'SUV điện cỡ lớn với ba hàng ghế, dẫn động AWD và khoang hành khách được thiết kế cho những chuyến đi dài.',
    hero: image('VF9/img-video.webp'),
    intro: image('VF9/CE17.webp'),
    gallery: [
      image('VF9/interior-first-sight.webp'),
      image('VF9/int-slide-2.webp'),
      image('VF9/cs-home-charger.webp'),
    ],
    specs: [
      { value: '626 km', label: 'Quãng đường WLTP Eco' },
      { value: '300 kW', label: 'Công suất tối đa' },
      { value: '620 Nm', label: 'Mô-men xoắn' },
      { value: '123 kWh', label: 'Pin khả dụng' },
    ],
    colors: [
      { name: 'Đen Jet Black', hex: '#1f2123', image: image('VF9/CE11.webp') },
      { name: 'Trắng Infinity Blanc', hex: '#ededeb', image: image('VF9/CE18.webp') },
      { name: 'Xám Zenith Grey', hex: '#7c8083', image: image('VF9/CE1V.webp') },
      { name: 'Đỏ Crimson Red', hex: '#9d2630', image: image('VF9/CE1M.webp') },
      { name: 'Xanh Urban Mint', hex: '#9aa58e', image: image('VF9/CE1W.webp') },
      { name: 'Xanh Ivy Green', hex: '#2e483d', image: image('VF9/CE22.webp') },
      { name: 'Bạc Desat Silver', hex: '#b8b9b7', image: image('VF9/CE17.webp') },
    ],
    brochure: 'VF 9 Brochure · Eco / Plus',
    featured: true,
  },
  {
    id: 'herio-green',
    name: 'Herio Green',
    navName: 'Herio Green',
    category: 'fleet',
    body: 'eSUV dịch vụ',
    seats: '5 chỗ',
    price: 'Chính sách dành cho kinh doanh',
    tagline: 'Bền bỉ cho mỗi cuốc xe.',
    description: 'Thiết kế tối ưu cho tần suất vận hành cao, khoang hành khách thoáng và chi phí năng lượng dễ kiểm soát.',
    hero: image('Dịch vụ_Herio Green/Hero-new.webp'),
    intro: image('Dịch vụ_Herio Green/trắng.png'),
    gallery: [
      image('Dịch vụ_Herio Green/Banner-new.webp'),
      image('Dịch vụ_Herio Green/herio-green-section-3-1.webp'),
      image('Dịch vụ_Herio Green/parallax-2.webp'),
    ],
    specs: [
      { value: '326 km', label: 'Quãng đường NEDC' },
      { value: '100 kW', label: 'Công suất tối đa' },
      { value: '5 chỗ', label: 'Sức chứa' },
      { value: 'FWD', label: 'Dẫn động' },
    ],
    colors: [
      { name: 'Trắng', hex: '#e9e9e5', image: image('Dịch vụ_Herio Green/trắng.png') },
      { name: 'Đen', hex: '#222426', image: image('Dịch vụ_Herio Green/Đen.png') },
      { name: 'Đỏ', hex: '#94282d', image: image('Dịch vụ_Herio Green/đỏ.png') },
    ],
    brochure: 'Catalogue VinFast Herio Green',
    featured: false,
  },
  {
    id: 'minio-green',
    name: 'Minio Green',
    navName: 'Minio Green',
    category: 'fleet',
    body: 'Mini car dịch vụ',
    seats: '4 chỗ',
    price: 'Chính sách dành cho kinh doanh',
    tagline: 'Nhỏ gọn, xoay trở tức thì.',
    description: 'Chiếc xe nhỏ nhất dải Green, ưu tiên bán kính vận hành đô thị và mức tiêu thụ năng lượng thấp.',
    hero: image('Dịch vụ_MINIO Green/Minio.webp'),
    intro: image('Dịch vụ_MINIO Green/Minio.webp'),
    gallery: [
      image('Dịch vụ_MINIO Green/feature-exterior@2x.webp'),
      image('Dịch vụ_MINIO Green/feature-interior@2x.webp'),
      image('Dịch vụ_MINIO Green/gallery-featured-img3.webp'),
    ],
    specs: [
      { value: '210 km', label: 'Quãng đường NEDC' },
      { value: '30 kW', label: 'Công suất tối đa' },
      { value: '65 Nm', label: 'Mô-men xoắn' },
      { value: '18,3 kWh', label: 'Pin khả dụng' },
    ],
    colors: [],
    brochure: 'Minio Green Brochure · 09.01.2026',
    featured: false,
  },
  {
    id: 'nerio-green',
    name: 'Nerio Green',
    navName: 'Nerio Green',
    category: 'fleet',
    body: 'eSUV dịch vụ',
    seats: '5 chỗ',
    price: 'Chính sách dành cho kinh doanh',
    tagline: 'Không gian rộng, vận hành gọn.',
    description: 'Dòng xe dịch vụ hướng đến đội xe cần khoang hành khách dễ sử dụng và khả năng vận hành liên tục.',
    hero: image('Dịch vụ_Nerio Green/nerio-img-01.webp'),
    intro: image('Dịch vụ_Nerio Green/nerio-img-04.webp'),
    gallery: [
      image('Dịch vụ_Nerio Green/nerio-img-06.webp'),
      image('Dịch vụ_Nerio Green/nerio-img-09.webp'),
      image('Dịch vụ_Nerio Green/nerio-img-11.webp'),
    ],
    specs: [
      { value: '318 km', label: 'Quãng đường tham chiếu' },
      { value: '110 kW', label: 'Công suất tối đa' },
      { value: '5 chỗ', label: 'Sức chứa' },
      { value: 'FWD', label: 'Dẫn động' },
    ],
    colors: [],
    brochure: 'Catalogue VinFast Nerio Green',
    featured: false,
  },
  {
    id: 'limo-green',
    name: 'Limo Green',
    navName: 'Limo Green',
    category: 'fleet',
    body: 'MPV điện dịch vụ',
    seats: '7 chỗ',
    price: 'Chính sách dành cho kinh doanh',
    tagline: 'Rộng rãi cho mọi hành trình.',
    description: 'Thân xe dài, ba hàng ghế và tầm hoạt động phù hợp cho vận chuyển hành khách đường dài.',
    hero: image('Dịch vụ_Limo Green/footer.webp'),
    intro: image('Dịch vụ_Limo Green/img_slider.webp'),
    gallery: [
      image('Dịch vụ_Limo Green/limo-green-3.webp'),
      image('Dịch vụ_Limo Green/limo-green-4.webp'),
      image('Dịch vụ_Limo Green/limo-green-5.webp'),
    ],
    specs: [
      { value: '450 km', label: 'Quãng đường NEDC' },
      { value: '150 kW', label: 'Công suất tối đa' },
      { value: '280 Nm', label: 'Mô-men xoắn' },
      { value: '60,13 kWh', label: 'Pin khả dụng' },
    ],
    colors: [],
    brochure: 'Limo Green Brochure · 09.01.2026',
    featured: false,
  },
  {
    id: 'ec-van',
    name: 'EC Van',
    navName: 'EC Van',
    category: 'fleet',
    body: 'Van điện chở hàng',
    seats: '2 chỗ',
    price: 'Chính sách dành cho kinh doanh',
    tagline: 'Giao hàng bằng năng lượng sạch.',
    description: 'Khoang hàng 2,6 m³, bán kính quay vòng 4,85 m và hệ dẫn động cầu sau cho nhịp giao vận đô thị.',
    hero: image('Dịch vụ_ EC Van/banner.webp'),
    intro: image('Dịch vụ_ EC Van/ecvan-jade.webp'),
    gallery: [
      image('Dịch vụ_ EC Van/ecvan-img-01.webp'),
      image('Dịch vụ_ EC Van/ecvan-img-03.webp'),
      image('Dịch vụ_ EC Van/ecvan-jade-02.webp'),
    ],
    specs: [
      { value: '175 km', label: 'Quãng đường NEDC' },
      { value: '30 kW', label: 'Công suất tối đa' },
      { value: '2,6 m³', label: 'Khoang hàng' },
      { value: '18,3 kWh', label: 'Pin khả dụng' },
    ],
    colors: [],
    brochure: 'EC Van Brochure · 04.07.2026',
    featured: false,
  },
  {
    id: 'ebus',
    name: 'VinFast eBus',
    navName: 'eBus',
    category: 'fleet',
    body: 'Xe buýt điện',
    seats: '60–90 hành khách',
    price: 'Liên hệ giải pháp vận tải',
    tagline: 'Thành phố chuyển động êm hơn.',
    description: 'Nền tảng xe buýt điện cho vận tải công cộng với cấu hình chiều dài và sức chứa theo nhu cầu vận hành.',
    hero: image('Dịch vụ_EBus/ebus-img-01.webp'),
    intro: image('Dịch vụ_EBus/ebus-img-02.webp'),
    gallery: [
      image('Dịch vụ_EBus/ebus-img-03.webp'),
      image('Dịch vụ_EBus/ebus-img-05.webp'),
      image('Dịch vụ_EBus/ebus-img-06.webp'),
    ],
    specs: [
      { value: '8,61–12,11 m', label: 'Chiều dài thân xe' },
      { value: '359–422 kWh', label: 'Dung lượng pin' },
      { value: '120–140 kW', label: 'Công suất sạc' },
      { value: '60–90', label: 'Sức chứa hành khách' },
    ],
    colors: [],
    brochure: 'VinFast eBus Brochure · 09.2025',
    featured: false,
  },
]

const assetFoldersByCar = {
  vf3: ['VF3'],
  vf5: ['VF5'],
  vf6: ['VF6'],
  vf7: ['VF7'],
  'vf-mpv-7': ['VF7 FMP'],
  vf8: ['VF8'],
  'vf8-the-he-moi': ['VF8 All the new'],
  vf9: ['VF9'],
  'herio-green': ['Dịch vụ_Herio Green'],
  'minio-green': ['Dịch vụ_MINIO Green'],
  'nerio-green': ['Dịch vụ_Nerio Green'],
  'limo-green': ['Dịch vụ_Limo Green'],
  'ec-van': ['Dịch vụ_ EC Van'],
  ebus: ['Dịch vụ_EBus'],
}

// Ảnh dùng riêng cho luồng đặt lịch của ViVi: bắt buộc là ảnh studio của mẫu xe
// (nền trong suốt hoặc nền trắng phẳng), không dùng ảnh banner/bối cảnh vì khi đặt
// cạnh tên xe cỡ lớn, khối nền của ảnh sẽ đè lên chữ.
//   mode: 'cutout' → ảnh PNG/WebP đã tách nền, xe "nổi" tự do trên nền studio.
//   mode: 'plate'  → ảnh studio nền trắng phẳng, đặt trong thẻ trắng bo góc.
//   mode: 'photo'  → chưa có ảnh studio trong kho ảnh, đóng khung ảnh bối cảnh lại.
// TODO [BACKEND]: GET /api/v1/vehicles cần trả thêm `studioImageUrl` và
// `studioImageMode` ('cutout' | 'plate' | 'photo') cho từng mẫu xe để thay bảng này.
// Với `cutout`, file bắt buộc có alpha thật, không có nền/viền ảnh và xe hướng đầu
// sang phải để preset drive-left-to-right chạy đúng; backend/CDN không được tự flatten PNG.
// Limo Green và eBus vẫn cần bổ sung ảnh tách nền từ hệ thống media backend.
const studioShotByCar = {
  vf3: { src: image('VF3/xám.png'), mode: 'cutout' },
  vf5: { src: image('VF5/trắng.webp'), mode: 'cutout' },
  vf6: { src: vf6StudioShot, mode: 'cutout' },
  vf7: { src: image('VF7/product-CE18.webp'), mode: 'cutout' },
  'vf-mpv-7': { src: vfMpv7StudioShot, mode: 'cutout' },
  vf8: { src: image('VF8/product-CE18.webp'), mode: 'cutout' },
  'vf8-the-he-moi': { src: image('VF8 All the new/VF8PH-23.webp'), mode: 'cutout' },
  // VF 9 và Nerio Green: ảnh gốc còn bệ trắng nên đã tách nền lại, xem src/assets.
  vf9: { src: vf9StudioShot, mode: 'cutout' },
  'herio-green': { src: image('Dịch vụ_Herio Green/trắng.png'), mode: 'cutout' },
  'minio-green': { src: image('Dịch vụ_MINIO Green/Minio.webp'), mode: 'cutout' },
  'nerio-green': { src: nerioStudioShot, mode: 'cutout' },
  'limo-green': { src: limoStudioShot, mode: 'photo' },
  'ec-van': { src: image('Dịch vụ_ EC Van/ecvan-jade.webp'), mode: 'cutout' },
  ebus: { src: image('Dịch vụ_EBus/ebus-img-01.webp'), mode: 'photo' },
}

const motionImageByCar = {
  vf3: image('VF3/xám.png'),
  vf5: image('VF5/trắng.webp'),
  vf6: vf6StudioShot,
  vf7: image('VF7/product-CE1M.webp'),
  'vf-mpv-7': vfMpv7StudioShot,
  vf8: image('VF8/product-CE1M.webp'),
  'vf8-the-he-moi': image('VF8 All the new/car-left.webp'),
  // Ảnh CE1M gốc còn vùng canvas trắng cao; dùng bản PNG alpha đã crop để
  // hero VF 9 hoà vào nền trang giống các mẫu xe còn lại.
  vf9: vf9StudioShot,
  'herio-green': image('Dịch vụ_Herio Green/trắng.png'),
  'minio-green': image('Dịch vụ_MINIO Green/Minio.webp'),
  'limo-green': image('Dịch vụ_Limo Green/limo-green-3.webp'),
  'ec-van': image('Dịch vụ_ EC Van/ecvan-jade.webp'),
}

// TODO [BACKEND/VEHICLE FILM]: Replace these bundled URLs with the optional
// `presentationFilm` object from GET /api/v1/vehicles/{id}. The API supplies
// media/content only (url, posterUrl, mimeType, width, height, duration,
// transcript/captions, revision); layout, controls and GSAP timing remain here.
// VF 8 and VF 8 Thế hệ mới currently use two separately uploaded files that are
// byte-identical. Keep them mapped independently so CMS revisions can diverge later.
const presentationFilmByCar = {
  vf8: {
    src: vf8PresentationFilm,
    poster: image('VF8/banner.webp'),
    eyebrow: 'VF 8 trong chuyển động',
    title: 'Ánh sáng đi qua từng bề mặt.',
    copy: 'Một thước phim liền mạch để quan sát tỷ lệ, đường vai và dấu ấn ngoại thất của VF 8 khi chiếc xe thực sự chuyển động.',
  },
  'vf8-the-he-moi': {
    src: vf8NewPresentationFilm,
    poster: image('VF8 All the new/VF8PH-23.webp'),
    eyebrow: 'Một nhịp nhìn mới',
    title: 'Tinh giản, nhưng không đứng yên.',
    copy: 'Chuyển động điện ảnh làm nổi bật cách bề mặt và ánh sáng định hình diện mạo VF 8 Thế hệ mới.',
  },
  vf9: {
    src: vf9PresentationFilm,
    poster: image('VF9/interior-first-sight.webp'),
    eyebrow: 'Bên trong VF 9',
    title: 'Khoang lái mở ra trong một nhịp phim.',
    copy: 'Góc máy đi từ vị trí người lái qua màn hình trung tâm, cho cảm nhận trực tiếp hơn về cách các chi tiết được đặt trong tầm quan sát.',
  },
}

// Mỗi chương ảnh trên trang chi tiết xe được gán đúng loại ảnh, thay vì gán tiêu đề
// theo thứ tự khiến ảnh nội thất bị chú thích là "hình khối".
const chapterLibrary = {
  exterior: ['Hình khối', 'Tỷ lệ tổng thể và đường nét tạo nên nhận diện đầu tiên.'],
  profile: ['Đường nét bên hông', 'Dáng xe nhìn ngang cho thấy tỷ lệ và chiều dài cơ sở.'],
  rear: ['Góc sau', 'Cụm đèn hậu và phần đuôi hoàn thiện nhận diện của dòng xe.'],
  cockpit: ['Khoang lái', 'Vô lăng, màn hình và những thao tác thường dùng nằm trong tầm với.'],
  cabin: ['Không gian hành khách', 'Chỗ ngồi, vật liệu và sự thoải mái dành cho người đi cùng.'],
  rearSeats: ['Hàng ghế sau', 'Chỗ ngồi phía sau và không gian dành cho hành khách đường dài.'],
  technology: ['Cấu trúc kỹ thuật', 'Bố trí pin, khung gầm và hệ truyền động bên dưới thân xe.'],
  drive: ['Trên đường', 'Chiếc xe trong bối cảnh vận hành thực tế.'],
  charging: ['Nạp năng lượng', 'Giải pháp sạc đi kèm cho những hành trình dài.'],
  cargo: ['Khoang hàng', 'Không gian chở hàng và khả năng xoay trở khi giao vận.'],
}

// [loại chương, ảnh, nền thẻ]. 'light' cho ảnh studio nền sáng, 'dark' cho ảnh bối cảnh.
// TODO [BACKEND]: GET /api/v1/vehicles/{id}/media nên trả kèm `mediaType` cho từng ảnh
// (exterior | cockpit | cabin | technology | charging | cargo) để bảng này sinh tự động.
const chaptersByCar = {
  vf3: [
    ['exterior', 'VF3/2..png', 'light'],
    ['cockpit', 'VF3/3..jpg', 'dark'],
    ['rear', 'VF3/4.png', 'light'],
  ],
  vf5: [
    ['exterior', 'VF5/trắng.webp', 'light'],
    ['cockpit', 'VF5/2.webp', 'dark'],
    ['cabin', 'VF5/4..webp', 'dark'],
  ],
  vf6: [
    ['exterior', vf6StudioShot, 'light'],
    ['cockpit', 'VF6/interior-vf6-2.jpg', 'dark'],
    ['technology', 'VF6/technology-vf6-3.jpg', 'light'],
  ],
  vf7: [
    ['drive', 'VF7/vf7-uu-diem-3.webp', 'dark'],
    ['cockpit', 'VF7/vf7-noi-that-compare-left.webp', 'dark'],
    ['cabin', 'VF7/vf7-noi-that-overview.webp', 'dark'],
  ],
  'vf-mpv-7': [
    ['exterior', vfMpv7StudioShot, 'light'],
    ['cabin', 'VF7 FMP/D_03.webp', 'dark'],
    ['cockpit', 'VF7 FMP/D_05.webp', 'dark'],
  ],
  vf8: [
    ['drive', 'VF8/banner.webp', 'dark'],
    ['cockpit', 'VF8/volang.webp', 'dark'],
    ['cabin', 'VF8/gheda-vegan.webp', 'dark'],
  ],
  'vf8-the-he-moi': [
    ['drive', 'VF8 All the new/car-left.webp', 'dark'],
    ['cockpit', 'VF8 All the new/ex-right.webp', 'dark'],
    ['cabin', 'VF8 All the new/ex-ex5-e.png', 'light'],
  ],
  vf9: [
    ['charging', 'VF9/charging-tag-line-bg.webp', 'dark'],
    ['cockpit', 'VF9/int-slide-1.webp', 'dark'],
    ['rearSeats', 'VF9/int-slide-4.webp', 'dark'],
  ],
  'herio-green': [
    ['drive', 'Dịch vụ_Herio Green/herio-green-section-3-3.webp', 'dark'],
    ['cockpit', 'Dịch vụ_Herio Green/parallax-4.webp', 'dark'],
    ['rearSeats', 'Dịch vụ_Herio Green/parallax-1.webp', 'dark'],
  ],
  'minio-green': [
    ['rear', 'Dịch vụ_MINIO Green/feature-exterior@2x.webp', 'light'],
    ['cockpit', 'Dịch vụ_MINIO Green/interior-gallery-left@2x.webp', 'light'],
    ['rearSeats', 'Dịch vụ_MINIO Green/interior-gallery-right@2x.webp', 'light'],
  ],
  'nerio-green': [
    ['exterior', 'Dịch vụ_Nerio Green/nerio-img-04.webp', 'light'],
    ['profile', 'Dịch vụ_Nerio Green/nerio-img-11.webp', 'light'],
    ['rear', 'Dịch vụ_Nerio Green/nerio-img-06.webp', 'light'],
  ],
  'limo-green': [
    ['exterior', limoStudioShot, 'dark'],
    ['cockpit', 'Dịch vụ_Limo Green/img_slider.webp', 'dark'],
    ['cabin', 'Dịch vụ_Limo Green/limo-green-5.webp', 'dark'],
  ],
  'ec-van': [
    ['exterior', 'Dịch vụ_ EC Van/ecvan-jade.webp', 'light'],
    ['cargo', 'Dịch vụ_ EC Van/ecvan-img-04.webp', 'light'],
    ['drive', 'Dịch vụ_ EC Van/ecvan-banner-01.webp', 'dark'],
  ],
  ebus: [
    ['drive', 'Dịch vụ_EBus/ebus-img-01.webp', 'dark'],
    ['cabin', 'Dịch vụ_EBus/ebus-img-03.webp', 'dark'],
  ],
}

// Ảnh đã import sẵn (dạng URL) thì dùng thẳng, còn lại là đường dẫn trong kho ảnh.
const resolveAsset = (value) => (value.startsWith('/') || value.startsWith('http') ? value : image(value))

export const cars = catalogue.map((car) => {
  const chapters = (chaptersByCar[car.id] || [])
    .map(([key, source, tone]) => ({
      key,
      src: resolveAsset(source),
      tone: tone || 'dark',
      title: chapterLibrary[key][0],
      copy: chapterLibrary[key][1],
    }))
    .filter((chapter) => chapter.src)
  const gallery = chapters.length ? chapters.map((chapter) => chapter.src) : car.gallery
  const colorAssets = car.colors.filter((color) => color.image).map((color) => ({ src: color.image }))
  return {
    ...car,
    gallery,
    chapters,
    motionImage: motionImageByCar[car.id] || '',
    studioShot: studioShotByCar[car.id] || { src: car.intro || car.hero, mode: 'photo' },
    presentationFilm: presentationFilmByCar[car.id]?.src ? presentationFilmByCar[car.id] : null,
    media: uniqueAssets([
      ...gallery.map((src) => ({ src })),
      ...assetsIn(...assetFoldersByCar[car.id]),
      ...colorAssets,
    ]).map((asset, index) => ({ ...asset, label: `Góc nhìn ${String(index + 1).padStart(2, '0')}` })),
  }
})

export const getCar = (id) => cars.find((car) => car.id === id)

export const carGroups = [
  {
    id: 'personal',
    label: 'Động cơ điện',
    description: 'Từ mini eSUV đến SUV điện ba hàng ghế.',
  },
  {
    id: 'fleet',
    label: 'Dòng xe dịch vụ',
    description: 'Dải Green, giao vận và vận tải công cộng.',
  },
]
