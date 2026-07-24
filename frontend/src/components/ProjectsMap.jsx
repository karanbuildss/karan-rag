import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { CircleMarker, MapContainer, Popup, TileLayer, useMap } from 'react-leaflet'

const markerColors = {
  official: '#177e68',
  reconstructed_from_official_sources: '#d99124',
  curated_demo: '#2774b8',
  synthetic_demo: '#8b5bb5',
}

function validCoordinates(project) {
  if (!project.location) return null
  const coordinates = [Number(project.location.latitude), Number(project.location.longitude)]
  return coordinates.every(Number.isFinite) ? coordinates : null
}

function FitProjectBounds({ locatedProjects }) {
  const map = useMap()
  useEffect(() => {
    if (locatedProjects.length > 1) {
      map.fitBounds(locatedProjects.map(({ coordinates }) => coordinates), {
        padding: [42, 42],
        maxZoom: 14,
      })
    }
  }, [locatedProjects, map])
  return null
}

function markerRadius(project, projects) {
  const known = projects
    .map(({ project: item }) => Number(item.allocated_amount))
    .filter((value) => Number.isFinite(value) && value > 0)
  const amount = Number(project.allocated_amount)
  if (!Number.isFinite(amount) || amount <= 0 || !known.length) return 8
  const min = Math.min(...known)
  const max = Math.max(...known)
  if (min === max) return 14
  return 8 + ((Math.sqrt(amount) - Math.sqrt(min)) / (Math.sqrt(max) - Math.sqrt(min))) * 16
}

export default function ProjectsMap({ projects }) {
  const { i18n, t } = useTranslation()
  const isNepali = i18n.resolvedLanguage === 'np'
  const locatedProjects = projects
    .map((project) => ({ project, coordinates: validCoordinates(project) }))
    .filter((item) => item.coordinates)
  const formatMoney = (value) =>
    value === null || value === undefined
      ? t('project.unknown')
      : new Intl.NumberFormat(isNepali ? 'ne-NP' : 'en-NP', {
          style: 'currency',
          currency: 'NPR',
          maximumFractionDigits: 0,
        }).format(Number(value))

  if (!locatedProjects.length) {
    return (
      <section className="map-empty-state">
        <p className="eyebrow">{t('discovery.map.eyebrow')}</p>
        <h2 className="mt-3 font-display text-3xl font-bold text-forest">{t('discovery.map.emptyTitle')}</h2>
        <p className="mt-4 max-w-2xl leading-7 text-muted">{t('discovery.map.emptyDescription')}</p>
        <p className="data-notice mt-6">{t('discovery.map.safety')}</p>
      </section>
    )
  }

  return (
    <section>
      <div className="mb-6">
        <p className="eyebrow">{t('discovery.map.eyebrow')}</p>
        <h2 className="mt-3 font-display text-3xl font-bold text-forest">{t('discovery.map.title')}</h2>
        <p className="mt-3 text-muted">{t('discovery.map.count', { count: locatedProjects.length })}</p>
      </div>
      <div aria-label={t('discovery.map.label')} className="project-map">
        <MapContainer center={locatedProjects[0].coordinates} scrollWheelZoom={false} zoom={12}>
          <FitProjectBounds locatedProjects={locatedProjects} />
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {locatedProjects.map(({ coordinates, project }) => (
            <CircleMarker
              center={coordinates}
              key={project.id}
              pathOptions={{
                color: '#ffffff',
                fillColor: markerColors[project.data_classification] || '#566a66',
                fillOpacity: 0.82,
                weight: 2,
              }}
              radius={markerRadius(project, locatedProjects)}
            >
              <Popup>
                <strong>{project[isNepali ? 'title_np' : 'title_en']}</strong>
                <br />
                {formatMoney(project.allocated_amount)}
                <br />
                {t(`project.classification.${
                  project.data_classification === 'reconstructed_from_official_sources'
                    ? 'reconstructed'
                    : project.data_classification === 'synthetic_demo'
                      ? 'syntheticDemo'
                      : project.data_classification === 'curated_demo'
                        ? 'curatedDemo'
                        : 'official'
                }`)}
                <br />
                <a href={`/projects/${project.id}`}>{t('discovery.card.open')}</a>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>
      <div className="map-legend" aria-label={t('discovery.map.legend')}>
        <span><i style={{ background: markerColors.official }} />{t('project.classification.official')}</span>
        <span><i style={{ background: markerColors.reconstructed_from_official_sources }} />{t('project.classification.reconstructed')}</span>
        <span><i style={{ background: markerColors.synthetic_demo }} />{t('project.classification.syntheticDemo')}</span>
        <small>{t('discovery.map.sizeNote')}</small>
      </div>
    </section>
  )
}
