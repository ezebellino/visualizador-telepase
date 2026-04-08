import {
  Dispatch,
  FormEvent,
  SetStateAction,
  startTransition,
  useDeferredValue,
  useEffect,
  useState,
} from "react";
import "driver.js/dist/driver.css";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { DashboardResponse } from "./types";

const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
  (import.meta.env.DEV ? "http://127.0.0.1:8000" : "");

type FiltersState = {
  vias: string[];
  sentidos: string[];
  patente: string;
  startTime: string;
  endTime: string;
};

type SectionVisibility = {
  highlights: boolean;
  trend: boolean;
  status: boolean;
  payment: boolean;
  detail: boolean;
};

type ExemptFiltersState = {
  agrupaciones: string[];
  subtipos: string[];
};

const DETAILED_EXEMPTION_TYPES = new Set([
  "Autoriza Supervisor",
  "Discapacitado",
  "Ambulancia",
  "Policia",
  "Bomberos",
  "Ex Combatientes",
  "Personal propio",
  "Exento identificado",
  "Vialidad Provincial",
]);

const INITIAL_FILTERS: FiltersState = {
  vias: [],
  sentidos: [],
  patente: "",
  startTime: "",
  endTime: "",
};

const INITIAL_SECTIONS: SectionVisibility = {
  highlights: true,
  trend: true,
  status: true,
  payment: true,
  detail: true,
};

const INITIAL_EXEMPT_FILTERS: ExemptFiltersState = {
  agrupaciones: [],
  subtipos: [],
};

const TOUR_STORAGE_KEY = "telepase-tour-seen-v1";

