import { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';
export const NODE_TYPES = {
  Evaluacion: ['Evaluación', '#08275C'], AspiranteCohorte: ['Aspirante de cohorte', '#25A744'],
  Materia: ['Materia', '#5e82ab'], CarreraObservada: ['Carrera observada', '#355c89'],
  Cohorte: ['Año de ingreso', '#123B69'], LocalidadEducativa: ['Localidad educativa', '#7894b3'],
  Departamento: ['Departamento', '#9eb2ca'], TipoInstitucion: ['Tipo de institución', '#687b93'],
};
export default function GraphCanvas({ data, onSelect }) {
  const container = useRef(null); const instance = useRef(null);
  const onSelectRef = useRef(onSelect); onSelectRef.current = onSelect;
  useEffect(() => {
    const elements = [...data.nodes.map((n) => ({ data: { id: n.id, tipo: n.tipo, label: n.properties.nombre || n.properties.nombre_observado || (n.tipo === 'Evaluacion' ? `${n.properties.aprobado ? 'Aprobada' : 'No aprobada'} · ${n.properties.convocatoria}` : n.tipo === 'AspiranteCohorte' ? `Cohorte ${n.properties.anio_ingreso}` : n.properties.anio || NODE_TYPES[n.tipo]?.[0]), color: NODE_TYPES[n.tipo]?.[1] || '#687b93' } })), ...data.edges.map((e) => ({ data: { id: e.id, source: e.source, target: e.target, label: e.tipo } }))];
    const cy = cytoscape({ container: container.current, elements, minZoom: 0.15, maxZoom: 3,
      style: [
        { selector: 'node', style: { 'background-color': 'data(color)', width: 24, height: 24, label: 'data(label)', 'font-size': 10, 'text-opacity': 0, 'min-zoomed-font-size': 9, 'text-valign': 'bottom', 'text-margin-y': 7, 'text-max-width': 90, 'text-wrap': 'ellipsis', color: '#46566a', 'border-width': 3, 'border-color': '#fff' } },
        // Keep the dense evaluation/cohort labels for hover or selection.
        { selector: 'node[tipo != "Evaluacion"][tipo != "AspiranteCohorte"]', style: { 'text-opacity': 1 } },
        { selector: 'node:selected, node.label-hover', style: { 'text-opacity': 1, 'min-zoomed-font-size': 0, 'text-background-color': '#FFFFFF', 'text-background-opacity': 0.95, 'text-background-padding': 3, 'z-index': 10 } },
        { selector: 'edge', style: { width: 1, 'line-color': '#c8d3de', 'target-arrow-color': '#a5b6c5', 'target-arrow-shape': 'triangle', 'arrow-scale': 0.6, 'curve-style': 'bezier' } },
        { selector: ':selected', style: { 'border-color': '#08275C', 'border-width': 4, 'line-color': '#08275C', 'target-arrow-color': '#08275C' } },
      ], layout: { name: 'cose', animate: false, randomize: false, nodeRepulsion: () => 12000, idealEdgeLength: () => 90, numIter: 400, padding: 40 } });
    instance.current = cy;
    cy.on('tap', 'node', (event) => onSelectRef.current(data.nodes.find((n) => n.id === event.target.id())));
    cy.on('mouseover', 'node', (event) => event.target.addClass('label-hover'));
    cy.on('mouseout', 'node', (event) => event.target.removeClass('label-hover'));
    const observer = new ResizeObserver(() => { cy.resize(); }); observer.observe(container.current);
    return () => { observer.disconnect(); cy.destroy(); instance.current = null; };
  }, [data]);
  const zoom = (factor) => { const cy = instance.current; if (cy) cy.zoom({ level: Math.min(3, Math.max(0.15, cy.zoom() * factor)), renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } }); };
  return <div className="graph-viewport"><div className="graph-canvas" ref={container} role="img" aria-label="Grafo interactivo. Usa la lista de nodos para consultar sus propiedades con teclado."/><div className="graph-controls"><button aria-label="Acercar grafo" onClick={() => zoom(1.3)}>+</button><button aria-label="Alejar grafo" onClick={() => zoom(0.77)}>−</button><button aria-label="Ajustar grafo al área visible" onClick={() => instance.current?.fit(undefined, 35)}>⌖</button></div><span className="graph-hint">Arrastra para explorar · selecciona un nodo</span></div>;
}
