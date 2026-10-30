import { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';
export const NODE_TYPES = {
  Evaluacion: ['Evaluación', '#426fb2'], AspiranteCohorte: ['Aspirante de cohorte', '#287b83'],
  Materia: ['Materia', '#c09541'], CarreraObservada: ['Carrera observada', '#8b6fa6'],
  Cohorte: ['Año de ingreso', '#517c9c'], LocalidadEducativa: ['Localidad educativa', '#9d7965'],
  Departamento: ['Departamento', '#6f8b63'], TipoInstitucion: ['Tipo de institución', '#778593'],
};
export default function GraphCanvas({ data, onSelect }) {
  const container = useRef(null); const instance = useRef(null);
  const onSelectRef = useRef(onSelect); onSelectRef.current = onSelect;
  useEffect(() => {
    const elements = [...data.nodes.map((n) => ({ data: { id: n.id, label: n.properties.nombre || n.properties.nombre_observado || (n.tipo === 'Evaluacion' ? `${n.properties.aprobado ? 'Aprobada' : 'No aprobada'} · ${n.properties.convocatoria}` : n.tipo === 'AspiranteCohorte' ? `Cohorte ${n.properties.anio_ingreso}` : n.properties.anio || NODE_TYPES[n.tipo]?.[0]), color: NODE_TYPES[n.tipo]?.[1] || '#778593' } })), ...data.edges.map((e) => ({ data: { id: e.id, source: e.source, target: e.target, label: e.tipo } }))];
    const cy = cytoscape({ container: container.current, elements, minZoom: 0.15, maxZoom: 3,
      style: [
        { selector: 'node', style: { 'background-color': 'data(color)', width: 24, height: 24, label: 'data(label)', 'font-size': 9, 'text-valign': 'bottom', 'text-margin-y': 7, 'text-max-width': 110, 'text-wrap': 'ellipsis', color: '#46566a', 'border-width': 3, 'border-color': '#fff' } },
        { selector: 'edge', style: { width: 1, 'line-color': '#c8d3de', 'target-arrow-color': '#a5b6c5', 'target-arrow-shape': 'triangle', 'arrow-scale': 0.6, 'curve-style': 'bezier' } },
        { selector: ':selected', style: { 'border-color': '#102b46', 'border-width': 4, 'line-color': '#102b46', 'target-arrow-color': '#102b46' } },
      ], layout: { name: 'cose', animate: false, randomize: false, nodeRepulsion: () => 12000, idealEdgeLength: () => 90, numIter: 400, padding: 40 } });
    instance.current = cy;
    cy.on('tap', 'node', (event) => onSelectRef.current(data.nodes.find((n) => n.id === event.target.id())));
    const observer = new ResizeObserver(() => { cy.resize(); }); observer.observe(container.current);
    return () => { observer.disconnect(); cy.destroy(); instance.current = null; };
  }, [data]);
  const zoom = (factor) => { const cy = instance.current; if (cy) cy.zoom({ level: Math.min(3, Math.max(0.15, cy.zoom() * factor)), renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } }); };
  return <div className="graph-viewport"><div className="graph-canvas" ref={container} role="img" aria-label="Grafo interactivo. Usa la lista de nodos para consultar sus propiedades con teclado."/><div className="graph-controls"><button aria-label="Acercar grafo" onClick={() => zoom(1.3)}>+</button><button aria-label="Alejar grafo" onClick={() => zoom(0.77)}>−</button><button aria-label="Ajustar grafo al área visible" onClick={() => instance.current?.fit(undefined, 35)}>⌖</button></div><span className="graph-hint">Arrastra para explorar · selecciona un nodo</span></div>;
}
