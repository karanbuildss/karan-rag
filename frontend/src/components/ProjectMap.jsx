import { CircleMarker, MapContainer, Popup, TileLayer } from 'react-leaflet'
import { useTranslation } from 'react-i18next'

export default function ProjectMap({ location, projectTitle }) {
  const { i18n, t } = useTranslation()
  if (!location) {
    return <p className="empty-evidence">{t('project.mapUnavailable')}</p>
  }

  const coordinates = [Number(location.latitude), Number(location.longitude)]
  const isNepali = i18n.resolvedLanguage === 'np'
  const label = location[isNepali ? 'label_np' : 'label_en'] || projectTitle

  return (
    <div aria-label={t('project.mapLabel', { title: projectTitle })} className="project-map">
      <MapContainer center={coordinates} scrollWheelZoom={false} zoom={15}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <CircleMarker
          center={coordinates}
          pathOptions={{ color: '#103c37', fillColor: '#c77b22', fillOpacity: 0.9 }}
          radius={10}
        >
          <Popup>
            <strong>{projectTitle}</strong>
            <br />
            {label}
          </Popup>
        </CircleMarker>
      </MapContainer>
    </div>
  )
}