export default function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [filters, setFilters] = useState<FiltersState>(INITIAL_FILTERS);
  const [sections, setSections] = useState<SectionVisibility>(INITIAL_SECTIONS);
  const [exemptFilters, setExemptFilters] = useState<ExemptFiltersState>(INITIAL_EXEMPT_FILTERS);
  const [activeView, setActiveView] = useState<"overview" | "exempts" | "deep-dive" | "audit">(
    "overview",
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const deferredPatente = useDeferredValue(filters.patente.trim().toLowerCase());

  useEffect(() => {
    if (!dashboard) {
      return;
    }

    setFilters((current) => ({
      ...current,
      vias: current.vias.length ? current.vias : dashboard.filters.vias,
      sentidos: current.sentidos.length ? current.sentidos : dashboard.filters.sentidos,
    }));
    setExemptFilters({
      agrupaciones: uniqueValues(dashboard.exempt_records.map((record) => record.agrupacion)),
      subtipos: uniqueValues(dashboard.exempt_records.map((record) => record.subtipo)),
    });
  }, [dashboard]);

  useEffect(() => {
    if (!dashboard || typeof window === "undefined") {
      return;
    }

    if (window.localStorage.getItem(TOUR_STORAGE_KEY)) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      runProductTour(setActiveView);
      window.localStorage.setItem(TOUR_STORAGE_KEY, "true");
    }, 500);

    return () => window.clearTimeout(timeoutId);
  }, [dashboard]);

  const visibleRecords = dashboard?.records.filter((record) => {
    if (!deferredPatente) {
      return true;
    }

    return record.patente.toLowerCase().includes(deferredPatente);
  });

  const exemptGroupingOptions = uniqueValues(
    dashboard?.exempt_records.map((record) => record.agrupacion) ?? [],
  );
  const exemptSubtypeOptions = uniqueValues(
    dashboard?.exempt_records
      .filter(
        (record) =>
          !exemptFilters.agrupaciones.length ||
          exemptFilters.agrupaciones.includes(record.agrupacion),
      )
      .map((record) => record.subtipo) ?? [],
  );
  const filteredExemptRecords =
    dashboard?.exempt_records.filter((record) => {
      const groupingMatch =
        !exemptFilters.agrupaciones.length ||
        exemptFilters.agrupaciones.includes(record.agrupacion);
      const subtypeMatch =
        !exemptFilters.subtipos.length || exemptFilters.subtipos.includes(record.subtipo);
      return groupingMatch && subtypeMatch;
    }) ?? [];

  const filteredExemptDistribution = countByLabel(
    filteredExemptRecords.map((record) => record.agrupacion),
  );
  const filteredSupervisorDistribution = countByLabel(
    filteredExemptRecords
      .filter((record) => record.agrupacion === "Autoriza Supervisor")
      .map((record) => record.subtipo),
  );
  const filteredSupervisorTotal = filteredExemptRecords.filter(
    (record) => record.agrupacion === "Autoriza Supervisor",
  ).length;
  const filteredSupervisorClassified = filteredExemptRecords.filter(
    (record) =>
      record.agrupacion === "Autoriza Supervisor" && record.subtipo !== "Supervisor - Otro",
  ).length;
  const filteredDetailedRecords = filteredExemptRecords.filter((record) =>
    DETAILED_EXEMPTION_TYPES.has(record.tipo),
  );
  const filteredOperationalRecords = filteredExemptRecords.filter(
    (record) => !DETAILED_EXEMPTION_TYPES.has(record.tipo),
  );
  const filteredDetailedDistribution = countByLabel(
    filteredDetailedRecords.map((record) => record.tipo),
  );
  const filteredOperationalDistribution = countByLabel(
    filteredOperationalRecords.map((record) => record.tipo),
  );
  const filteredDetailedSubtypeDistribution = countByLabel(
    filteredDetailedRecords.map((record) => `${record.tipo} | ${record.subtipo}`),
  ).slice(0, 10);
  const antennaBaseMetric = dashboard?.metrics.find((metric) => metric.label === "Base real antena");
  const antennaReadsMetric = dashboard?.metrics.find(
    (metric) => metric.label === "Lecturas correctas",
  );
  const antennaManualMetric = dashboard?.metrics.find(
    (metric) => metric.label === "Ingresadas manual",
  );
  const antennaEffectivenessMetric = dashboard?.metrics.find(
    (metric) => metric.label === "Efectividad real antena",
  );
  const antennaBase = Number(antennaBaseMetric?.value ?? 0);
  const antennaReads = Number(antennaReadsMetric?.value ?? 0);
  const antennaManuals = Number(antennaManualMetric?.value ?? 0);
  const antennaReadRate = antennaBase ? (antennaReads / antennaBase) * 100 : 0;
  const antennaManualRate = antennaBase ? (antennaManuals / antennaBase) * 100 : 0;
  const visibleRecordCount = visibleRecords?.length ?? 0;
  const cashRecordsCount = dashboard?.records.filter((record) => record.forma_pago === "Efectivo").length ?? 0;
  const manualRecordCount =
    dashboard?.records.filter((record) => record.estado.includes("Manual")).length ?? 0;
  const topViaStatuses = (dashboard?.status_by_via ?? []).slice(0, 8);
  const auditSummaryRows = dashboard
    ? [
        { indicador: "Archivo procesado", valor: dashboard.file_name },
        { indicador: "Generado", valor: formatAuditDate(dashboard.generated_at) },
        { indicador: "Transitos visibles", valor: String(dashboard.total_records) },
        { indicador: "Registros auditables en tabla", valor: String(visibleRecordCount) },
        { indicador: "Base real antena", valor: String(antennaBase) },
        { indicador: "Lecturas correctas", valor: String(antennaReads) },
        { indicador: "Ingresadas manual", valor: String(antennaManuals) },
        { indicador: "Cobro efectivo", valor: String(cashRecordsCount) },
        { indicador: "Manuales detectadas", valor: String(manualRecordCount) },
        { indicador: "Efectividad real antena", valor: `${roundMetricValue(antennaReadRate)}%` },
        { indicador: "EXENTOS / Otros", valor: String(filteredExemptRecords.length) },
        { indicador: "Supervisor clasificados", valor: String(filteredSupervisorClassified) },
        { indicador: "Vias activas", valor: dashboard.filters.vias.join(", ") || "N/A" },
        { indicador: "Sentidos activos", valor: dashboard.filters.sentidos.join(", ") || "N/A" },
      ]
    : [];

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedFile) {
      setErrorMessage("Selecciona un archivo operativo antes de ejecutar el tablero.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    const formData = new FormData();
    formData.append("file", selectedFile);
    if (filters.vias.length) {
      formData.append("vias", filters.vias.join(","));
    }
    if (filters.sentidos.length) {
      formData.append("sentidos", filters.sentidos.join(","));
    }
    if (filters.patente) {
      formData.append("patente", filters.patente);
    }
    if (filters.startTime) {
      formData.append("start_time", filters.startTime);
    }
    if (filters.endTime) {
      formData.append("end_time", filters.endTime);
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/analyze`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || "No se pudo construir el dashboard.");
      }

      const payload = (await response.json()) as DashboardResponse;
      startTransition(() => {
        setDashboard(payload);
      });
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Ocurrio un error inesperado en la API.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleStartTour() {
    runProductTour(setActiveView);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(TOUR_STORAGE_KEY, "true");
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar" id="tour-sidebar">
        <div>
          <p className="eyebrow">Telepase Ops</p>
          <h1>Control Center</h1>
          <p className="sidebar-copy">
            Dashboard ejecutivo seccionado, con portada operativa y anexo analitico de EXENTOS.
          </p>
        </div>

        <form className="control-form" id="tour-upload" onSubmit={handleSubmit}>
          <label className="field">
            <span>Reporte fuente</span>
            <input
              type="file"
              accept=".csv,.xls,.xlsx"
              onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
            />
          </label>

          <label className="field">
            <span>Patente</span>
            <input
              type="text"
              placeholder="Filtrar por coincidencia"
              value={filters.patente}
              onChange={(event) =>
                setFilters((current) => ({ ...current, patente: event.target.value }))
              }
            />
          </label>

          <div className="field-grid">
            <label className="field">
              <span>Hora inicio</span>
              <input
                type="time"
                value={filters.startTime}
                onChange={(event) =>
                  setFilters((current) => ({ ...current, startTime: event.target.value }))
                }
              />
            </label>

            <label className="field">
              <span>Hora fin</span>
              <input
                type="time"
                value={filters.endTime}
                onChange={(event) =>
                  setFilters((current) => ({ ...current, endTime: event.target.value }))
                }
              />
            </label>
          </div>

          <MultiSelect
            label="Vias"
            options={dashboard?.filters.vias ?? []}
            selected={filters.vias}
            onToggle={(value) =>
              setFilters((current) => ({
                ...current,
                vias: toggleValue(current.vias, value),
              }))
            }
          />

          <MultiSelect
            label="Sentidos"
            options={dashboard?.filters.sentidos ?? []}
            selected={filters.sentidos}
            onToggle={(value) =>
              setFilters((current) => ({
                ...current,
                sentidos: toggleValue(current.sentidos, value),
              }))
            }
          />

          <SectionSelector sections={sections} setSections={setSections} />

          <button className="submit-button" disabled={isSubmitting} type="submit">
            {isSubmitting ? "Procesando lote..." : "Construir dashboard"}
          </button>
          <button className="secondary-button" onClick={handleStartTour} type="button">
            Ver guía rápida
          </button>
          <p className="tour-hint">Puedes cerrar la guía con la tecla `Esc` o con el botón `X`.</p>
        </form>

        {errorMessage ? <p className="error-message">{errorMessage}</p> : null}
      </aside>

      <main className="workspace">
        <section className="hero-panel">
          <div>
            <p className="eyebrow">Operational Workspace</p>
            <h2>{dashboard?.headline ?? "Arquitectura lista para FastAPI + React"}</h2>
          </div>
          <div className="hero-note">
            <article className="hero-note-card">
              <span>Estacion</span>
              <strong>La Huella</strong>
            </article>
            <article className="hero-note-card">
              <span>Ubicacion</span>
              <strong>Ruta 11 Km 240</strong>
            </article>
            <article className="hero-note-card">
              <span>Stack</span>
              <strong>FastAPI + React</strong>
            </article>
          </div>
        </section>

        <nav className="view-switcher" id="tour-views">
          <button
            className={`view-button ${activeView === "overview" ? "view-button-active" : ""}`}
            onClick={() => setActiveView("overview")}
            type="button"
          >
            Portada operativa
          </button>
          <button
            className={`view-button ${activeView === "exempts" ? "view-button-active" : ""}`}
            onClick={() => setActiveView("exempts")}
            type="button"
          >
            Anexo EXENTOS
          </button>
          <button
            className={`view-button ${activeView === "deep-dive" ? "view-button-active" : ""}`}
            onClick={() => setActiveView("deep-dive")}
            type="button"
          >
            Detalles minuciosos
          </button>
          <button
            className={`view-button ${activeView === "audit" ? "view-button-active" : ""}`}
            onClick={() => setActiveView("audit")}
            type="button"
          >
            Auditoria operativa
          </button>
        </nav>

        {dashboard ? (
          activeView === "overview" ? (
            <>
              <section className="metrics-strip" id="tour-metrics">
                {dashboard.metrics.map((metric) => (
                  <article className="metric-block" key={metric.label}>
                    <span>{metric.label}</span>
                    <strong>{metric.value}</strong>
                    <small>{metric.delta ?? "Sin observaciones"}</small>
                  </article>
                ))}
              </section>

              <section className="antenna-panel">
                <article className="antenna-summary">
                  <div className="panel-heading">
                    <p className="eyebrow">Antena real</p>
                    <h3>Performance sin cobro en efectivo</h3>
                  </div>
                  <p className="antenna-copy">
                    La base real de antena toma el universo total y descuenta el cobro en efectivo.
                    Sobre esa base se compara lectura correcta contra intervención manual.
                  </p>
                  <div className="antenna-metrics">
                    <div>
                      <span>Base analizada</span>
                      <strong>{antennaBase}</strong>
                      <small>{antennaBaseMetric?.delta ?? "Sin exclusiones informadas"}</small>
                    </div>
                    <div>
                      <span>Efectividad real</span>
                      <strong>{roundMetricValue(antennaEffectivenessMetric?.value)}%</strong>
                      <small>{antennaEffectivenessMetric?.delta ?? "Sin lectura de referencia"}</small>
                    </div>
                  </div>
                </article>

                <article className="antenna-breakdown">
                  <div className="antenna-bar-group">
                    <div className="antenna-bar-header">
                      <span>Lecturas correctas</span>
                      <strong>
                        {antennaReads} · {roundMetricValue(antennaReadRate)}%
                      </strong>
                    </div>
                    <div className="antenna-bar-track">
                      <div
                        className="antenna-bar-fill antenna-bar-fill-good"
                        style={{ width: `${Math.min(antennaReadRate, 100)}%` }}
                      />
                    </div>
                    <small>{antennaReadsMetric?.delta ?? "Sin detalle"}</small>
                  </div>

                  <div className="antenna-bar-group">
                    <div className="antenna-bar-header">
                      <span>Ingresadas manual</span>
                      <strong>
                        {antennaManuals} · {roundMetricValue(antennaManualRate)}%
                      </strong>
                    </div>
                    <div className="antenna-bar-track">
                      <div
                        className="antenna-bar-fill antenna-bar-fill-warn"
                        style={{ width: `${Math.min(antennaManualRate, 100)}%` }}
                      />
                    </div>
                    <small>{antennaManualMetric?.delta ?? "Sin detalle"}</small>
                  </div>
                </article>
              </section>

              {sections.highlights || sections.trend ? (
                <section className="insights-grid">
                  {sections.highlights ? (
                    <article className="list-panel">
                      <div className="panel-heading">
                        <p className="eyebrow">Highlights</p>
                        <h3>Lectura ejecutiva</h3>
                      </div>
                      <ul className="highlights-list">
                        {dashboard.highlights.map((highlight) => (
                          <li key={highlight}>{highlight}</li>
                        ))}
                      </ul>
                    </article>
                  ) : null}

                  {sections.trend ? (
                    <article className="chart-panel">
                      <div className="panel-heading">
                        <p className="eyebrow">Trend</p>
                        <h3>Efectividad de lectura</h3>
                      </div>
                      <ResponsiveContainer height={260} width="100%">
                        <LineChart data={dashboard.effectiveness_trend}>
                          <CartesianGrid stroke="rgba(113,128,150,0.2)" strokeDasharray="3 3" />
                          <XAxis dataKey="time" minTickGap={28} tickFormatter={formatShortTime} />
                          <YAxis />
                          <Tooltip
                            formatter={(value: number) => [`${value}%`, "Efectividad"]}
                            labelFormatter={formatTooltipDate}
                          />
                          <Line
                            dataKey="effectiveness"
                            dot={false}
                            stroke="#0f766e"
                            strokeWidth={3}
                            type="monotone"
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </article>
                  ) : null}
                </section>
              ) : null}

              {sections.status || sections.payment ? (
                <section className="charts-grid">
                  {sections.status ? (
                    <article className="chart-panel">
                      <div className="panel-heading">
                        <p className="eyebrow">Status mix</p>
                        <h3>Estados operativos</h3>
                      </div>
                      <ResponsiveContainer height={260} width="100%">
                        <BarChart data={dashboard.status_distribution}>
                          <CartesianGrid stroke="rgba(113,128,150,0.2)" strokeDasharray="3 3" />
                          <XAxis angle={-10} dataKey="label" height={64} interval={0} textAnchor="end" />
                          <YAxis />
                          <Tooltip />
                          <Bar dataKey="value" fill="#1d4ed8" radius={[10, 10, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </article>
                  ) : null}

                  {sections.payment ? (
                    <article className="chart-panel">
                      <div className="panel-heading">
                        <p className="eyebrow">Payment</p>
                        <h3>Distribucion de cobro</h3>
                      </div>
                      <ResponsiveContainer height={260} width="100%">
                        <BarChart data={dashboard.payment_distribution}>
                          <CartesianGrid stroke="rgba(113,128,150,0.2)" strokeDasharray="3 3" />
                          <XAxis dataKey="label" />
                          <YAxis />
                          <Tooltip />
                          <Bar dataKey="value" fill="#ea580c" radius={[10, 10, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </article>
                  ) : null}
                </section>
              ) : null}

              {sections.detail ? (
                <section className="table-panel">
                  <div className="panel-heading">
                    <p className="eyebrow">Audit table</p>
                    <h3>Detalle operativo</h3>
                  </div>
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Hora</th>
                          <th>Via</th>
                          <th>Patente</th>
                          <th>Estado</th>
                          <th>Pago</th>
                          <th>Categoria</th>
                        </tr>
                      </thead>
                      <tbody>
                        {visibleRecords?.slice(0, 14).map((record) => (
                          <tr key={`${record.transito}-${record.hora}`}>
                            <td>{record.hora}</td>
                            <td>{record.via}</td>
                            <td>{record.patente}</td>
                            <td>
                              <span className={`status-pill ${statusClassName(record.estado)}`}>
                                {record.estado}
                              </span>
                            </td>
                            <td>{record.forma_pago}</td>
                            <td>{record.categoria}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              ) : null}
            </>
          ) : activeView === "exempts" ? (
            <>
              <section className="list-panel annex-filters" id="tour-exempts">
                <div className="panel-heading">
                  <p className="eyebrow">Filtros del anexo</p>
                  <h3>Tipo de subconjuntos y agrupaciones</h3>
                </div>
                <MultiSelect
                  label="Agrupacion"
                  options={exemptGroupingOptions}
                  selected={exemptFilters.agrupaciones}
                  onToggle={(value) =>
                    setExemptFilters((current) => {
                      const nextAgrupaciones = toggleValue(current.agrupaciones, value);
                      const allowedSubtypes = uniqueValues(
                        (dashboard?.exempt_records ?? [])
                          .filter(
                            (record) =>
                              !nextAgrupaciones.length ||
                              nextAgrupaciones.includes(record.agrupacion),
                          )
                          .map((record) => record.subtipo),
                      );

                      return {
                        agrupaciones: nextAgrupaciones,
                        subtipos: current.subtipos.filter((subtipo) =>
                          allowedSubtypes.includes(subtipo),
                        ),
                      };
                    })
                  }
                />
                <MultiSelect
                  label="Tipo de subconjunto"
                  options={exemptSubtypeOptions}
                  selected={exemptFilters.subtipos}
                  onToggle={(value) =>
                    setExemptFilters((current) => ({
                      ...current,
                      subtipos: toggleValue(current.subtipos, value),
                    }))
                  }
                />
              </section>

              <section className="metrics-strip">
                <article className="metric-block">
                  <span>Total EXENTOS / Otros</span>
                  <strong>{filteredExemptRecords.length}</strong>
                  <small>
                    {filteredExemptRecords.length === dashboard.exempt_total
                      ? "Universo completo del anexo"
                      : `Filtrado sobre ${dashboard.exempt_total} registros`}
                  </small>
                </article>
                <article className="metric-block">
                  <span>Con agrupacion base</span>
                  <strong>{filteredExemptDistribution.length}</strong>
                  <small>Agrupaciones visibles en el grafico principal</small>
                </article>
                <article className="metric-block">
                  <span>Autoriza Supervisor</span>
                  <strong>{filteredSupervisorTotal}</strong>
                  <small>Subconjunto dentro del total</small>
                </article>
                <article className="metric-block">
                  <span>Supervisor clasificados</span>
                  <strong>{filteredSupervisorClassified}</strong>
                  <small>Debito o TAG habilitado</small>
                </article>
                <article className="metric-block">
                  <span>Supervisor sin clasificar</span>
                  <strong>{filteredSupervisorTotal - filteredSupervisorClassified}</strong>
                  <small>Requieren criterio adicional</small>
                </article>
              </section>

              <section className="list-panel">
                <div className="panel-heading">
                  <p className="eyebrow">Como leer el anexo</p>
                  <h3>Niveles de análisis</h3>
                </div>
                <ul className="highlights-list">
                  <li>
                    El primer grafico distribuye los <strong>{filteredExemptRecords.length}</strong>{" "}
                    registros visibles por <strong>Agrupacion</strong>.
                  </li>
                  <li>
                    De ese total, <strong>{filteredSupervisorTotal}</strong> pertenecen a{" "}
                    <strong>Autoriza Supervisor</strong>.
                  </li>
                  <li>
                    El segundo bloque no representa los restantes casos: desglosa solo ese subconjunto
                    de supervisor en <strong>Pago con Debito</strong>,{" "}
                    <strong>TAG habilitado</strong> y <strong>Supervisor - Otro</strong>.
                  </li>
                  <li>
                    Puedes combinar <strong>Agrupacion</strong> con <strong>Tipo de subconjunto</strong>{" "}
                    para aislar, por ejemplo, solo <strong>Discapacitado con DNI</strong> o solo{" "}
                    <strong>TAG habilitado por Supervisor</strong>.
                  </li>
                </ul>
              </section>

              <section className="charts-grid">
                <article className="chart-panel">
                  <div className="panel-heading">
                    <p className="eyebrow">Exentos</p>
                    <h3>Distribucion visible por agrupacion</h3>
                  </div>
                  <ResponsiveContainer height={280} width="100%">
                    <BarChart data={filteredExemptDistribution}>
                      <CartesianGrid stroke="rgba(113,128,150,0.2)" strokeDasharray="3 3" />
                      <XAxis dataKey="label" interval={0} />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="value" fill="#7c3aed" radius={[10, 10, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </article>

                <article className="list-panel">
                  <div className="panel-heading">
                    <p className="eyebrow">Supervisor</p>
                    <h3>Subtipos visibles dentro de Autoriza Supervisor</h3>
                  </div>
                  <ul className="highlights-list">
                    {filteredSupervisorDistribution.map((item) => (
                      <li key={item.label}>
                        {item.label}: {item.value}
                        {item.label === "Supervisor - Otro" ? " <- revisar observaciones restantes" : ""}
                      </li>
                    ))}
                  </ul>
                </article>
              </section>

              <section className="table-panel">
                <div className="panel-heading">
                  <p className="eyebrow">Exentos detail</p>
                  <h3>Anexo de observaciones clasificadas</h3>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Hora</th>
                        <th>Via</th>
                        <th>Agrupacion</th>
                        <th>Tipo</th>
                        <th>Subtipo</th>
                        <th>Patente</th>
                        <th>Documento</th>
                        <th>TAG Ref</th>
                        <th>Detalle</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredExemptRecords.map((record, index) => (
                        <tr key={`${record.hora}-${record.via}-${index}`}>
                          <td>{record.hora}</td>
                          <td>{record.via}</td>
                          <td>{record.agrupacion}</td>
                          <td>{record.tipo}</td>
                          <td>{record.subtipo}</td>
                          <td>{record.patente}</td>
                          <td>{record.documento}</td>
                          <td>{record.tag_ref}</td>
                          <td>{record.detalle}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </>
          ) : activeView === "deep-dive" ? (
            <DetailedExemptsView
              detailedRecords={filteredDetailedRecords}
              detailedDistribution={filteredDetailedDistribution}
              detailedSubtypeDistribution={filteredDetailedSubtypeDistribution}
              operationalDistribution={filteredOperationalDistribution}
              operationalRecords={filteredOperationalRecords}
              supervisorDistribution={filteredSupervisorDistribution}
              supervisorResolved={filteredSupervisorClassified}
              supervisorTotal={filteredSupervisorTotal}
            />
          ) : (
            <AuditWorkspace
              auditSummaryRows={auditSummaryRows}
              dashboard={dashboard}
              exemptRecords={filteredExemptRecords}
              topViaStatuses={topViaStatuses}
              visibleRecords={visibleRecords ?? []}
            />
          )
        ) : (
          <section className="empty-workspace">
            <p className="eyebrow">Next step</p>
            <h3>Sube un reporte para transformar esta base en un dashboard ejecutable.</h3>
            <p>
              Esta iteracion separa la portada operativa del anexo de EXENTOS y permite elegir que
              bloques mostrar en pantalla.
            </p>
          </section>
        )}
      </main>
    </div>
  );
}

function SectionSelector({
  sections,
  setSections,
}: {
  sections: SectionVisibility;
  setSections: Dispatch<SetStateAction<SectionVisibility>>;
}) {
  return (
    <div className="field">
      <span>Secciones visibles</span>
      <div className="toggle-list">
        {Object.entries(sections).map(([key, value]) => (
          <label className="toggle-item" key={key}>
            <input
              checked={value}
              onChange={() =>
                setSections((current) => ({ ...current, [key]: !current[key as keyof SectionVisibility] }))
              }
              type="checkbox"
            />
            <span>{sectionLabel(key)}</span>
          </label>
        ))}
      </div>
    </div>
  );
}

function MultiSelect({
  label,
  options,
  selected,
  onToggle,
}: {
  label: string;
  options: string[];
  selected: string[];
  onToggle: (value: string) => void;
}) {
  return (
    <div className="field">
      <span>{label}</span>
      <div className="pill-group">
        {options.length ? (
          options.map((option) => (
            <button
              className={`pill ${selected.includes(option) ? "pill-active" : ""}`}
              key={option}
              onClick={(event) => {
                event.preventDefault();
                onToggle(option);
              }}
              type="button"
            >
              {option}
            </button>
          ))
        ) : (
          <span className="muted-text">Carga un archivo para habilitar opciones.</span>
        )}
      </div>
    </div>
  );
}

function DetailedExemptsView({
  detailedRecords,
  detailedDistribution,
  detailedSubtypeDistribution,
  operationalDistribution,
  operationalRecords,
  supervisorDistribution,
  supervisorResolved,
  supervisorTotal,
}: {
  detailedRecords: DashboardResponse["exempt_records"];
  detailedDistribution: Array<{ label: string; value: number }>;
  detailedSubtypeDistribution: Array<{ label: string; value: number }>;
  operationalDistribution: Array<{ label: string; value: number }>;
  operationalRecords: DashboardResponse["exempt_records"];
  supervisorDistribution: Array<{ label: string; value: number }>;
  supervisorResolved: number;
  supervisorTotal: number;
}) {
  return (
    <>
      <section className="metrics-strip">
        <article className="metric-block">
          <span>Exenciones reales</span>
          <strong>{detailedRecords.length}</strong>
          <small>Casos que merecen auditoria fina</small>
        </article>
        <article className="metric-block">
          <span>Eventos operativos</span>
          <strong>{operationalRecords.length}</strong>
          <small>Separados para no contaminar el anexo</small>
        </article>
        <article className="metric-block">
          <span>Autoriza Supervisor</span>
          <strong>{supervisorTotal}</strong>
          <small>Subset resuelto dentro de exenciones reales</small>
        </article>
        <article className="metric-block">
          <span>Supervisores resueltos</span>
          <strong>{supervisorResolved}</strong>
          <small>Casos ya clasificados por regla</small>
        </article>
        <article className="metric-block">
          <span>Combinaciones top</span>
          <strong>{detailedSubtypeDistribution.length}</strong>
          <small>Tipos y subtipos mas frecuentes</small>
        </article>
      </section>

      <section className="list-panel">
        <div className="panel-heading">
          <p className="eyebrow">Lectura fina</p>
          <h3>Detalles minuciosos</h3>
        </div>
        <ul className="highlights-list">
          <li>
            Esta vista separa <strong>exenciones reales</strong> de <strong>eventos operativos</strong>{" "}
            para que el dashboard principal no mezcle beneficio con ruido de operación.
          </li>
          <li>
            El gráfico izquierdo concentra solo agrupaciones auditables: supervisor, discapacidad,
            ambulancia, policía, personal propio y equivalentes.
          </li>
          <li>
            El gráfico derecho deja aparte <strong>Cobro efectivo</strong>,{" "}
            <strong>Violacion operativa</strong> y <strong>Anomalia operativa</strong>.
          </li>
          <li>
            La tabla inferior muestra únicamente el detalle minucioso de exenciones reales.
          </li>
        </ul>
      </section>

      <section className="charts-grid">
        <article className="chart-panel">
          <div className="panel-heading">
            <p className="eyebrow">Exenciones reales</p>
            <h3>Distribucion de detalle por tipo</h3>
          </div>
          <ResponsiveContainer height={280} width="100%">
            <BarChart data={detailedDistribution}>
              <CartesianGrid stroke="rgba(113,128,150,0.2)" strokeDasharray="3 3" />
              <XAxis dataKey="label" interval={0} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#0f766e" radius={[10, 10, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </article>

        <article className="chart-panel">
          <div className="panel-heading">
            <p className="eyebrow">Eventos aparte</p>
            <h3>Distribucion operativa separada</h3>
          </div>
          <ResponsiveContainer height={280} width="100%">
            <BarChart data={operationalDistribution}>
              <CartesianGrid stroke="rgba(113,128,150,0.2)" strokeDasharray="3 3" />
              <XAxis dataKey="label" interval={0} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#1d4ed8" radius={[10, 10, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </article>
      </section>

      <section className="insights-grid">
        <article className="list-panel">
          <div className="panel-heading">
            <p className="eyebrow">Top combinaciones</p>
            <h3>Tipo y subtipo con mas peso</h3>
          </div>
          <ul className="highlights-list">
            {detailedSubtypeDistribution.map((item) => (
              <li key={item.label}>
                {item.label}: {item.value}
              </li>
            ))}
          </ul>
        </article>

        <article className="list-panel">
          <div className="panel-heading">
            <p className="eyebrow">Supervisor</p>
            <h3>Resolucion puntual del subconjunto</h3>
          </div>
          <ul className="highlights-list">
            {supervisorDistribution.map((item) => (
              <li key={item.label}>
                {item.label}: {item.value}
              </li>
            ))}
          </ul>
        </article>
      </section>

      <section className="table-panel">
        <div className="panel-heading">
          <p className="eyebrow">Auditoria fina</p>
          <h3>Detalle minucioso de exenciones reales</h3>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Hora</th>
                <th>Via</th>
                <th>Agrupacion</th>
                <th>Tipo</th>
                <th>Subtipo</th>
                <th>Patente</th>
                <th>Documento</th>
                <th>TAG Ref</th>
                <th>Detalle</th>
              </tr>
            </thead>
            <tbody>
              {detailedRecords.map((record, index) => (
                <tr key={`${record.hora}-${record.via}-${index}`}>
                  <td>{record.hora}</td>
                  <td>{record.via}</td>
                  <td>{record.agrupacion}</td>
                  <td>{record.tipo}</td>
                  <td>{record.subtipo}</td>
                  <td>{record.patente}</td>
                  <td>{record.documento}</td>
                  <td>{record.tag_ref}</td>
                  <td>{record.detalle}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

function AuditWorkspace({
  auditSummaryRows,
  dashboard,
  exemptRecords,
  topViaStatuses,
  visibleRecords,
}: {
  auditSummaryRows: Array<{ indicador: string; valor: string }>;
  dashboard: DashboardResponse;
  exemptRecords: DashboardResponse["exempt_records"];
  topViaStatuses: DashboardResponse["status_by_via"];
  visibleRecords: DashboardResponse["records"];
}) {
  const exportedAt = new Date().toISOString();

  function exportAuditSummary() {
    downloadTextFile(
      `auditoria-operativa-${safeFileStem(dashboard.file_name)}.json`,
      JSON.stringify(
        {
          exported_at: exportedAt,
          dashboard_generated_at: dashboard.generated_at,
          source_file: dashboard.file_name,
          summary: auditSummaryRows,
          top_via_statuses: topViaStatuses,
        },
        null,
        2,
      ),
      "application/json;charset=utf-8",
    );
  }

  function exportVisibleRecords() {
    downloadTextFile(
      `auditoria-transitos-${safeFileStem(dashboard.file_name)}.csv`,
      toCsv(
        visibleRecords.map((record) => ({
          Hora: record.hora,
          Via: record.via,
          Transito: String(record.transito),
          Patente: record.patente,
          TAG: record.tag,
          Estado: record.estado,
          FormaPago: record.forma_pago,
          Categoria: record.categoria,
          Sentido: record.sentido,
          ViolacionViaAbierta: record.violacion_via_abierta ? "Si" : "No",
          DescripcionOriginal: record.descripcion_original,
        })),
      ),
      "text/csv;charset=utf-8",
    );
  }

  function exportExemptRecords() {
    downloadTextFile(
      `auditoria-exentos-${safeFileStem(dashboard.file_name)}.csv`,
      toCsv(
        exemptRecords.map((record) => ({
          Hora: record.hora,
          Via: record.via,
          Agrupacion: record.agrupacion,
          Tipo: record.tipo,
          Subtipo: record.subtipo,
          Patente: record.patente,
          Documento: record.documento,
          TagRef: record.tag_ref,
          Detalle: record.detalle,
          Observacion: record.observacion,
        })),
      ),
      "text/csv;charset=utf-8",
    );
  }

  return (
    <>
      <section className="audit-toolbar" id="tour-audit">
        <div>
          <p className="eyebrow">Auditoria</p>
          <h3>Vista operativa exportable</h3>
          <p className="audit-copy">
            Resume el lote procesado, deja trazabilidad del corte analizado y permite exportar
            transitos, EXENTOS y resumen ejecutivo para compartir o archivar.
          </p>
        </div>
        <div className="audit-actions">
          <button className="audit-button" onClick={exportAuditSummary} type="button">
            Exportar resumen JSON
          </button>
          <button className="audit-button" onClick={exportVisibleRecords} type="button">
            Exportar transitos CSV
          </button>
          <button className="audit-button" onClick={exportExemptRecords} type="button">
            Exportar EXENTOS CSV
          </button>
        </div>
      </section>

      <section className="metrics-strip">
        {auditSummaryRows.slice(0, 5).map((item) => (
          <article className="metric-block" key={item.indicador}>
            <span>{item.indicador}</span>
            <strong>{item.valor}</strong>
            <small>Control de auditoria</small>
          </article>
        ))}
      </section>

      <section className="charts-grid">
        <article className="list-panel">
          <div className="panel-heading">
            <p className="eyebrow">Bitacora</p>
            <h3>Resumen del lote auditado</h3>
          </div>
          <div className="audit-summary-grid">
            {auditSummaryRows.map((item) => (
              <div className="audit-summary-item" key={item.indicador}>
                <span>{item.indicador}</span>
                <strong>{item.valor}</strong>
              </div>
            ))}
          </div>
        </article>

        <article className="list-panel">
          <div className="panel-heading">
            <p className="eyebrow">Foco por via</p>
            <h3>Estados con mayor volumen</h3>
          </div>
          <ul className="highlights-list">
            {topViaStatuses.map((item, index) => (
              <li key={`${item.via}-${item.estado}-${index}`}>
                Via {item.via}: {item.estado} ({item.cantidad})
              </li>
            ))}
          </ul>
        </article>
      </section>

      <section className="table-panel">
        <div className="panel-heading">
          <p className="eyebrow">Traza exportable</p>
          <h3>Muestra de transitos auditados</h3>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Hora</th>
                <th>Via</th>
                <th>Transito</th>
                <th>Patente</th>
                <th>Estado</th>
                <th>Pago</th>
                <th>Categoria</th>
              </tr>
            </thead>
            <tbody>
              {visibleRecords.slice(0, 18).map((record) => (
                <tr key={`audit-${record.transito}-${record.hora}`}>
                  <td>{record.hora}</td>
                  <td>{record.via}</td>
                  <td>{record.transito}</td>
                  <td>{record.patente}</td>
                  <td>{record.estado}</td>
                  <td>{record.forma_pago}</td>
                  <td>{record.categoria}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

function toggleValue(current: string[], value: string) {
  return current.includes(value)
    ? current.filter((item) => item !== value)
    : [...current, value];
}

function statusClassName(status: string) {
  if (status.includes("Correctamente")) {
    return "status-good";
  }
  if (status.includes("Manual")) {
    return "status-warn";
  }
  return "status-neutral";
}

function formatShortTime(value: string) {
  return value
    ? new Date(value).toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit" })
    : "";
}

function formatTooltipDate(value: string) {
  return value ? new Date(value).toLocaleString("es-AR") : "";
}

function roundMetricValue(value: string | number | undefined | null) {
  const numeric = Number(value ?? 0);
  return Number.isFinite(numeric) ? numeric.toFixed(1) : "0.0";
}

function sectionLabel(key: string) {
  const labels: Record<string, string> = {
    highlights: "Highlights",
    trend: "Tendencia",
    status: "Estados",
    payment: "Cobro",
    detail: "Tabla",
  };
  return labels[key] ?? key;
}

function uniqueValues(values: string[]) {
  return [...new Set(values.filter(Boolean))].sort((left, right) => left.localeCompare(right));
}

function countByLabel(values: string[]) {
  const counts = new Map<string, number>();

  values.filter(Boolean).forEach((value) => {
    counts.set(value, (counts.get(value) ?? 0) + 1);
  });

  return [...counts.entries()]
    .map(([label, value]) => ({ label, value }))
    .sort((left, right) => right.value - left.value || left.label.localeCompare(right.label));
}

async function runProductTour(
  setActiveView: Dispatch<SetStateAction<"overview" | "exempts" | "deep-dive" | "audit">>,
) {
  const { driver } = await import("driver.js");
  const tour = driver({
    showProgress: true,
    allowClose: true,
    overlayClickBehavior: "close",
    nextBtnText: "Siguiente",
    prevBtnText: "Anterior",
    doneBtnText: "Listo",
    steps: [
      {
        element: "#tour-sidebar",
        popover: {
          title: "Centro de control",
          description:
            "Aqui cargas el archivo operativo, ajustas filtros y ejecutas la construccion del dashboard.",
          side: "right",
          align: "start",
        },
      },
      {
        element: "#tour-upload",
        popover: {
          title: "Entrada del lote",
          description:
            "Sube archivos CSV, XLS o XLSX. Luego puedes filtrar por via, sentido, patente y franja horaria.",
          side: "right",
          align: "start",
        },
      },
      {
        element: "#tour-views",
        popover: {
          title: "Navegacion por vistas",
          description:
            "La app separa portada operativa, anexo EXENTOS, detalles minuciosos y auditoria operativa.",
          side: "bottom",
          align: "start",
          onNextClick: () => {
            setActiveView("overview");
            window.setTimeout(() => tour.moveNext(), 120);
          },
        },
      },
      {
        element: "#tour-metrics",
        popover: {
          title: "KPIs ejecutivos",
          description:
            "Estas tarjetas concentran transitos visibles, base real de antena, lecturas correctas y manuales.",
          side: "bottom",
          align: "start",
          onNextClick: () => {
            setActiveView("exempts");
            window.setTimeout(() => tour.moveNext(), 160);
          },
        },
      },
      {
        element: "#tour-exempts",
        popover: {
          title: "Analitica de EXENTOS",
          description:
            "Aqui puedes segmentar agrupaciones y subtipos para leer el anexo con mayor precision.",
          side: "top",
          align: "start",
          onNextClick: () => {
            setActiveView("audit");
            window.setTimeout(() => tour.moveNext(), 160);
          },
        },
      },
      {
        element: "#tour-audit",
        popover: {
          title: "Auditoria exportable",
          description:
            "Esta vista resume el lote y permite exportar JSON o CSV para compartir, archivar o revisar operativamente.",
          side: "bottom",
          align: "start",
        },
      },
    ],
    onDestroyed: () => {
      if (typeof window !== "undefined") {
        window.localStorage.setItem(TOUR_STORAGE_KEY, "true");
      }
    },
  });

  setActiveView("overview");
  window.setTimeout(() => {
    tour.drive();
  }, 150);
}

function formatAuditDate(value: string) {
  return value ? new Date(value).toLocaleString("es-AR") : "N/A";
}

function safeFileStem(fileName: string) {
  return fileName.replace(/\.[^/.]+$/, "").replace(/[^a-z0-9_-]+/gi, "-").toLowerCase();
}

function toCsv(rows: Array<Record<string, string>>) {
  if (!rows.length) {
    return "";
  }

  const headers = Object.keys(rows[0]);
  const csvRows = [
    headers.join(","),
    ...rows.map((row) =>
      headers
        .map((header) => `"${String(row[header] ?? "").replaceAll('"', '""')}"`)
        .join(","),
    ),
  ];

  return csvRows.join("\n");
}

function downloadTextFile(fileName: string, content: string, contentType: string) {
  const blob = new Blob([content], { type: contentType });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  anchor.click();
  URL.revokeObjectURL(url);
}
