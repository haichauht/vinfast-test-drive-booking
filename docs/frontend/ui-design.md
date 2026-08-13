# Frontend UI Design Audit

Nguon tham chieu UI/UX: `origin/NguyenHoangMinh`.

Ghi chu audit: khong checkout truc tiep branch reference trong working tree hien tai vi repo dang co thay doi rieng va branch reference co mot filename PDF chua ky tu `|`, gay loi voi Git for Windows khi export/checkout day du. Audit nay duoc thuc hien bang `git grep` va `git show` tren `origin/NguyenHoangMinh`, tap trung vao `frontend/src`.

Pham vi loai tru: booking UI khong duoc audit/refactor trong tai lieu nay theo yeu cau moi. Route `/booking` van duoc ghi nhan vi la dich den cua navigation/CTA, nhung khong phan tich form, modal, assistant flow hoac workspace booking.

## Route Inventory

Reference branch:

| Route | Page | Ghi chu |
| --- | --- | --- |
| `/` | `HomePage` | Trang chu, model rail, ecosystem, technology story, testimonial carousel, CTA |
| `/cars/:carId` | `CarDetailPage` | Template chi tiet xe dung chung cho moi model |
| `/booking` | `BookingPage` | Co route, bo qua UI audit |
| `/after-sales` | `AfterSalesPage` | Trang hau mai/chinh sach bao hanh |
| `/charging` | `ChargingPage` | Trang pin va tram sac |
| `/agent` | redirect `/booking` | CTA ViVi |
| `/home` | redirect `/` | Alias |
| `*` | redirect `/` | Fallback |

Current refactor branch:

| Route | Page | Trang thai can canh chinh |
| --- | --- | --- |
| `/` | `HomePage` | Can giu layout/animation reference, data lay qua backend |
| `/cars/:carId` | dang redirect booking trong `App.jsx` | Sai so voi reference; can tro ve `CarDetailPage` hoac alias sang `/models/:carId` |
| `/models/:carId` | `CarDetailPage` | Route refactor moi; co the giu nhu alias bo sung |
| `/booking` | `BookingPage` | Khong trong pham vi UI audit nay |
| `/after-sales` | `AfterSalesPage` | Can map UI reference vao data backend |
| `/charging` | `ChargingPage` | Can map UI reference vao data backend |
| `/agent`, `/home`, `*` | redirect | Giu hanh vi reference |

## Page Component Mapping

### `/` -> `HomePage`

```
HomePage
|-- AppShell
|   |-- Brand
|   |-- ProductMegaMenu
|   |-- MobileMenuOverlay
|   `-- IslandButton booking CTA
|-- HomeHero
|   |-- SmartImage hero vehicle
|   `-- IslandButton group
|-- RoadChapter
|-- FactoryFilm
|-- FactoryOrigin
|-- ModelMarquee
|-- ModelsSection
|   |-- ModelTabs
|   |-- VehicleRail
|   `-- VehicleTile
|-- FlagshipPassage
|   `-- FlagshipCard
|-- ViviIntro
|-- ScrollDrive
|-- OwnershipBento
|-- TechnologyStory
|   `-- TechnologyPanel
|-- VoiceCarousel
|-- HomeAction
`-- SiteFooter
```

Important behavior:

- Hero car slides from left to final anchor on reload, then drifts vertically on scroll.
- Hero copy reveals with blur/y stagger.
- Product rail scrolls horizontally; arrow controls use `scrollBy`.
- Model tabs switch personal/fleet vehicles and respond to `#models-electric` / `#models-service`.
- Vehicle cards link to vehicle detail, not booking.
- ScrollDrive car moves left-to-right across road while scrolling.
- Technology intro is pinned on desktop and panels reveal by scroll.
- Voice carousel changes quote with previous/next buttons.
- Mega menu opens by click, closes by outside pointer/Escape/navigation.
- Mobile menu locks body scroll and staggers overlay links.
- Responsive layout collapses rails/grids and enables mobile menu below tablet breakpoints.

### `/cars/:carId` and `/models/:carId` -> `VehicleDetailTemplate`

```
VehicleDetailTemplate
|-- AppShell
|-- DetailHero
|   |-- BackLink
|   |-- VehicleMotionImage
|   `-- HeroActions
|-- OptionalLimoFilm
|-- TestDriveNudge
|-- ManifestoText
|-- OptionalModelFilm
|-- DetailSpecs
|   `-- SpecStrip
|-- DetailStory
|   |-- StoryAside
|   `-- DetailChapter[]
|-- DetailMediaGrid
|-- ColorExplorer
|-- BrochureNote
|-- DetailAction
|-- SiteFooter
`-- DetailBookingDock
```

