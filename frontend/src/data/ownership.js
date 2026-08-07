import { brochureByKeyword, commonMedia, vehicleAssetByName } from '../media/assets'

const chargingImage = (fileName) => vehicleAssetByName('Trạm sạc', fileName)

// TODO [BACKEND/CMS]: Replace the brochure-backed fixtures below with
// GET /api/v1/content/ownership?locale=vi-VN. The API should return a source
// revision/effectiveAt for every policy block so legal copy can be audited.
export const ownershipMedia = {
  afterSalesHero: commonMedia.afterSalesHero,
  afterSalesConsultation: commonMedia.afterSalesConsultation,
  afterSalesBrochure: brochureByKeyword('bảo hành'),
  chargingBrochure: brochureByKeyword('pin ô tô'),
  chargingStationDay: chargingImage('pin-tramsac-5_1660273699.png.webp'),
  chargingStationNight: chargingImage('pin-tramsac-6_1660273722.png.webp'),
  charger250: chargingImage('pin-tramsac-7_1660273744.png.webp'),
  charger150: chargingImage('pin-tramsac-8_1660273763.png.webp'),
  charger60: chargingImage('img_1705981400.png.webp'),
  charger30: chargingImage('pin-tramsac-9_1660273785.png.webp'),
  wallCharger: chargingImage('pin-tramsac-11_1660273822.png.webp'),
  portableCharger: chargingImage('pin-tramsac-12_1660273840.png.webp'),
  portableChargerAlt: chargingImage('pin-tramsac-13_1660273860.png.webp'),
  availableIndicator: chargingImage('pin-tramsac-14_1660273636.png.webp'),
}

export const highVoltageWarranty = [
  {
    term: '10 năm',
    distance: '200.000 km',
    models: 'VF 8, VF 9, Lạc Hồng 900 LX',
  },
  {
    term: '8 năm',
    distance: '160.000 km',
    models: 'VF 3, VF 5, VF 6, VF 7, VF Minio Green, VF Herio Green, VF MPV7, VF e34, VF Nerio Green, VF Limo Green, VF 8 The All New',
  },
  {
    term: '7 năm',
    distance: '160.000 km',
    models: 'VF EC Van',
  },
]
export const chargingUnits = [
  {
    power: '250 kW',
    name: 'Sạc siêu nhanh DC',
    image: ownershipMedia.charger250,
    facts: ['Tủ đứng', '1 cổng / trụ', '200–1.000 VDC', 'IP54 · −30°C đến 55°C'],
  },
  {
    power: '150 kW',
    name: 'Sạc siêu nhanh DC',
    image: ownershipMedia.charger150,
    facts: ['Tủ đứng', '2 cổng / trụ', '200–1.000 VDC', 'IP54'],
  },
  {
    power: '60 kW',
    name: 'Sạc nhanh DC',
    image: ownershipMedia.charger60,
    facts: ['Tủ đứng', '2 cổng / trụ', '200–1.000 VDC', 'IP54'],
  },
  {
    power: '30 kW',
    name: 'Sạc nhanh DC',
    image: ownershipMedia.charger30,
    facts: ['Treo tường hoặc tủ đứng', '1 cổng / trụ', 'CAN Protocol', 'IP54'],
  },
]
