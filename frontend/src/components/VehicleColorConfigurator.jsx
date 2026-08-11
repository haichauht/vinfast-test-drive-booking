/**
 * VehicleColorConfigurator — section chọn màu dùng chung cho mọi trang model.
 *
 * FRONTEND/BACKEND CONTRACT:
 * - Bắt buộc: color.name, color.hex, color.image.
 * - Tuỳ chọn: color.group, color.groupLabel để chia nhóm màu; color.secondaryHex
 *   (hoặc color.hexes) để vẽ swatch hai tông. Thiếu các field tuỳ chọn thì UI
 *   giữ một dải màu phẳng, không tự suy đoán hay tạo dữ liệu sản phẩm.
 * - vehicle.specs tiếp tục dùng schema { label, value }; field thiếu tự ẩn.
 *
 * State chọn màu được giữ cục bộ như ColorExplorer trước đây. Route đặt lịch và
 * mapping color -> image không đổi; component chỉ chuẩn hoá hierarchy và responsive.
 */
import { useState } from 'react'
import { IslandButton } from './IslandButton'
import { SmartImage } from './SmartImage'

const GROUP_LABELS = {
  standard: 'Màu tiêu chuẩn',
  premium: 'Màu nâng cao',
  advanced: 'Màu nâng cao',
  special: 'Màu đặc biệt',
  'two-tone': 'Màu hai tông',
  other: 'Màu khác',
}

function getSwatchBackground(color) {
  const tones = Array.isArray(color.hexes)
    ? color.hexes.filter(Boolean).slice(0, 2)
    : [color.hex, color.secondaryHex || color.hex2].filter(Boolean)

  if (tones.length > 1) {
    return `linear-gradient(135deg, ${tones[0]} 0 48%, ${tones[1]} 52% 100%)`
  }

  return tones[0] || '#d7d9d8'
}

function groupColors(colors) {
  const hasExplicitGroups = colors.some((color) => color.group)
  if (!hasExplicitGroups) return [{ key: 'all', label: '', colors }]

  return colors.reduce((groups, color) => {
    const key = color.group || 'other'
    let group = groups.find((item) => item.key === key)
    if (!group) {
      group = {
        key,
        label: color.groupLabel || GROUP_LABELS[key] || key,
        colors: [],
      }
      groups.push(group)
    }
    group.colors.push(color)
    return groups
  }, [])
}

export function VehicleColorConfigurator({ vehicle }) {
  const availableColors = (vehicle.colors || []).filter((color) => color.image)
  const visibleSpecs = (vehicle.specs || []).filter((spec) => spec?.value && spec?.label).slice(0, 4)
  const [selectedIndex, setSelectedIndex] = useState(0)
  const selected = availableColors[selectedIndex]

  if (availableColors.length < 2) return null

  const indexedColors = availableColors.map((color, index) => ({ ...color, sourceIndex: index }))
  const colorGroups = groupColors(indexedColors)

  return (
    <section className="color-explorer" aria-labelledby={`color-title-${vehicle.id}`}>
      <div className="section-frame">
        <div className="color-explorer__stage">
          <div className="color-explorer__grid">
            <header className="color-explorer__copy">
              <p className="eyebrow">{vehicle.name} · Bảng màu ngoại thất</p>
              <h2 id={`color-title-${vehicle.id}`}>{vehicle.tagline}</h2>
              {vehicle.description && <p>{vehicle.description}</p>}
            </header>

            {visibleSpecs.length > 0 && (
              <dl className="color-explorer__specs" aria-label={`Thông số nổi bật ${vehicle.name}`}>
                {visibleSpecs.map((spec) => (
                  <div className="color-explorer__spec" key={spec.label}>
                    <dt>{spec.label}</dt>
                    <dd>{spec.value}</dd>
                  </div>
                ))}
              </dl>
            )}

            <div className="color-explorer__visual" aria-live="polite">
              <SmartImage
                key={selected.image}
                className="color-explorer__image"
                src={selected.image}
                alt={`${vehicle.name} màu ${selected.name}`}
              />
            </div>

            <div className="color-explorer__palette">
              <p className="color-explorer__name">
                <span>Màu đang chọn</span>
                <strong>{selected.name}</strong>
              </p>

              <div className={`color-explorer__groups ${colorGroups.length > 1 ? 'has-multiple-groups' : ''}`}>
                {colorGroups.map((group) => (
                  <div className="color-explorer__group" key={group.key}>
                    {group.label && <p>{group.label}</p>}
                    <div className="color-explorer__swatches" role="radiogroup" aria-label={group.label || `Chọn màu ${vehicle.name}`}>
                      {group.colors.map((color) => {
                        const isSelected = selectedIndex === color.sourceIndex
                        return (
                          <button
                            key={`${color.name}-${color.sourceIndex}`}
                            className={isSelected ? 'is-active' : ''}
                            type="button"
                            role="radio"
                            aria-checked={isSelected}
                            aria-label={`${color.name}${isSelected ? ', đang chọn' : ''}`}
                            title={color.name}
                            onClick={() => setSelectedIndex(color.sourceIndex)}
                          >
                            <span style={{ background: getSwatchBackground(color) }} aria-hidden="true" />
                          </button>
                        )
                      })}
                    </div>
                  </div>
                ))}
              </div>

              <div className="color-explorer__action">
                <IslandButton to={`/booking?car=${vehicle.id}`} variant="dark">
                  Đặt lịch lái thử
                </IslandButton>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