Important behavior:

- Mot template duy nhat dung cho VF3, VF5, VF6, VF7, VF MPV 7, VF8, VF8 moi, VF9 va cac dong Green.
- Xe trong hero truot tu trai sang vi tri moc khi reload; sau do scroll chi dich nhe tu moc, khong reset moc.
- Copy hero reveal sau xe bang stagger/blur.
- `ManifestoText` tach tung tu thanh `.manifesto-word` va tang opacity theo scroll.
- Optional model film co scroll reveal stage/video/copy.
- Chapter cards scale/opacity reveal theo scroll.
- Media grid scale/opacity reveal theo scroll va moi card phai co caption `Goc nhin 01`, `Goc nhin 02`, ...
- ColorExplorer chi hien khi co it nhat 2 mau; click swatch doi anh xe va active state.
- TestDriveNudge hien sau delay, co session dismissal theo vehicle id.
- Booking CTA trong detail co the truyen `?car=<id>` vi nguoi dung dang xem xe cu the.
- Next vehicle CTA phai di toi route detail cua model tiep theo.
- Responsive: hero/image/action dock khong de text overlap; media/story grid chuyen thanh mot cot tren mobile.

### `/charging` -> `ChargingPage`

```
ChargingPage
|-- AppShell
|-- OwnershipHero
|-- OwnershipSubnav
|-- ChargingNotice
|-- ChargingNetwork
|   |-- NetworkStats
|   `-- NetworkPlaceGrid
|-- ChargingPrice
|   `-- OverstayFees
|-- ChargerLineup
|   `-- ChargerCard[]
|-- HomeCharging
|-- BatteryCare
|   `-- BatteryRuleAccordion
|-- LegacyRental
|-- OwnershipContact
`-- OwnershipFooter
```

Important behavior:

- Hero background image parallax scale on scroll.
- Intro text reveals with y/opacity stagger.
- Subnav uses anchor links to sections.
- Charger intro is pinned on desktop while charger cards scroll.
- Charger cards and network places reveal once when entering viewport.
- Battery rules are native `details`; first item open by default.
- Responsive: policy grids, charger cards, stats and contact actions collapse to one column.

### `/after-sales` -> `AfterSalesPage`

```
AfterSalesPage
|-- AppShell
|-- OwnershipHero
|-- OwnershipSubnav
|-- PolicyIntro
|   `-- PrincipleCard[]
|-- ElectronicBook
|-- BatteryWarranty
|   `-- BatteryTerm[]
|-- PartsPolicy
|   `-- PartsBento
|-- PolicyAccordion
|-- PolicyFAQ
|-- OwnershipContact
`-- OwnershipFooter
```

Important behavior:

- Hero media parallax scale and intro reveal match `ChargingPage`.
- Policy cards reveal once on scroll.
- Subnav anchors jump to policy sections.
- Accordion/FAQ use native `details`; first exclusion open by default.
- Contact actions are tel/mail links with icon+text layout.
- Responsive behavior shares the `OwnershipPage` system with charging.

### `/booking`

Route ton tai va nhan CTA tu nav/home/detail. UI booking excluded from this audit.

## Reusable Components

Can giu/tach thanh reusable components theo UI reference, nhung nap data tu backend API:

- `AppShell`: fixed pill navigation, mega menu, mobile overlay, skip link, booking CTA.
- `Brand`: logo lockup.
- `IslandButton`: rounded CTA with arrow icon and variants `dark`, `light`, `blue`, `ghost-light`.
- `SmartImage`: image skeleton/error handling.
- `Reveal`: scroll reveal wrapper using GSAP + ScrollTrigger.
- `SiteFooter`: shared footer used by home and detail.
- `VehicleShot`: studio image renderer with modes `cutout`, `plate`, `photo`.
- `VehicleRail` and `VehicleTile`: horizontal product rail.
- `ModelTabs`: category switcher.
- `VehicleDetailTemplate`: shared model detail page.
- `ColorExplorer`: color selector for vehicles with color media.
- `DetailBookingDock`: sticky bottom booking CTA on detail.
- `OwnershipHero`: shared hero for charging/after-sales.
- `OwnershipSubnav`: sticky section anchor nav.
- `PolicyCard`: reusable cards for policy/ownership sections.
- `AccordionList`: native details/summary list.
- `MediaFeature`: image/video section with veil/caption.

## Reusable Templates

### `VehicleDetailTemplate + VehicleData`

All model detail routes must share one template. Differences are data only:

- identity: `id`, `name`, `navName`, `body`, `seats`, `price`, `tagline`, `description`
- media: `motionImage`, `hero`, `intro`, `studioShot`, `gallery`, `media`, `actionMedia`, optional `presentationFilm`
- content: `specs`, `chapters`, `colors`, `brochure`
- behavior flags: `testDriveEligible`, optional `hasLimoFilm`

Do not create `VF6Page`, `VF7Page`, `VF8Page` unless a page has unique structure that cannot be expressed by data.

### `OwnershipPageTemplate + OwnershipData`

`/charging` and `/after-sales` share:

- `OwnershipHero`
- sticky `OwnershipSubnav`
- large policy/info sections
- card grids
- accordion blocks
- contact/footer area
- same hero reveal/parallax language

They should share primitives even if not a single monolithic template.

### `HomeSectionTemplate`

Home should remain composed of named sections, but repeated patterns should be components:

- section heading
- media feature
- bento/card grid
- horizontal vehicle list
- dark CTA section

## Animation And Interaction Contract

GSAP timing/selectors live in frontend. Backend may provide only data/preset names, not executable animation code.

Key animation rules to preserve:

- Respect `prefers-reduced-motion`; set final states with no animation.
- Page route change scrolls to hash target or top.
- Home hero vehicle reload animation: `xPercent` from negative to `0`, opacity 0 to 1.
- Detail hero vehicle reload animation: slide from left to anchor. Scroll animation starts from anchor and moves slightly right.
- ScrollTrigger animations use scrub for parallax/motion sections and once-style reveals for cards.
- Desktop-only pinned sections use `gsap.matchMedia`.
- Text reveal can use blur/y/opacity stagger.
- Media/card reveal uses scale and opacity.
- Hover transitions live in CSS: tile lift, arrow color/position, image scale.
- Native `details` controls are used for accordion behavior.

## Navigation And User Flow

Expected reference flow:

- Navbar product mega menu anchors to home model sections.
- Home vehicle cards and arrow affordances navigate to detail route: `/cars/:carId` in reference, `/models/:carId` may be kept as alias in refactor.
- Top booking CTA navigates to `/booking` without forcing a fixed vehicle when not in vehicle context.
- Vehicle detail booking CTA may navigate to `/booking?car=<carId>`.
- Detail next model CTA navigates to another detail route.
- `/agent` redirects to `/booking`.
- `/home` redirects to `/`.

Known current mismatch to fix after this design:

- Current `App.jsx` redirects `/cars/:carId` to `/booking?car=...`; this conflicts with reference. It should render detail or redirect to `/models/:carId`.

## Proposed Frontend Structure

```text
frontend/src/
|-- api/
|   |-- client.js
|   |-- vehicles.js
|   |-- content.js
|   `-- adapters.js
|-- components/
|   |-- shell/
|   |   |-- AppShell.jsx
|   |   |-- ProductMegaMenu.jsx
|   |   `-- MobileMenuOverlay.jsx
|   |-- ui/
|   |   |-- Brand.jsx
|   |   |-- IslandButton.jsx
|   |   |-- Reveal.jsx
|   |   `-- SmartImage.jsx
|   |-- vehicle/
|   |   |-- VehicleRail.jsx
|   |   |-- VehicleTile.jsx
|   |   |-- VehicleShot.jsx
|   |   |-- VehicleDetailTemplate.jsx
|   |   |-- ColorExplorer.jsx
|   |   |-- DetailBookingDock.jsx
|   |   `-- DetailMediaGrid.jsx
|   |-- ownership/
|   |   |-- OwnershipHero.jsx
|   |   |-- OwnershipSubnav.jsx
|   |   |-- PolicyCard.jsx
|   |   `-- AccordionList.jsx
|   `-- SiteFooter.jsx
|-- hooks/
|   `-- useSiteData.js
|-- pages/
|   |-- HomePage.jsx
|   |-- CarDetailPage.jsx
|   |-- ChargingPage.jsx
|   |-- AfterSalesPage.jsx
|   `-- BookingPage.jsx
|-- media/
|   `-- assets.js
|-- styles/
|   |-- base.css
|   |-- shell.css
|   |-- home.css
|   |-- vehicle-detail.css
|   `-- ownership.css
|-- App.jsx
`-- main.jsx
```

Migration principle:

- UI/UX follows `origin/NguyenHoangMinh`.
- Data source follows current refactor: backend API via hooks/adapters.
- Components/templates are extracted by structure, not by model name.
- Booking UI is left out of this refactor pass.
