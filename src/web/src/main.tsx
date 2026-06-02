import React from "react";
import { createRoot } from "react-dom/client";
import { Activity, AlertTriangle, ClipboardList, Gauge, Layers3, RefreshCw, ShieldCheck } from "lucide-react";
import "./styles.css";

type RiskLabel = "low" | "medium" | "high" | "unknown";

type AssetHierarchyItem = {
  tenant_id: string;
  plant_id: string;
  plant_code: string;
  line_id: string;
  line_code: string;
  cell_id: string;
  cell_code: string;
  equipment_id: string;
  equipment_code: string;
  equipment_class: string;
  last_known_state: string;
  last_state_updated_at: string;
};

type SensorObservationItem = {
  observation_id: string;
  equipment_id: string;
  observed_at: string;
  temperature_c: number;
  vibration_mm_s: number;
  pressure_bar: number;
  rpm: number;
  operating_hours: number;
  load_pct: number;
  sensor_quality: string;
  created_at: string;
};

type MaintenanceLogItem = {
  maintenance_log_id: string;
  equipment_id: string;
  reported_at: string;
  operator_state: string;
  failure_code: string | null;
  free_text_observation: string;
  created_at: string;
};

type FailureCatalogItem = {
  failure_code: string;
  failure_category: string;
  failure_mode: string;
  iso14224_reference: string;
  is_active: boolean;
};

type PredictionResponse = {
  equipment_id: string;
  observed_at: string;
  risk_label: string;
  risk_score: number;
  model_version: string;
  feature_count: number;
};

type ApiCredentials = {
  username: string;
  password: string;
};

