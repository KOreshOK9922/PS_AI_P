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

interface AgentStatus {
  name: string
  icon: string
  status: 'idle' | 'working' | 'done' | 'error'
  detail: string
}

interface ModelObject {
  name: string
  class: string
  params: Record<string, number>
  x: number
  y: number
  connected: boolean
}

interface ResearchResult {
  method: string
  code: string
  success: boolean
  error?: string
  time: number
}

type AppState = 'idle' | 'connecting' | 'parsing' | 'building' | 'executing' | 'researching' | 'done' | 'error'

const API_BASE = 'http://localhost:8000'

// ─── Main App ────────────────────────────────────────────────────────
export default function App() {
  const [description, setDescription] = useState('')
  const [appState, setAppState] = useState<AppState>('idle')
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [agents, setAgents] = useState<AgentStatus[]>(getDefaultAgents())
  const [modelObjects, setModelObjects] = useState<ModelObject[]>([])
  const [researchResults, setResearchResults] = useState<ResearchResult[]>([])
  const [backendOnline, setBackendOnline] = useState(false)
  const [ollamaOnline, setOllamaOnline] = useState(false)
  const [psOnline, setPsOnline] = useState(false)
  const [activeTab, setActiveTab] = useState<'control' | 'model' | 'research' | 'logs'>('control')
  const [autoResearch, setAutoResearch] = useState(true)
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
        
        // Update agents from log
        data.forEach(entry => {
          if (entry.agent === 'ARCHITECT') setAgents(prev => prev.map(a => a.name === 'Архитектор' ? { ...a, status: 'working', detail: entry.msg } : a))
          if (entry.agent === 'BUILDER') setAgents(prev => prev.map(a => a.name === 'Строитель' ? { ...a, status: 'working', detail: entry.msg } : a))
          if (entry.agent === 'EXECUTOR') setAgents(prev => prev.map(a => a.name === 'Исполнитель' ? { ...a, status: 'working', detail: entry.msg } : a))
          if (entry.agent === 'DEBUGGER') setAgents(prev => prev.map(a => a.name === 'Отладчик' ? { ...a, status: 'working', detail: entry.msg } : a))
          if (entry.agent === 'RESEARCHER') setAgents(prev => prev.map(a => a.name === 'Исследователь' ? { ...a, status: 'working', detail: entry.msg } : a))
        })
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
    setModelObjects([])
    setResearchResults([])
    setAgents(getDefaultAgents())
    logIdRef.current = 0

    addLocalLog('INFO', 'SYSTEM', 'Запуск автономной системы...')

    try {
      const r = await fetch(`${API_BASE}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description, auto_research: autoResearch }),
      })
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      
      // Start polling
      setAppState('parsing')
      pollRef.current = setInterval(async () => {
        await pollLogs()
        try {
          const sr = await fetch(`${API_BASE}/status`, { signal: AbortSignal.timeout(2000) })
          const sd = await sr.json()
          if (sd.state === 'done') {
            setAppState('done')
            setAgents(prev => prev.map(a => ({ ...a, status: 'done' as const })))
            if (pollRef.current) clearInterval(pollRef.current)
          } else if (sd.state === 'error') {
            setAppState('error')
            if (pollRef.current) clearInterval(pollRef.current)
          } else {
            setAppState(sd.state as AppState)
          }
          if (sd.objects) setModelObjects(sd.objects)
          if (sd.research) setResearchResults(sd.research)
        } catch { /* ignore */ }
      }, 500)
    } catch (err: any) {
      addLocalLog('ERROR', 'SYSTEM', `Не удалось подключиться к бэкенду: ${err.message}`)
      addLocalLog('INFO', 'SYSTEM', 'Убедитесь что запущен: python backend/main.py')
      setAppState('error')
    }
  }

  const startResearch = async () => {
    setAppState('researching')
    setLogs([])
    setResearchResults([])
    logIdRef.current = 0
    addLocalLog('INFO', 'RESEARCHER', 'Запуск авто-исследования API Plant Simulation...')

    try {
      await fetch(`${API_BASE}/research`, { method: 'POST' })
      setAgents(prev => prev.map(a => a.name === 'Исследователь' ? { ...a, status: 'working', detail: 'Исследует API...' } : a))
      
      pollRef.current = setInterval(async () => {
        await pollLogs()
        try {
          const sr = await fetch(`${API_BASE}/status`, { signal: AbortSignal.timeout(2000) })
          const sd = await sr.json()
          if (sd.research) setResearchResults(sd.research)
          if (sd.state === 'done') {
            setAppState('done')
            setAgents(prev => prev.map(a => a.name === 'Исследователь' ? { ...a, status: 'done', detail: 'Исследование завершено' } : a))
            if (pollRef.current) clearInterval(pollRef.current)
          }
        } catch { /* ignore */ }
      }, 500)
    } catch (err: any) {
      addLocalLog('ERROR', 'SYSTEM', `Ошибка: ${err.message}`)
      setAppState('error')
    }
  }

  const reset = () => {
    setAppState('idle')
    setLogs([])
    setModelObjects([])
    setResearchResults([])
    setAgents(getDefaultAgents())
    logIdRef.current = 0
    if (pollRef.current) clearInterval(pollRef.current)
  }

  const addLocalLog = (level: LogEntry['level'], agent: string, msg: string) => {
    const entry: LogEntry = {
      id: ++logIdRef.current,
      time: new Date().toLocaleTimeString('ru-RU'),
      level, agent, msg,
    }
    setLogs(prev => [...prev, entry])
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
              <p className="text-[11px] text-gray-500">Автономная система • Plant Simulation 2404</p>
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
                placeholder="Источник заготовок с интервалом 3 минуты, станция обработки 20 секунд, накопитель на 10 мест, сход"
                className="w-full h-32 bg-gray-950 border border-gray-700 rounded-lg p-3 text-sm text-gray-200 placeholder-gray-600 resize-none focus:outline-none focus:border-blue-600 transition-colors"
                disabled={appState !== 'idle' && appState !== 'done' && appState !== 'error'}
              />
              
              <div className="flex items-center gap-2 mt-3">
                <label className="flex items-center gap-2 text-xs text-gray-400 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={autoResearch}
                    onChange={e => setAutoResearch(e.target.checked)}
                    className="rounded bg-gray-800 border-gray-600"
                  />
                  Авто-исследование при ошибках
                </label>
              </div>

              <div className="flex gap-2 mt-3">
                <button
                  onClick={startAgent}
                  disabled={appState !== 'idle' && appState !== 'done' && appState !== 'error'}
                  className="flex-1 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 text-white font-medium text-sm transition-colors"
                >
                  {appState === 'idle' ? '▶ Запустить агента' : appState === 'done' ? '▶ Запустить снова' : '⏳ Работает...'}
                </button>
                <button
                  onClick={startResearch}
                  disabled={appState !== 'idle' && appState !== 'done' && appState !== 'error'}
                  className="px-4 py-2.5 rounded-lg bg-purple-600/20 border border-purple-600/40 hover:bg-purple-600/30 disabled:bg-gray-800 disabled:border-gray-700 disabled:text-gray-600 text-purple-300 text-sm transition-colors"
                  title="Исследовать API Plant Simulation"
                >
                  🔬
                </button>
                {(appState === 'done' || appState === 'error') && (
                  <button
                    onClick={reset}
                    className="px-4 py-2.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm transition-colors"
                  >
                    ↺
                  </button>
                )}
              </div>
            </div>

            {/* Agent Status */}
            <div className="rounded-xl bg-gray-900 border border-gray-800 p-4">
              <h3 className="text-sm font-medium text-gray-300 mb-3">Агенты</h3>
              <div className="space-y-2">
                {agents.map(agent => (
                  <div key={agent.name} className="flex items-center gap-3 p-2 rounded-lg bg-gray-800/50">
                    <span className="text-lg">{agent.icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-medium text-gray-200">{agent.name}</div>
                      <div className="text-[11px] text-gray-500 truncate">{agent.detail}</div>
                    </div>
                    <AgentBadge status={agent.status} />
                  </div>
                ))}
              </div>
            </div>

            {/* Quick Examples */}
            <div className="rounded-xl bg-gray-900 border border-gray-800 p-4">
              <h3 className="text-sm font-medium text-gray-300 mb-3">Примеры</h3>
              <div className="space-y-2">
                {[
                  'Источник 3 мин, станция 20 сек, буфер 10, сход',
                  'Генератор каждые 60 секунд, две станции по 15 секунд, накопитель 5, выход',
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
          </div>

          {/* ─── Right: Main Content ─── */}
          <div className="lg:col-span-2 space-y-4">
            {/* Tabs */}
            <div className="flex gap-1 bg-gray-900 rounded-xl p-1 border border-gray-800">
              {([
                ['control', '📡 Управление'],
                ['model', '🏗️ Модель'],
                ['research', '🔬 Исследование'],
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
                {activeTab === 'control' && (
                  <ControlPanel
                    appState={appState}
                    logs={logs}
                    logEndRef={logEndRef}
                  />
                )}
                {activeTab === 'model' && (
                  <ModelView objects={modelObjects} />
                )}
                {activeTab === 'research' && (
                  <ResearchView results={researchResults} />
                )}
                {activeTab === 'logs' && (
                  <LogsView logs={logs} logEndRef={logEndRef} />
                )}
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

function AgentBadge({ status }: { status: AgentStatus['status'] }) {
  const config = {
    idle: { color: 'bg-gray-600', label: 'Ожидание' },
    working: { color: 'bg-blue-500 animate-pulse', label: 'Работа' },
    done: { color: 'bg-green-500', label: 'Готово' },
    error: { color: 'bg-red-500', label: 'Ошибка' },
  }
  const c = config[status]
  return (
    <div className="flex items-center gap-1">
      <div className={`w-1.5 h-1.5 rounded-full ${c.color}`} />
      <span className="text-[10px] text-gray-500">{c.label}</span>
    </div>
  )
}

function ControlPanel({ appState, logs, logEndRef }: {
  appState: AppState; logs: LogEntry[]; logEndRef: React.RefObject<HTMLDivElement>
}) {
  const stateInfo: Record<AppState, { icon: string; label: string; color: string }> = {
    idle: { icon: '💤', label: 'Ожидание запуска', color: 'text-gray-400' },
    connecting: { icon: '🔌', label: 'Подключение к системам...', color: 'text-blue-400' },
    parsing: { icon: '🧠', label: 'Архитектор анализирует описание...', color: 'text-purple-400' },
    building: { icon: '🔧', label: 'Строитель генерирует код...', color: 'text-cyan-400' },
    executing: { icon: '⚡', label: 'Исполнитель создаёт модель...', color: 'text-green-400' },
    researching: { icon: '🔬', label: 'Исследователь изучает API...', color: 'text-amber-400' },
    done: { icon: '✅', label: 'Модель построена!', color: 'text-green-400' },
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
              {appState === 'idle' ? 'Нажмите "Запустить агента" для начала работы' : 'Ожидание логов...'}
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
    DEBUGGER: 'bg-amber-700',
    RESEARCHER: 'bg-pink-700',
    PARSER: 'bg-teal-700',
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

function ModelView({ objects }: { objects: ModelObject[] }) {
  if (objects.length === 0) {
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
      <h3 className="text-sm font-medium text-gray-300 mb-4">Схема модели</h3>
      <div className="flex items-center gap-2 overflow-x-auto pb-4">
        {objects.map((obj, i) => (
          <div key={obj.name} className="flex items-center gap-2">
            <div className={`shrink-0 rounded-xl border p-4 text-center min-w-[120px] ${
              obj.connected
                ? 'bg-green-950/30 border-green-700/40'
                : 'bg-gray-800 border-gray-700'
            }`}>
              <div className="text-2xl mb-1">
                {obj.class === 'Source' ? '📦' : obj.class === 'Station' ? '⚙️' : obj.class === 'Buffer' ? '📋' : '🚪'}
              </div>
              <div className="text-xs font-medium text-white">{obj.name}</div>
              <div className="text-[10px] text-gray-400">{obj.class}</div>
              {Object.entries(obj.params).map(([k, v]) => (
                <div key={k} className="text-[10px] text-gray-500">{k}: {v}</div>
              ))}
            </div>
            {i < objects.length - 1 && (
              <div className={`text-lg ${obj.connected ? 'text-green-400' : 'text-gray-600'}`}>
                {obj.connected ? '→' : '⇢'}
              </div>
            )}
          </div>
        ))}
      </div>
      
      {/* Object list */}
      <div className="mt-4 space-y-2">
        {objects.map(obj => (
          <div key={obj.name} className="flex items-center gap-3 p-2 rounded-lg bg-gray-800/50 text-xs">
            <span className={`w-2 h-2 rounded-full ${obj.connected ? 'bg-green-400' : 'bg-yellow-400'}`} />
            <span className="text-gray-200 font-medium">{obj.name}</span>
            <span className="text-gray-500">{obj.class}</span>
            <span className="text-gray-600 ml-auto">
              {Object.entries(obj.params).map(([k, v]) => `${k}=${v}`).join(', ') || 'без параметров'}
            </span>
            <span className={`px-1.5 py-0.5 rounded text-[10px] ${obj.connected ? 'bg-green-800/40 text-green-300' : 'bg-yellow-800/40 text-yellow-300'}`}>
              {obj.connected ? 'соединён' : 'нет связи'}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

function ResearchView({ results }: { results: ResearchResult[] }) {
  if (results.length === 0) {
    return (
      <div className="rounded-xl bg-gray-900 border border-gray-800 p-12 text-center">
        <div className="text-4xl mb-3">🔬</div>
        <div className="text-gray-400">Исследование не запущено</div>
        <div className="text-xs text-gray-600 mt-1">Нажмите 🔬 для авто-исследования API Plant Simulation</div>
        <div className="mt-6 text-left bg-gray-950 rounded-lg p-4 text-xs text-gray-500 max-w-md mx-auto">
          <p className="mb-2">Исследователь автоматически:</p>
          <ul className="space-y-1 list-disc list-inside">
            <li>Создаёт тестовые объекты</li>
            <li>Пробует все известные методы соединений</li>
            <li>Тестирует новые комбинации API</li>
            <li>Записывает рабочие и нерабочие методы</li>
            <li>Интроспекция атрибутов объектов</li>
          </ul>
        </div>
      </div>
    )
  }

  const success = results.filter(r => r.success).length
  const failed = results.filter(r => !r.success).length

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <div className="flex-1 rounded-xl bg-green-950/20 border border-green-800/30 p-4 text-center">
          <div className="text-2xl font-bold text-green-400">{success}</div>
          <div className="text-xs text-green-300">Работает</div>
        </div>
        <div className="flex-1 rounded-xl bg-red-950/20 border border-red-800/30 p-4 text-center">
          <div className="text-2xl font-bold text-red-400">{failed}</div>
          <div className="text-xs text-red-300">Не работает</div>
        </div>
        <div className="flex-1 rounded-xl bg-blue-950/20 border border-blue-800/30 p-4 text-center">
          <div className="text-2xl font-bold text-blue-400">{results.length}</div>
          <div className="text-xs text-blue-300">Всего проверено</div>
        </div>
      </div>

      <div className="rounded-xl bg-gray-900 border border-gray-800 overflow-hidden">
        <div className="px-4 py-2 border-b border-gray-800">
          <span className="text-sm text-gray-400">Результаты исследования API</span>
        </div>
        <div className="divide-y divide-gray-800 max-h-[500px] overflow-y-auto">
          {results.map((r, i) => (
            <div key={i} className="p-3 hover:bg-gray-800/30">
              <div className="flex items-center gap-2 mb-1">
                <span className={r.success ? 'text-green-400' : 'text-red-400'}>
                  {r.success ? '✅' : '❌'}
                </span>
                <span className="text-sm text-white font-medium">{r.method}</span>
                <span className="text-[10px] text-gray-600 ml-auto">{r.time}ms</span>
              </div>
              <code className="text-[11px] text-cyan-300 font-mono block mb-1 truncate">{r.code}</code>
              {r.error && <div className="text-[11px] text-red-400 truncate">{r.error}</div>}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function LogsView({ logs, logEndRef }: { logs: LogEntry[]; logEndRef: React.RefObject<HTMLDivElement> }) {
  return (
    <div className="rounded-xl bg-gray-900 border border-gray-800 overflow-hidden">
      <div className="px-4 py-2 border-b border-gray-800 flex items-center justify-between">
        <span className="text-sm text-gray-400">Полный журнал</span>
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

// ─── Helpers ─────────────────────────────────────────────────────────

function getDefaultAgents(): AgentStatus[] {
  return [
    { name: 'Архитектор', icon: '🏗️', status: 'idle', detail: 'Ожидание' },
    { name: 'Строитель', icon: '🔨', status: 'idle', detail: 'Ожидание' },
    { name: 'Исполнитель', icon: '⚡', status: 'idle', detail: 'Ожидание' },
    { name: 'Отладчик', icon: '🐛', status: 'idle', detail: 'Ожидание' },
    { name: 'Исследователь', icon: '🔬', status: 'idle', detail: 'Ожидание' },
  ]
}
