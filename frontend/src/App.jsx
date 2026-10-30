import { useEffect, useState } from 'react';
import { getHealth } from './services/api';

export default function App() {
  const [attempt, setAttempt] = useState(0);
  const [connection, setConnection] = useState({ state: 'loading' });

  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    setConnection({ state: 'loading' });
    const timeout = setTimeout(() => controller.abort(), 8000);

    getHealth(controller.signal)
      .then((data) => {
        if (active) setConnection({ state: 'connected', service: data.service });
      })
      .catch(() => {
        if (active) setConnection({ state: 'error' });
      })
      .finally(() => clearTimeout(timeout));

    return () => {
      active = false;
      clearTimeout(timeout);
      controller.abort();
    };
  }, [attempt]);

  const labels = {
    loading: 'Comprobando conexión…',
    connected: 'API disponible',
    error: 'No se pudo conectar con la API',
  };

  return (
    <>
      <header className="topbar">
        <a className="brand" href="/" aria-label="Admisiones USAC, inicio">
          <span className="brand-mark">U</span>
          <span>ADMISIONES <strong>USAC</strong></span>
        </a>
        <span className="course">Bases de Datos NoSQL · 2026</span>
      </header>
      <main>
        <p className="eyebrow">UNIVERSIDAD DE SAN CARLOS DE GUATEMALA</p>
        <h1>Comprender los datos.<br /><span>Explorar las oportunidades.</span></h1>
        <p className="intro">Sistema de análisis de pruebas específicas de admisión.
          Un espacio para consultar resultados y explorar las relaciones entre aspirantes,
          materias y carreras.</p>

        <section className="connection-card" aria-labelledby="connection-title">
          <div>
            <p className="eyebrow">ESTADO DEL SISTEMA</p>
            <h2 id="connection-title">Conexión con el servicio</h2>
            <div className={`status ${connection.state}`} role="status" aria-live="polite">
              <span className="dot" aria-hidden="true" />{labels[connection.state]}
            </div>
            <p className="detail">
              {connection.state === 'connected' && `Servicio: ${connection.service}`}
              {connection.state === 'loading' && 'Esperando respuesta de FastAPI.'}
              {connection.state === 'error' && 'Verifica que FastAPI esté ejecutándose en el puerto 8000 y vuelve a intentar.'}
            </p>
          </div>
          <button disabled={connection.state === 'loading'} onClick={() => setAttempt((value) => value + 1)}>
            {connection.state === 'loading' ? 'Comprobando…' : 'Comprobar conexión'}
          </button>
        </section>

        <section className="next-section" aria-labelledby="next-title">
          <div className="section-heading"><h2 id="next-title">El proyecto, paso a paso</h2><span>Etapa 1 de 8</span></div>
          <div className="cards">
            <article><span className="number">01</span><h3>Carga de datos</h3><p>Importación y validación de archivos CSV oficiales.</p><span className="pending">Pendiente de implementación</span></article>
            <article><span className="number">02</span><h3>Análisis estadístico</h3><p>Consultas de MongoDB para comprender los resultados.</p><span className="pending">Pendiente de implementación</span></article>
            <article><span className="number">03</span><h3>Exploración de relaciones</h3><p>Recorridos y visualización de grafos con Neo4j.</p><span className="pending">Pendiente de implementación</span></article>
          </div>
        </section>
        <p className="scope">Esta comprobación verifica únicamente la API. Las conexiones con MongoDB y Neo4j se incorporarán en la siguiente etapa.</p>
      </main>
      <footer>Proyecto individual · Ingeniería en Ciencias y Sistemas · USAC</footer>
    </>
  );
}
