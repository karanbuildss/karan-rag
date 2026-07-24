import { useTranslation } from 'react-i18next'
import { CircleMarker, MapContainer, Popup, TileLayer } from 'react-leaflet'

function validCoordinates(project) {
  if (!project.location) return null
  const coordinates = [Number(project.location.latitude), Number(project.location.longitude)]
  return coordinates.every(Number.isFinite) ? coordinates : null
}
export default function ProjectsMap({ projects }) {
  const { i18n, t } = useTranslation()
  const isNepali = i18n.resolvedLanguage === 'np'
  const locatedProjects = projects
    .map((project) => ({ project, coordinates: validCoordinates(project) }))
    .filter((item) => item.coordinates)

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
        <MapContainer center={locatedProjects[0].coordinates} scrollWheelZoom={false} zoom={13}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {locatedProjects.map(({ coordinates, project }) => (
            <CircleMarker
              center={coordinates}
              key={project.id}
              pathOptions={{ color: '#103c37', fillColor: '#c77b22', fillOpacity: 0.9 }}
              radius={9}
            >
              <Popup>
                <strong>{project[isNepali ? 'title_np' : 'title_en']}</strong>
                <br />
                <a href={`/projects/${project.id}`}>{t('discovery.card.open')}</a>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>
    </section>
  )
}
