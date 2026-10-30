export function Loading({ label = 'Consultando resultados…' }) {
  return <div className="state loading-state" role="status"><span className="spinner" aria-hidden="true"/><span>{label}</span></div>;
}
export function ErrorState({ error, retry }) {
  return <div className="state error-state" role="alert"><span className="state-symbol" aria-hidden="true">!</span><div><strong>No pudimos completar la consulta</strong><p>{error?.message || 'Intenta nuevamente.'}</p></div><button className="button secondary" onClick={retry}>Reintentar</button></div>;
}
export function EmptyState({ clear, message = 'No hay registros para esta selección.' }) {
  return <div className="state empty-state"><span className="empty-symbol" aria-hidden="true">∅</span><h3>Sin resultados</h3><p>{message}</p>{clear && <button className="button secondary" onClick={clear}>Restablecer filtros</button>}</div>;
}
export function QueryState({ query, children }) {
  if (query.status === 'loading') return <Loading/>;
  if (query.status === 'error') return <ErrorState error={query.error} retry={query.retry}/>;
  if (query.status !== 'success') return null;
  return children(query.response.data, query.response.meta);
}
export function SourceNote() {
  return <p className="source-note">Datos de admisión 2015–2024</p>;
}
export function PageHeading({ eyebrow, title, description, children }) {
  return <div className="page-heading"><div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p className="page-description">{description}</p></div>{children}</div>;
}
