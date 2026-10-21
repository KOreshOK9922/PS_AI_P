import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

// ─── Types ───────────────────────────────────────────────────────────
interface LogEntry {
  id: number
  time: string
  level: 'INFO' | 'WARN' | 'ERROR' | 'SUCCESS' | 'RESEARCH'
  agent: string
  msg: string
}

interface ModelObject {
  name: string
  class: string
  x: number
  y: number
  params: Record<string, number>
}

interface Spec {
  objects: ModelObject[]
  connections: string[][]
}

type AppState = 'idle' | 'connecting' | 'parsing' | 'building' | 'executing' | 'testing' | 'done' | 'error'

const API_BASE = 'http://localhost:7860'

// ─── Main App ────────────────────────────────────────────────────────
export default function App() {
  const [description, setDescription] = useState('')
  const [appState, setAppState] = useState<AppState>('idle')
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [spec, setSpec] = useState<Spec | null>(null)
  const [code, setCode] = useState('')
  const [backendOnline, setBackendOnline] = useState(false)
  const [ollamaOnline, setOllamaOnline] = useState(false)
  const [psOnline, setPsOnline] = useState(false)
  const [activeTab, setActiveTab] = useState<'control' | 'spec' | 'code' | 'model' | 'logs'>('control')
  const logEndRef = useRef<HTMLDivElement>(null!)
  const logIdRef = useRef(0)
  const pollRef = useRef<ReturnType<typeof setInterval>>()

  // ─── Health check ─────────────────────────────────────────────────
  useEffect(() => {
    const check = async () => {
      try {
        const r = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(2000) })
        const d = await r.json()
        setBackendOnline(true)
        setOllamaOnline(d.ollama ?? false)
        setPsOnline(d.plant_simulation ?? false)
      } catch {
        setBackendOnline(false)
        setOllamaOnline(false)
        setPsOnline(false)
      }
    }
    check()
    const iv = setInterval(check, 5000)
    return () => clearInterval(iv)
  }, [])

  // ─── Log polling ──────────────────────────────────────────────────
  const pollLogs = useCallback(async () => {
    try {
      const r = await fetch(`${API_BASE}/logs?after=${logIdRef.current}`, { signal: AbortSignal.timeout(3000) })
      const data: LogEntry[] = await r.json()
      if (data.length > 0) {
        logIdRef.current = data[data.length - 1].id
        setLogs(prev => [...prev, ...data])
      }
    } catch { /* ignore */ }
  }, [])

  useEffect(() => {
    if (appState !== 'idle') {
      pollRef.current = setInterval(pollLogs, 500)
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [appState, pollLogs])

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  // ─── Actions ──────────────────────────────────────────────────────
  const startAgent = async () => {
    if (!description.trim()) return
    setAppState('connecting')
    setLogs([])
    setSpec(null)
    setCode('')
    logIdRef.current = 0

    try {
      const r = await fetch(`${API_BASE}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description, output_path: 'model.spp' }),
      })
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      
      setAppState('parsing')
      pollRef.current = setInterval(async () => {
        await pollLogs()
        try {
          const sr = await fetch(`${API_BASE}/status`, { signal: AbortSignal.timeout(2000) })
          const sd = await sr.json()
          if (sd.state === 'done') {
            setAppState('done')
            if (pollRef.current) clearInterval(pollRef.current)
          } else if (sd.state === 'error') {
            setAppState('error')
            if (pollRef.current) clearInterval(pollRef.current)
          } else {
            setAppState(sd.state as AppState)
          }
          if (sd.spec) setSpec(sd.spec)
          if (sd.code) setCode(sd.code)
        } catch { /* ignore */ }
      }, 500)
    } catch (err: any) {
      setLogs([{
        id: ++logIdRef.current,
        time: new Date().toLocaleTimeString('ru-RU'),
        level: 'ERROR',
        agent: 'SYSTEM',
        msg: `Не удалось подключиться: ${err.message}`,
      }])
      setAppState('error')
    }
  }

  const runDryRun = async () => {
    if (!description.trim()) return
    setAppState('parsing')
    setLogs([])
    logIdRef.current = 0

    try {
      const r = await fetch(`${API_BASE}/dry-run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description }),
      })
      const data = await r.json()
      if (data.error) {
        setLogs([{
          id: ++logIdRef.current,
          time: new Date().toLocaleTimeString('ru-RU'),
          level: 'ERROR',
          agent: 'SYSTEM',
          msg: data.error,
        }])
        setAppState('error')
      } else {
        setSpec(data.spec)
        setCode(data.code)
        setAppState('done')
        setLogs([{
          id: ++logIdRef.current,
          time: new Date().toLocaleTimeString('ru-RU'),
          level: 'SUCCESS',
          agent: 'SYSTEM',
          msg: 'Dry-run завершён успешно',
        }])
      }
    } catch (err: any) {
      setLogs([{
        id: ++logIdRef.current,
        time: new Date().toLocaleTimeString('ru-RU'),
        level: 'ERROR',
        agent: 'SYSTEM',
        msg: `Ошибка: ${err.message}`,
      }])
      setAppState('error')
    }
  }

  const runSelfTest = async () => {
    setAppState('testing')
    setLogs([])
    logIdRef.current = 0

    try {
      await fetch(`${API_BASE}/selftest`, { method: 'POST' })
      pollRef.current = setInterval(async () => {
        await pollLogs()
        try {
          const sr = await fetch(`${API_BASE}/status`, { signal: AbortSignal.timeout(2000) })
          const sd = await sr.json()
          if (sd.state === 'done') {
            setAppState('done')
            if (pollRef.current) clearInterval(pollRef.current)
          }
        } catch { /* ignore */ }
      }, 500)
    } catch (err: any) {
      setLogs([{
        id: ++logIdRef.current,
        time: new Date().toLocaleTimeString('ru-RU'),
        level: 'ERROR',
        agent: 'SYSTEM',
        msg: `Ошибка: ${err.message}`,
      }])
      setAppState('error')
    }
  }

  const reset = () => {
    setAppState('idle')
    setLogs([])
    setSpec(null)
    setCode('')
    logIdRef.current = 0
    if (pollRef.current) clearInterval(pollRef.current)
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="bg-gray-900/95 backdrop-blur border-b border-gray-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-lg">🏭</div>
            <div>
              <h1 className="text-lg font-bold text-white leading-tight">PS AI Agent</h1>
              <p className="text-[11px] text-gray-500">ТЗ v1.0 • Plant Simulation 2404 • Автономная система</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <StatusDot label="Backend" online={backendOnline} />
            <StatusDot label="Ollama" online={ollamaOnline} />
            <StatusDot label="Plant Sim" online={psOnline} />
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* ─── Left: Control Panel ─── */}
          <div className="lg:col-span-1 space-y-4">
            {/* Description Input */}
            <div className="rounded-xl bg-gray-900 border border-gray-800 p-4">
              <label className="text-sm font-medium text-gray-300 mb-2 block">Описание производственной линии</label>
              <textarea
                value={description}
                onChange={e => setDescription(e.target.value)}
                placeholder="Линия: источник заготовок с интервалом 3 минуты, станция обработки 20 секунд, накопитель на 10 мест, сход"
                className="w-full h-32 bg-gray-950 border border-gray-700 rounded-lg p-3 text-sm text-gray-200 placeholder-gray-600 resize-none focus:outline-none focus:border-blue-600 transition-colors"
                disabled={appState !== 'idle' && appState !== 'done' && appState !== 'error'}
              />

              <div className="flex gap-2 mt-3">
                <button
                  onClick={startAgent}
                  disabled={appState !== 'idle' && appState !== 'done' && appState !== 'error'}
                  className="flex-1 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 text-white font-medium text-sm transition-colors"
                >
                  {appState === 'idle' ? '▶ Запустить' : appState === 'done' ? '▶ Запустить снова' : '⏳ Работает...'}
                </button>
              </div>

              <div className="flex gap-2 mt-2">
                <button
                  onClick={runDryRun}
                  disabled={appState !== 'idle' && appState !== 'done' && appState !== 'error'}
                  className="flex-1 py-2 rounded-lg bg-cyan-600/20 border border-cyan-600/40 hover:bg-cyan-600/30 disabled:bg-gray-800 disabled:border-gray-700 disabled:text-gray-600 text-cyan-300 text-sm transition-colors"
                >
                  🧪 Dry Run
                </button>
                <button
                  onClick={runSelfTest}
                  disabled={appState !== 'idle' && appState !== 'done' && appState !== 'error'}
                  className="flex-1 py-2 rounded-lg bg-purple-600/20 border border-purple-600/40 hover:bg-purple-600/30 disabled:bg-gray-800 disabled:border-gray-700 disabled:text-gray-600 text-purple-300 text-sm transition-colors"
                >
                  🔧 Selftest
                </button>
              </div>

              {(appState === 'done' || appState === 'error') && (
                <button
                  onClick={reset}
                  className="w-full mt-2 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm transition-colors"
                >
                  ↺ Сброс
                </button>
              )}
            </div>

            {/* Quick Examples */}
            <div className="rounded-xl bg-gray-900 border border-gray-800 p-4">
              <h3 className="text-sm font-medium text-gray-300 mb-3">Примеры (US-1, US-2)</h3>
              <div className="space-y-2">
                {[
                  'Линия: источник заготовок с интервалом 3 минуты, станция обработки 20 секунд, накопитель на 10 мест, сход',
                  'Источник каждые 60 секунд, две станции по 15 секунд, буфер 5, выход',
                  'Source interval 120, Station procTime 30, Buffer capacity 20, Drain',
                ].map((ex, i) => (
                  <button
                    key={i}
                    onClick={() => setDescription(ex)}
                    className="w-full text-left text-xs text-gray-400 hover:text-blue-300 p-2 rounded bg-gray-800/30 hover:bg-gray-800 transition-colors"
                  >
                    {ex}
                  </button>
                ))}
              </div>
            </div>

            {/* API Rules Reference */}
            <div className="rounded-xl bg-gray-900 border border-gray-800 p-4">
              <h3 className="text-sm font-medium text-gray-300 mb-3">📋 API Rules (PS 2404)</h3>
              <div className="space-y-1 text-[11px]">
                <div className="flex items-center gap-2 text-green-400">
                  <span>✅</span>
                  <span className="text-gray-300">createObject(f, x, y)</span>
                </div>
                <div className="flex items-center gap-2 text-green-400">
                  <span>✅</span>
                  <span className="text-gray-300">Connector.connect(obj1, obj2)</span>
                </div>
                <div className="flex items-center gap-2 text-green-400">
                  <span>✅</span>
                  <span className="text-gray-300">Station, Buffer, Source, Drain</span>
                </div>
                <div className="flex items-center gap-2 text-red-400">
                  <span>❌</span>
                  <span className="text-gray-300">SingleProc, Entity (устарели)</span>
                </div>
                <div className="flex items-center gap-2 text-red-400">
                  <span>❌</span>
                  <span className="text-gray-300">obj.succ := obj2 (read-only)</span>
                </div>
              </div>
            </div>
          </div>

          {/* ─── Right: Main Content ─── */}
          <div className="lg:col-span-2 space-y-4">
            {/* Tabs */}
            <div className="flex gap-1 bg-gray-900 rounded-xl p-1 border border-gray-800">
              {([
                ['control', '📡 Управление'],
                ['spec', '📄 Спецификация'],
                ['code', '💻 SimTalk'],
                ['model', '🏗️ Модель'],
                ['logs', '📋 Логи'],
              ] as const).map(([id, label]) => (
                <button
                  key={id}
                  onClick={() => setActiveTab(id)}
                  className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                    activeTab === id ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.15 }}
              >
                {activeTab === 'control' && <ControlPanel appState={appState} logs={logs} logEndRef={logEndRef} />}
                {activeTab === 'spec' && <SpecView spec={spec} />}
                {activeTab === 'code' && <CodeView code={code} />}
                {activeTab === 'model' && <ModelView spec={spec} />}
                {activeTab === 'logs' && <LogsView logs={logs} logEndRef={logEndRef} />}
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Sub-components ──────────────────────────────────────────────────

function StatusDot({ label, online }: { label: string; online: boolean }) {
  return (
    <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-gray-800">
      <div className={`w-2 h-2 rounded-full ${online ? 'bg-green-400' : 'bg-red-400'} ${online ? 'animate-pulse' : ''}`} />
      <span className="text-[11px] text-gray-400">{label}</span>
    </div>
  )
}

function ControlPanel({ appState, logs, logEndRef }: {
  appState: AppState; logs: LogEntry[]; logEndRef: React.RefObject<HTMLDivElement>
}) {
  const stateInfo: Record<AppState, { icon: string; label: string; color: string }> = {
    idle: { icon: '💤', label: 'Ожидание запуска', color: 'text-gray-400' },
    connecting: { icon: '🔌', label: 'Подключение к Plant Simulation...', color: 'text-blue-400' },
    parsing: { icon: '🧠', label: 'Архитектор анализирует описание...', color: 'text-purple-400' },
    building: { icon: '🔧', label: 'Строитель генерирует SimTalk...', color: 'text-cyan-400' },
    executing: { icon: '⚡', label: 'Исполнитель создаёт модель...', color: 'text-green-400' },
    testing: { icon: '🔬', label: 'Самотестирование API...', color: 'text-amber-400' },
    done: { icon: '✅', label: 'Модель создана и сохранена!', color: 'text-green-400' },
    error: { icon: '❌', label: 'Ошибка — смотрите логи', color: 'text-red-400' },
  }
  const info = stateInfo[appState]

  return (
    <div className="space-y-4">
      {/* State Banner */}
      <div className="rounded-xl bg-gray-900 border border-gray-800 p-6 text-center">
        <div className="text-4xl mb-2">{info.icon}</div>
        <div className={`text-lg font-semibold ${info.color}`}>{info.label}</div>
        {appState !== 'idle' && (
          <div className="mt-4 flex justify-center gap-1">
            {['connecting', 'parsing', 'building', 'executing'].map((s, i) => (
              <div
                key={s}
                className={`h-1.5 w-12 rounded-full transition-colors ${
                  ['connecting', 'parsing', 'building', 'executing'].indexOf(appState) >= i
                    ? 'bg-blue-500'
                    : 'bg-gray-700'
                }`}
              />
            ))}
          </div>
        )}
      </div>

      {/* Live Log Preview */}
      <div className="rounded-xl bg-gray-900 border border-gray-800 overflow-hidden">
        <div className="px-4 py-2 border-b border-gray-800 flex items-center justify-between">
          <span className="text-sm text-gray-400">Живой журнал</span>
          <span className="text-xs text-gray-600">{logs.length} записей</span>
        </div>
        <div className="p-3 max-h-[400px] overflow-y-auto font-mono text-xs space-y-0.5">
          {logs.length === 0 && (
            <div className="text-gray-600 text-center py-8">
              {appState === 'idle' ? 'Нажмите "Запустить" для начала работы' : 'Ожидание логов...'}
            </div>
          )}
          {logs.slice(-50).map(entry => (
            <LogLine key={entry.id} entry={entry} />
          ))}
          <div ref={logEndRef} />
        </div>
      </div>
    </div>
  )
}

function LogLine({ entry }: { entry: LogEntry }) {
  const levelColors = {
    INFO: 'text-blue-400',
    WARN: 'text-yellow-400',
    ERROR: 'text-red-400',
    SUCCESS: 'text-green-400',
    RESEARCH: 'text-purple-400',
  }
  const agentColors: Record<string, string> = {
    SYSTEM: 'bg-gray-700',
    ARCHITECT: 'bg-purple-700',
    BUILDER: 'bg-cyan-700',
    EXECUTOR: 'bg-blue-700',
    VALIDATOR: 'bg-green-700',
    DEBUGGER: 'bg-amber-700',
    TEST: 'bg-pink-700',
  }
  return (
    <div className="flex items-start gap-2 py-0.5 hover:bg-gray-800/30 px-1 rounded">
      <span className="text-gray-600 shrink-0">{entry.time}</span>
      <span className={`shrink-0 w-14 ${levelColors[entry.level]}`}>{entry.level}</span>
      <span className={`shrink-0 px-1 rounded text-[10px] text-white ${agentColors[entry.agent] || 'bg-gray-600'}`}>
        {entry.agent}
      </span>
      <span className={entry.level === 'ERROR' ? 'text-red-300' : 'text-gray-300'}>{entry.msg}</span>
    </div>
  )
}

function SpecView({ spec }: { spec: Spec | null }) {
  if (!spec) {
    return (
      <div className="rounded-xl bg-gray-900 border border-gray-800 p-12 text-center">
        <div className="text-4xl mb-3">📄</div>
        <div className="text-gray-400">JSON-спецификация пока пуста</div>
        <div className="text-xs text-gray-600 mt-1">Запустите агента для генерации спецификации</div>
      </div>
    )
  }

  return (
    <div className="rounded-xl bg-gray-900 border border-gray-800 overflow-hidden">
      <div className="px-4 py-2 border-b border-gray-800 flex items-center justify-between">
        <span className="text-sm text-gray-400">JSON-спецификация (Internal Contract)</span>
        <button
          onClick={() => navigator.clipboard.writeText(JSON.stringify(spec, null, 2))}
          className="text-xs text-gray-500 hover:text-white px-2 py-1 rounded hover:bg-gray-800"
        >
          📋 Копировать
        </button>
      </div>
      <div className="p-4 max-h-[600px] overflow-y-auto">
        <pre className="text-sm font-mono text-green-300 whitespace-pre-wrap">
          {JSON.stringify(spec, null, 2)}
        </pre>
      </div>
    </div>
  )
}

function CodeView({ code }: { code: string }) {
  if (!code) {
    return (
      <div className="rounded-xl bg-gray-900 border border-gray-800 p-12 text-center">
        <div className="text-4xl mb-3">💻</div>
        <div className="text-gray-400">SimTalk код пока не сгенерирован</div>
        <div className="text-xs text-gray-600 mt-1">Запустите агента для генерации кода</div>
      </div>
    )
  }

  return (
    <div className="rounded-xl bg-gray-900 border border-gray-800 overflow-hidden">
      <div className="px-4 py-2 border-b border-gray-800 flex items-center justify-between">
        <span className="text-sm text-gray-400">Сгенерированный SimTalk код</span>
        <button
          onClick={() => navigator.clipboard.writeText(code)}
          className="text-xs text-gray-500 hover:text-white px-2 py-1 rounded hover:bg-gray-800"
        >
          📋 Копировать
        </button>
      </div>
      <div className="p-4 max-h-[600px] overflow-y-auto">
        <pre className="text-sm font-mono text-cyan-300 whitespace-pre-wrap">
          {code}
        </pre>
      </div>
    </div>
  )
}

function ModelView({ spec }: { spec: Spec | null }) {
  if (!spec || spec.objects.length === 0) {
    return (
      <div className="rounded-xl bg-gray-900 border border-gray-800 p-12 text-center">
        <div className="text-4xl mb-3">🏗️</div>
        <div className="text-gray-400">Модель пока пуста</div>
        <div className="text-xs text-gray-600 mt-1">Запустите агента для создания модели</div>
      </div>
    )
  }

  return (
    <div className="rounded-xl bg-gray-900 border border-gray-800 p-6">
      <h3 className="text-sm font-medium text-gray-300 mb-4">Схема модели (координаты из спецификации)</h3>
      
      {/* Visual representation */}
      <div className="relative bg-gray-950 rounded-lg p-6 min-h-[200px] overflow-x-auto">
        <div className="flex items-center gap-4">
          {spec.objects.map((obj, i) => (
            <div key={obj.name} className="flex items-center gap-4">
              <div className="shrink-0 rounded-xl border border-blue-700/40 bg-blue-950/30 p-4 text-center min-w-[120px]">
                <div className="text-2xl mb-1">
                  {obj.class === 'Source' ? '📦' : obj.class === 'Station' ? '⚙️' : obj.class === 'Buffer' ? '📋' : '🚪'}
                </div>
                <div className="text-xs font-medium text-white">{obj.name}</div>
                <div className="text-[10px] text-gray-400">{obj.class}</div>
                <div className="text-[10px] text-gray-500 mt-1">
                  ({obj.x}, {obj.y})
                </div>
                {Object.entries(obj.params).map(([k, v]) => (
                  <div key={k} className="text-[10px] text-gray-500">{k}: {v}</div>
                ))}
              </div>
              {i < spec.objects.length - 1 && (
                <div className="text-lg text-green-400">→</div>
              )}
            </div>
          ))}
        </div>
      </div>
      
      {/* Object list */}
      <div className="mt-4 space-y-2">
        <h4 className="text-xs font-medium text-gray-400 uppercase">Объекты ({spec.objects.length})</h4>
        {spec.objects.map(obj => (
          <div key={obj.name} className="flex items-center gap-3 p-2 rounded-lg bg-gray-800/50 text-xs">
            <span className="w-2 h-2 rounded-full bg-green-400" />
            <span className="text-gray-200 font-medium">{obj.name}</span>
            <span className="text-gray-500">{obj.class}</span>
            <span className="text-gray-600">({obj.x}, {obj.y})</span>
            <span className="text-gray-600 ml-auto">
              {Object.entries(obj.params).map(([k, v]) => `${k}=${v}`).join(', ') || 'без параметров'}
            </span>
          </div>
        ))}
      </div>

      {/* Connections */}
      <div className="mt-4 space-y-2">
        <h4 className="text-xs font-medium text-gray-400 uppercase">Соединения ({spec.connections.length})</h4>
        {spec.connections.map((conn, i) => (
          <div key={i} className="flex items-center gap-3 p-2 rounded-lg bg-gray-800/50 text-xs">
            <span className="text-green-400">→</span>
            <span className="text-gray-200">{conn[0]}</span>
            <span className="text-gray-500">→</span>
            <span className="text-gray-200">{conn[1]}</span>
            <span className="text-gray-600 ml-auto">Connector.connect()</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function LogsView({ logs, logEndRef }: { logs: LogEntry[]; logEndRef: React.RefObject<HTMLDivElement> }) {
  return (
    <div className="rounded-xl bg-gray-900 border border-gray-800 overflow-hidden">
      <div className="px-4 py-2 border-b border-gray-800 flex items-center justify-between">
        <span className="text-sm text-gray-400">Полный журнал (agent_log.txt)</span>
        <span className="text-xs text-gray-600">{logs.length} записей</span>
      </div>
      <div className="p-3 max-h-[600px] overflow-y-auto font-mono text-xs space-y-0.5">
        {logs.length === 0 && (
          <div className="text-gray-600 text-center py-8">Журнал пуст</div>
        )}
        {logs.map(entry => (
          <LogLine key={entry.id} entry={entry} />
        ))}
        <div ref={logEndRef} />
      </div>
    </div>
  )
}