type EquipmentRisk = {
  asset: AssetHierarchyItem;
  observation?: SensorObservationItem;
  prediction?: PredictionResponse;
  status: "ok" | "no-sensor" | "prediction-unavailable";
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8080";

class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function apiFetch<T>(path: string, credentials: ApiCredentials, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Accept", "application/json");
  if (init?.body) headers.set("Content-Type", "application/json");
  if (credentials.username && credentials.password) {
    headers.set("Authorization", `Basic ${window.btoa(`${credentials.username}:${credentials.password}`)}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  if (!response.ok) {
    let message = "La API no pudo completar la solicitud.";
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail && response.status !== 500) message = payload.detail;
    } catch {
      message = response.statusText || message;
    }
    throw new ApiError(response.status, message);
  }
  return response.json() as Promise<T>;
}

const api = {
  hierarchy: (credentials: ApiCredentials) =>
    apiFetch<{ items: AssetHierarchyItem[] }>("/api/v1/assets/hierarchy", credentials),
  observations: (credentials: ApiCredentials, equipmentId?: string) => {
    const params = new URLSearchParams({ limit: "200" });
    if (equipmentId) params.set("equipment_id", equipmentId);
    return apiFetch<{ items: SensorObservationItem[] }>(`/api/v1/sensor-observations?${params}`, credentials);
  },
  maintenanceLogs: (credentials: ApiCredentials, equipmentId?: string) => {
    const params = new URLSearchParams({ limit: "200" });
    if (equipmentId) params.set("equipment_id", equipmentId);
    return apiFetch<{ items: MaintenanceLogItem[] }>(`/api/v1/maintenance-logs?${params}`, credentials);
  },
  failureCatalog: (credentials: ApiCredentials) =>
    apiFetch<{ items: FailureCatalogItem[] }>("/api/v1/failure-catalog", credentials),
  prediction: (credentials: ApiCredentials, asset: AssetHierarchyItem, observation: SensorObservationItem) =>
    apiFetch<PredictionResponse>("/api/v1/predictions/risk", credentials, {
      method: "POST",
      body: JSON.stringify({
        equipment_id: asset.equipment_id,
        observed_at: observation.observed_at,
        features: {
          equipment_class: asset.equipment_class,
          temperature_c: observation.temperature_c,
          vibration_mm_s: observation.vibration_mm_s,
          pressure_bar: observation.pressure_bar,
          rpm: observation.rpm,
          operating_hours: observation.operating_hours,
          load_pct: observation.load_pct,
          sensor_quality: observation.sensor_quality,
        },
      }),
    }),
  createMaintenanceLog: (credentials: ApiCredentials, payload: Omit<MaintenanceLogItem, "maintenance_log_id" | "created_at">) =>
    apiFetch<MaintenanceLogItem>("/api/v1/maintenance-logs", credentials, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};

function riskLabel(value?: string): RiskLabel {
  if (value === "low" || value === "medium" || value === "high") return value;
  return "unknown";
}

function riskClass(value?: string) {
  const label = riskLabel(value);
  return {
    low: "bg-emerald-100 text-emerald-900 border-emerald-300",
    medium: "bg-amber-100 text-amber-950 border-amber-300",
    high: "bg-red-100 text-red-950 border-red-300",
    unknown: "bg-zinc-100 text-zinc-700 border-zinc-300",
  }[label];
}

function equipmentStatusLabel(status: EquipmentRisk["status"]) {
  return {
    ok: "Prediccion disponible",
    "no-sensor": "Sin sensor",
    "prediction-unavailable": "Modelo no disponible",
  }[status];
}

function equipmentStatusDetail(status: EquipmentRisk["status"]) {
  return {
    ok: "Lectura reciente evaluada por el modelo.",
    "no-sensor": "No hay observacion de sensor para este equipo; no se ejecuta inferencia.",
    "prediction-unavailable": "Hay sensor reciente, pero la API de prediccion no respondio para este equipo.",
  }[status];
}

function equipmentTileClass(risk: EquipmentRisk) {
  if (risk.status === "no-sensor") return "bg-zinc-50 text-zinc-700 border-zinc-300";
  if (risk.status === "prediction-unavailable") return "bg-sky-50 text-sky-950 border-sky-300";
  return riskClass(risk.prediction?.risk_label);
}

function formatDate(value?: string) {
  if (!value) return "Sin fecha";
  return new Intl.DateTimeFormat("es-MX", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

function latestByEquipment(observations: SensorObservationItem[]) {
  const result = new Map<string, SensorObservationItem>();
  for (const item of observations) {
    const current = result.get(item.equipment_id);
    if (!current || new Date(item.observed_at) > new Date(current.observed_at)) {
      result.set(item.equipment_id, item);
    }
  }
  return result;
}

function groupBy<T>(items: T[], getKey: (item: T) => string) {
  const grouped = new Map<string, T[]>();
  for (const item of items) {
    const key = getKey(item);
    grouped.set(key, [...(grouped.get(key) ?? []), item]);
  }
  return grouped;
}

function EmptyState({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="rounded border border-dashed border-steel bg-white p-5 text-sm text-zinc-600">
      <strong className="block text-ink">{title}</strong>
      <span>{detail}</span>
    </div>
  );
}

function ApiNotice({ error, partial }: { error?: string; partial?: string }) {
  if (!error && !partial) return null;
  return (
    <div className="flex items-start gap-3 rounded border border-amber-300 bg-amber-50 p-4 text-sm text-amber-950">
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
      <div>
        <strong className="block">{error ? "Atencion de API" : "Datos parciales"}</strong>
        <span>{error ?? partial}</span>
      </div>
    </div>
  );
}

function AuthPanel({
  credentials,
  onChange,
  onRefresh,
  loading,
}: {
  credentials: ApiCredentials;
  onChange: (next: ApiCredentials) => void;
  onRefresh: () => void;
  loading: boolean;
}) {
  return (
    <section className="grid gap-3 border-b border-steel bg-white px-4 py-3 md:grid-cols-[1fr_220px_220px_auto] md:items-end">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-signal">MERO on-premise</p>
        <h1 className="text-xl font-semibold text-ink">Riesgo operacional</h1>
      </div>
      <label className="text-xs font-medium text-zinc-700">
        Usuario Basic
        <input
          className="mt-1 w-full rounded border border-steel px-3 py-2 text-sm"
          value={credentials.username}
          autoComplete="username"
          onChange={(event) => onChange({ ...credentials, username: event.target.value })}
        />
      </label>
      <label className="text-xs font-medium text-zinc-700">
        Password Basic
        <input
          className="mt-1 w-full rounded border border-steel px-3 py-2 text-sm"
          value={credentials.password}
          type="password"
          autoComplete="current-password"
          onChange={(event) => onChange({ ...credentials, password: event.target.value })}
        />
      </label>
      <button
        className="inline-flex h-10 items-center justify-center gap-2 rounded bg-ink px-4 text-sm font-semibold text-white disabled:opacity-60"
        onClick={onRefresh}
        disabled={loading}
        title="Actualizar datos"
      >
        <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        Actualizar
      </button>
    </section>
  );
}

function MetricsStrip({ risks, logs }: { risks: EquipmentRisk[]; logs: MaintenanceLogItem[] }) {
  const high = risks.filter((item) => riskLabel(item.prediction?.risk_label) === "high").length;
  const medium = risks.filter((item) => riskLabel(item.prediction?.risk_label) === "medium").length;
  const noSensor = risks.filter((item) => item.status === "no-sensor").length;
  const unavailable = risks.filter((item) => item.status === "prediction-unavailable").length;
  const review = logs.filter((item) => item.operator_state !== "operational").length;
  const cards = [
    { label: "Equipos en contrato", value: risks.length, icon: Layers3 },
    { label: "Riesgo predictivo alto", value: high, icon: Gauge },
    { label: "Riesgo predictivo medio", value: medium, icon: Activity },
    { label: "Registros humanos a revisar", value: review, icon: ClipboardList },
    { label: "Sin sensor", value: noSensor, icon: ShieldCheck },
    { label: "Modelo no disponible", value: unavailable, icon: AlertTriangle },
  ];
  return (
    <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
      {cards.map((card) => (
        <div key={card.label} className="rounded border border-steel bg-white p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-zinc-600">{card.label}</span>
            <card.icon className="h-4 w-4 text-signal" />
          </div>
          <div className="mt-2 text-3xl font-semibold text-ink">{card.value}</div>
        </div>
      ))}
    </div>
  );
}

function RiskHeatMap({ risks, selectedId, onSelect }: { risks: EquipmentRisk[]; selectedId?: string; onSelect: (id: string) => void }) {
  if (risks.length === 0) {
    return <EmptyState title="Sin jerarquia de activos" detail="La API no devolvio equipos para construir el mapa de calor." />;
  }
  const byPlant = groupBy(risks, (risk) => risk.asset.plant_code);
  const legend = [
    { label: "low", className: riskClass("low") },
    { label: "medium", className: riskClass("medium") },
    { label: "high", className: riskClass("high") },
    { label: "Sin sensor", className: equipmentTileClass({ asset: risks[0].asset, status: "no-sensor" }) },
    { label: "Modelo no disponible", className: equipmentTileClass({ asset: risks[0].asset, status: "prediction-unavailable" }) },
  ];
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2 text-xs" aria-label="Leyenda de riesgo">
        {legend.map((item) => (
          <span key={item.label} className={`rounded border px-2 py-1 font-semibold ${item.className}`}>
            {item.label}
          </span>
        ))}
      </div>
      {[...byPlant.entries()].map(([plant, plantRisks]) => {
        const byLine = groupBy(plantRisks, (risk) => risk.asset.line_code);
        return (
          <section key={plant} className="border-t border-steel pt-4 first:border-t-0 first:pt-0">
            <h2 className="text-sm font-semibold text-ink">Planta {plant}</h2>
            <div className="mt-3 grid gap-3 xl:grid-cols-2">
              {[...byLine.entries()].map(([line, lineRisks]) => (
                <div key={line} className="rounded border border-steel bg-white p-3">
                  <div className="mb-3 flex items-center justify-between text-xs">
                    <span className="font-semibold text-zinc-700">Linea {line}</span>
                    <span className="text-zinc-500">{lineRisks.length} equipos</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                    {lineRisks.map((risk) => (
                      <button
                        key={risk.asset.equipment_id}
                        onClick={() => onSelect(risk.asset.equipment_id)}
                        className={`min-h-32 rounded border p-3 text-left transition hover:shadow-sm ${equipmentTileClass(risk)} ${
                          selectedId === risk.asset.equipment_id ? "ring-2 ring-ink" : ""
                        }`}
                      >
                        <span className="block text-xs font-medium">{risk.asset.cell_code}</span>
                        <span className="mt-1 block text-base font-semibold">{risk.asset.equipment_code}</span>
                        <span className="mt-2 block text-xs font-semibold">
                          {risk.prediction ? `${Math.round(risk.prediction.risk_score * 100)}% ${risk.prediction.risk_label}` : equipmentStatusLabel(risk.status)}
                        </span>
                        <span className="mt-2 block text-xs opacity-80">{risk.asset.equipment_class}</span>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}

function AlgorithmicPanel({ selected }: { selected?: EquipmentRisk }) {
  if (!selected) return <EmptyState title="Seleccione un equipo" detail="El panel predictivo mostrara sensores y modelo sin mezclarlos con la bitacora." />;
  return (
    <section className="rounded border border-steel bg-white p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase text-signal">Prediccion algoritmica</p>
          <h2 className="text-lg font-semibold text-ink">{selected.asset.equipment_code}</h2>
        </div>
        <span className={`rounded border px-3 py-1 text-xs font-semibold ${riskClass(selected.prediction?.risk_label)}`}>
          {selected.prediction?.risk_label ?? "sin prediccion"}
        </span>
      </div>
      {selected.status !== "ok" && (
        <div className="mt-4 rounded border border-sky-300 bg-sky-50 p-3 text-sm text-sky-950">
          <strong className="block">{equipmentStatusLabel(selected.status)}</strong>
          <span>{equipmentStatusDetail(selected.status)}</span>
        </div>
      )}
      {!selected.observation ? (
        <EmptyState title="Sin lectura de sensor" detail="No hay observaciones recientes para inferir riesgo." />
      ) : (
        <div className="mt-4 grid gap-2 text-sm sm:grid-cols-2">
          <span>Temperatura: <strong>{selected.observation.temperature_c} C</strong></span>
          <span>Vibracion: <strong>{selected.observation.vibration_mm_s} mm/s</strong></span>
          <span>Presion: <strong>{selected.observation.pressure_bar} bar</strong></span>
          <span>RPM: <strong>{selected.observation.rpm}</strong></span>
          <span>Carga: <strong>{selected.observation.load_pct}%</strong></span>
          <span>Calidad sensor: <strong>{selected.observation.sensor_quality}</strong></span>
          <span className="sm:col-span-2">Lectura: <strong>{formatDate(selected.observation.observed_at)}</strong></span>
        </div>
      )}
      {selected.prediction && (
        <div className="mt-4 rounded bg-panel p-3 text-sm">
          Modelo {selected.prediction.model_version} con {selected.prediction.feature_count} variables. Puntaje {selected.prediction.risk_score.toFixed(2)}.
        </div>
      )}
    </section>
  );
}

function MaintenancePanel({ logs, equipment }: { logs: MaintenanceLogItem[]; equipment: Map<string, AssetHierarchyItem> }) {
  if (logs.length === 0) {
    return <EmptyState title="Bitacora" detail="Sin registros" />;
  }
  return (
    <div className="overflow-hidden rounded border border-steel bg-white">
      <table className="w-full min-w-[1080px] text-left text-sm">
        <thead className="bg-panel text-xs uppercase text-zinc-600">
          <tr>
            <th className="px-4 py-3">Reportado</th>
            <th className="px-4 py-3">Planta</th>
            <th className="px-4 py-3">Linea</th>
            <th className="px-4 py-3">Celula</th>
            <th className="px-4 py-3">Equipo</th>
            <th className="px-4 py-3">Clase</th>
            <th className="px-4 py-3">Estado operador</th>
            <th className="px-4 py-3">Falla</th>
            <th className="px-4 py-3">Observacion</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-steel">
          {logs.map((log) => {
            const asset = equipment.get(log.equipment_id);
            return (
              <tr key={log.maintenance_log_id}>
                <td className="px-4 py-3">{formatDate(log.reported_at)}</td>
                <td className="px-4 py-3">{asset?.plant_code ?? "N/D"}</td>
                <td className="px-4 py-3">{asset?.line_code ?? "N/D"}</td>
                <td className="px-4 py-3">{asset?.cell_code ?? "N/D"}</td>
                <td className="px-4 py-3 font-medium">{asset?.equipment_code ?? log.equipment_id}</td>
                <td className="px-4 py-3">{asset?.equipment_class ?? "N/D"}</td>
                <td className="px-4 py-3">{log.operator_state}</td>
                <td className="px-4 py-3">{log.failure_code ?? "Sin codigo"}</td>
                <td className="px-4 py-3">{log.free_text_observation || "Sin texto"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function MaintenanceForm({
  credentials,
  equipment,
  catalog,
  onCreated,
}: {
  credentials: ApiCredentials;
  equipment: AssetHierarchyItem[];
  catalog: FailureCatalogItem[];
  onCreated: () => void;
}) {
  const [equipmentId, setEquipmentId] = React.useState("");
  const [state, setState] = React.useState("requires_review");
  const [failureCode, setFailureCode] = React.useState("");
  const [observation, setObservation] = React.useState("");
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState("");
  const selectedEquipment = equipment.find((item) => item.equipment_id === equipmentId);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!equipmentId) return;
    setSaving(true);
    setError("");
    try {
      await api.createMaintenanceLog(credentials, {
        equipment_id: equipmentId,
        reported_at: new Date().toISOString(),
        operator_state: state,
        failure_code: failureCode || null,
        free_text_observation: observation,
      });
      setObservation("");
      onCreated();
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "No fue posible guardar el registro.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={submit} className="grid gap-3 rounded border border-steel bg-white p-4 md:grid-cols-4">
      <label className="text-xs font-medium text-zinc-700">
        Equipo
        <select className="mt-1 w-full rounded border border-steel px-3 py-2 text-sm" value={equipmentId} onChange={(event) => setEquipmentId(event.target.value)}>
          <option value="">Seleccionar</option>
          {equipment.map((item) => (
            <option key={item.equipment_id} value={item.equipment_id}>{item.equipment_code}</option>
          ))}
        </select>
      </label>
      <label className="text-xs font-medium text-zinc-700">
        Planta
        <input className="mt-1 w-full rounded border border-steel bg-panel px-3 py-2 text-sm" value={selectedEquipment?.plant_code ?? ""} readOnly />
      </label>
      <label className="text-xs font-medium text-zinc-700">
        Linea
        <input className="mt-1 w-full rounded border border-steel bg-panel px-3 py-2 text-sm" value={selectedEquipment?.line_code ?? ""} readOnly />
      </label>
      <label className="text-xs font-medium text-zinc-700">
        Celula
        <input className="mt-1 w-full rounded border border-steel bg-panel px-3 py-2 text-sm" value={selectedEquipment?.cell_code ?? ""} readOnly />
      </label>
      <label className="text-xs font-medium text-zinc-700">
        Clase equipo
        <input className="mt-1 w-full rounded border border-steel bg-panel px-3 py-2 text-sm" value={selectedEquipment?.equipment_class ?? ""} readOnly />
      </label>
      <label className="text-xs font-medium text-zinc-700">
        Estado operador
        <select className="mt-1 w-full rounded border border-steel px-3 py-2 text-sm" value={state} onChange={(event) => setState(event.target.value)}>
          <option value="operational">operational</option>
          <option value="requires_review">requires_review</option>
          <option value="down">down</option>
        </select>
      </label>
      <label className="text-xs font-medium text-zinc-700">
        Codigo falla
        <select className="mt-1 w-full rounded border border-steel px-3 py-2 text-sm" value={failureCode} onChange={(event) => setFailureCode(event.target.value)}>
          <option value="">Sin codigo</option>
          {catalog.filter((item) => item.is_active).map((item) => (
            <option key={item.failure_code} value={item.failure_code}>{item.failure_code}</option>
          ))}
        </select>
      </label>
      <label className="text-xs font-medium text-zinc-700 md:col-span-2">
        Observacion
        <textarea className="mt-1 min-h-20 w-full rounded border border-steel px-3 py-2 text-sm" value={observation} onChange={(event) => setObservation(event.target.value)} />
      </label>
      {error && <div className="text-sm text-danger md:col-span-3">{error}</div>}
      <button className="h-10 rounded bg-signal px-4 text-sm font-semibold text-white disabled:opacity-60 md:col-start-4" disabled={saving || !equipmentId}>
        Guardar bitacora
      </button>
    </form>
  );
}

export function App() {
  const [credentials, setCredentials] = React.useState<ApiCredentials>({ username: "", password: "" });
  const [tab, setTab] = React.useState<"dashboard" | "maintenance">("dashboard");
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");
  const [partial, setPartial] = React.useState("");
  const [assets, setAssets] = React.useState<AssetHierarchyItem[]>([]);
  const [risks, setRisks] = React.useState<EquipmentRisk[]>([]);
  const [logs, setLogs] = React.useState<MaintenanceLogItem[]>([]);
  const [catalog, setCatalog] = React.useState<FailureCatalogItem[]>([]);
  const [selectedId, setSelectedId] = React.useState<string>();
  const [hasLoadedData, setHasLoadedData] = React.useState(false);

  const equipmentMap = React.useMemo(() => new Map(assets.map((asset) => [asset.equipment_id, asset])), [assets]);
  const selectedRisk = risks.find((risk) => risk.asset.equipment_id === selectedId) ?? risks[0];

  async function load() {
    setLoading(true);
    setError("");
    setPartial("");
    try {
      const [hierarchy, observationsResult, logsResult, catalogResult] = await Promise.all([
        api.hierarchy(credentials),
        api.observations(credentials),
        api.maintenanceLogs(credentials),
        api.failureCatalog(credentials),
      ]);
      const latest = latestByEquipment(observationsResult.items);
      const riskResults = await Promise.all(
        hierarchy.items.map(async (asset): Promise<EquipmentRisk> => {
          const observation = latest.get(asset.equipment_id);
          if (!observation) return { asset, status: "no-sensor" };
          try {
            return { asset, observation, prediction: await api.prediction(credentials, asset, observation), status: "ok" };
          } catch {
            return { asset, observation, status: "prediction-unavailable" };
          }
        }),
      );
      setAssets(hierarchy.items);
      setRisks(riskResults);
      setLogs(logsResult.items);
      setCatalog(catalogResult.items);
      setSelectedId((current) => current ?? hierarchy.items[0]?.equipment_id);
      setHasLoadedData(true);
      if (riskResults.some((risk) => risk.status !== "ok")) {
        setPartial("Algunos equipos no tienen sensores recientes o el modelo predictivo no esta disponible.");
      }
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "No fue posible conectar con la API.");
      setHasLoadedData(false);
      setAssets([]);
      setRisks([]);
      setLogs([]);
      setCatalog([]);
      setSelectedId(undefined);
    } finally {
      setLoading(false);
    }
  }

  function changeCredentials(next: ApiCredentials) {
    setCredentials(next);
    setHasLoadedData(false);
    setError("");
    setPartial("");
  }

  return (
    <main className="min-h-screen bg-panel text-ink">
      <AuthPanel credentials={credentials} onChange={changeCredentials} onRefresh={load} loading={loading} />
      <nav className="flex gap-2 border-b border-steel bg-white px-4 py-2">
        <button className={`rounded px-3 py-2 text-sm font-semibold ${tab === "dashboard" ? "bg-ink text-white" : "text-zinc-700"}`} onClick={() => setTab("dashboard")}>
          Dashboard
        </button>
        <button className={`rounded px-3 py-2 text-sm font-semibold ${tab === "maintenance" ? "bg-ink text-white" : "text-zinc-700"}`} onClick={() => setTab("maintenance")}>
          Bitacora
        </button>
      </nav>
      <div className="mx-auto max-w-7xl space-y-4 px-4 py-5">
        <ApiNotice error={error} partial={partial} />
        {!credentials.username || !credentials.password ? (
          <EmptyState title="Autenticacion requerida" detail="Ingrese credenciales Basic para consultar endpoints de negocio de /api/v1." />
        ) : !hasLoadedData && !loading ? (
          <EmptyState title="Actualizacion requerida" detail="Presione Actualizar para consultar la API con las credenciales Basic capturadas." />
        ) : loading && risks.length === 0 ? (
          <EmptyState title="Cargando datos operativos" detail="Consultando jerarquia, sensores, predicciones y bitacora." />
        ) : tab === "dashboard" ? (
          <>
            <MetricsStrip risks={risks} logs={logs} />
            <div className="grid gap-4 lg:grid-cols-[1fr_380px]">
              <section className="rounded border border-steel bg-white p-4">
                <div className="mb-4">
                  <p className="text-xs font-semibold uppercase text-signal">Mapa de calor predictivo</p>
                  <h2 className="text-lg font-semibold text-ink">Planta, linea, celula y equipo</h2>
                </div>
                <RiskHeatMap risks={risks} selectedId={selectedRisk?.asset.equipment_id} onSelect={setSelectedId} />
              </section>
              <AlgorithmicPanel selected={selectedRisk} />
            </div>
          </>
        ) : (
          <section className="space-y-4">
            <div>
              <p className="text-xs font-semibold uppercase text-signal">Realidad operativa declarada</p>
              <h2 className="text-lg font-semibold text-ink">Bitacora de mantenimiento</h2>
            </div>
            <MaintenanceForm credentials={credentials} equipment={assets} catalog={catalog} onCreated={load} />
            <MaintenancePanel logs={logs} equipment={equipmentMap} />
          </section>
        )}
      </div>
    </main>
  );
}

const rootElement = document.getElementById("root");

if (rootElement) {
  createRoot(rootElement).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  );
}
