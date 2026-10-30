import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router';
import { CatalogProvider } from './components/common/Catalogs';
import AppShell from './components/layout/AppShell';
import { Loading } from './components/common/States';
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const StatisticsPage = lazy(() => import('./pages/StatisticsPage'));
const EvaluationsPage = lazy(() => import('./pages/EvaluationsPage'));
const GraphPage = lazy(() => import('./pages/GraphPage'));
const QueriesPage = lazy(() => import('./pages/QueriesPage'));

export default function App() {
  return <BrowserRouter><CatalogProvider><Suspense fallback={<Loading label="Abriendo pantalla…"/>}><Routes><Route element={<AppShell/>}>
    <Route index element={<DashboardPage/>}/><Route path="estadisticas" element={<StatisticsPage/>}/>
    <Route path="evaluaciones" element={<EvaluationsPage/>}/><Route path="grafo" element={<GraphPage/>}/><Route path="consultas" element={<QueriesPage/>}/>
    <Route path="*" element={<section className="panel empty-state"><h1>Página no encontrada</h1><Link to="/">Volver al resumen</Link></section>}/>
  </Route></Routes></Suspense></CatalogProvider></BrowserRouter>;
}
