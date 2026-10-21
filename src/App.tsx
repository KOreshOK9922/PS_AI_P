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

interface AgentStatus {
  name: string
  status: 'idle' | 'working' | 'done' | 'error' | 'waiting'
}

interface KnowledgeMethod {
  name: string
  template: string
  success_rate: number
  attempts: number
  successes: number
  notes: string
}

interface KnowledgeClass {
  name: string
  create_method: string
  params: string | null
  notes: string
  verified: boolean
}

type AppState = 'idle' | 'initializing' | 'connecting' | 'parsing' | 'building' | 'executing' | 'researching' | 'testing' | 'done' | 'error'

const API_BASE = 'http://localhost:7860'

// ─── Main App ────────────────────────────────────────────────────────
export default function App() {
  const [description, setDescription] = useState('')
  const [appState, setAppState] = useState<AppState>('idle')
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [spec, setSpec] = useState<Spec | null>(null)
  const [code, setCode] = useState('')
  const [agents, setAgents] = useState<Record<string, string>>({})
  const [backendOnline, setBackendOnline] = useState(false)
  const [psOnline, setPsOnline] = useState(false)
  const [psMethod, setPsMethod] = useState<string>('')
  const [activeTab, setActiveTab] = useState<'control' | 'agents' | 'spec' | 'code' | 'model' | 'knowledge' | 'logs'>('control')
  const [parallelResearch, setParallelResearch] = useState(false)
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
        setPsOnline(d.plant_simulation ?? false)
        setPsMethod(d.connection_method ?? '')
      } catch {
        setBackendOnline(false)
        setPsOnline(false)
        setPsMethod('')
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
    setAppState('initializing')
    setLogs([])
    setSpec(null)
    setCode('')
    setAgents({})
    logIdRef.current = 0

    try {
      const r = await fetch(`${API_BASE}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          description, 
          output_path: 'model.spp',
          parallel_research: parallelResearch 
        }),
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
          if (sd.agents) setAgents(sd.agents)
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

  const runResearch = async (task: string = 'full') => {
    setAppState('researching')
    setLogs([])
    logIdRef.current = 0

    try {
      await fetch(`${API_BASE}/research`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task }),
      })
      
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
      setAppState('error')
    }
  }

  const reset = () => {
    setAppState('idle')
    setLogs([])
    setSpec(null)
    setCode('')
    setAgents({})
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
              <h1 className="text-lg font-bold text-white leading-tight">PS AI Agent v2.0</h1>
              <p className="text-[11px] text-gray-500">Параллельные агенты • База знаний • Plant Simulation 2404</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <StatusDot label="Backend" online={backendOnline} />
            <StatusDot label="Plant Sim" online={psOnline} />
            {psMethod && (
              <div className="px-2 py-1 rounded-md bg-gray-800 text-[11px] text-gray-400">
                {psMethod}
              </div>
            )}
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

              <label className="flex items-center gap-2 text-xs text-gray-400 mt-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={parallelResearch}
                  onChange={e => setParallelResearch(e.target.checked)}
                  className="rounded bg-gray-800 border-gray-600"
                />
                Параллельное исследование API
              </label>

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
                  onClick={() => runResearch('full')}
                  disabled={appState !== 'idle' && appState !== 'done' && appState !== 'error'}
                  className="flex-1 py-2 rounded-lg bg-purple-600/20 border border-purple-600/40 hover:bg-purple-600/30 disabled:bg-gray-800 disabled:border-gray-700 disabled:text-gray-600 text-purple-300 text-sm transition-colors"
                >
                  🔬 Исследовать
                </button>
                <button
                  onClick={runSelfTest}
                  disabled={appState !== 'idle' && appState !== 'done' && appState !== 'error'}
                  className="flex-1 py-2 rounded-lg bg-amber-600/20 border border-amber-600/40 hover:bg-amber-600/30 disabled:bg-gray-800 disabled:border-gray-700 disabled:text-gray-600 text-amber-300 text-sm transition-colors"
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

            {/* Agent Status */}
            <div className="rounded-xl bg-gray-900 border border-gray-800 p-4">
              <h3 className="text-sm font-medium text-gray-300 mb-3">Параллельные агенты</h3>
              <div className="space-y-2">
                {Object.entries(agents).length === 0 ? (
                  <div className="text-xs text-gray-600 text-center py-4">Агенты не активны</div>
                ) : (
                  Object.entries(agents).map(([name, status]) => (
                    <div key={name} className="flex items-center gap-3 p-2 rounded-lg bg-gray-800/50">
                      <AgentIcon name={name} />
                      <div className="flex-1">
                        <div className="text-xs font-medium text-gray-200">{name}</div>
                      </div>
                      <AgentBadge status={status as any} />
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Quick Examples */}
            <div className="rounded-xl bg-gray-900 border border-gray-800 p-4">
              <h3 className="text-sm font-medium text-gray-300 mb-3">Примеры</h3>
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
          </div>

          {/* ─── Right: Main Content ─── */}
          <div className="lg:col-span-2 space-y-4">
            {/* Tabs */}
            <div className="flex gap-1 bg-gray-900 rounded-xl p-1 border border-gray-800 overflow-x-auto">
              {([
                ['control', '📡 Управление'],
                ['agents', '🤖 Агенты'],
                ['spec', '📄 Спецификация'],
                ['code', '💻 SimTalk'],
                ['model', '🏗️ Модель'],
                ['knowledge', '🧠 База знаний'],
                ['logs', '📋 Логи'],
              ] as const).map(([id, label]) => (
                <button
                  key={id}
                  onClick={() => setActiveTab(id)}
                  className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
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
                {activeTab === 'agents' && <AgentsView agents={agents} />}
                {activeTab === 'spec' && <SpecView spec={spec} />}
                {activeTab === 'code' && <CodeView code={code} />}
                {activeTab === 'model' && <ModelView spec={spec} />}
                {activeTab === 'knowledge' && <KnowledgeView />}
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

function AgentIcon({ name }: { name: string }) {
  const icons: Record<string, string> = {
    Architect: '🏗️',
    Builder: '🔨',
    Executor: '⚡',
    Debugger: '🐛',
    Researcher: '🔬',
    Validator: '✅',
    Supervisor: '👑',
  }
  return <span className="text-lg">{icons[name] || '🤖'}</span>
}

function AgentBadge({ status }: { status: string }) {
  const config: Record<string, { color: string; label: string }> = {
    idle: { color: 'bg-gray-600', label: 'Ожидание' },
    working: { color: 'bg-blue-500 animate-pulse', label: 'Работа' },
    done: { color: 'bg-green-500', label: 'Готово' },
    error: { color: 'bg-red-500', label: 'Ошибка' },
    waiting: { color: 'bg-yellow-500', label: 'Ожидание' },
  }
  const c = config[status] || config.idle
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
    initializing: { icon: '🚀', label: 'Инициализация системы...', color: 'text-blue-400' },
    connecting: { icon: '🔌', label: 'Подключение к Plant Simulation...', color: 'text-blue-400' },
    parsing: { icon: '🧠', label: 'Архитектор анализирует описание...', color: 'text-purple-400' },
    building: { icon: '🔧', label: 'Строитель генерирует SimTalk...', color: 'text-cyan-400' },
    executing: { icon: '⚡', label: 'Исполнитель создаёт модель...', color: 'text-green-400' },
    researching: { icon: '🔬', label: 'Исследователь изучает API...', color: 'text-amber-400' },
    testing: { icon: '🔧', label: 'Самотестирование...', color: 'text-amber-400' },
    done: { icon: '✅', label: 'Модель создана и сохранена!', color: 'text-green-400' },
    error: { icon: '❌', label: 'Ошибка — смотрите логи', color: 'text-red-400' },
  }
  const info = stateInfo[appState]

  return (
    <div className="space-y-4">
      <div className="rounded-xl bg-gray-900 border border-gray-800 p-6 text-center">
        <div className="text-4xl mb-2">{info.icon}</div>
        <div className={`text-lg font-semibold ${info.color}`}>{info.label}</div>
      </div>

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
    Supervisor: 'bg-indigo-700',
    Architect: 'bg-purple-700',
    Builder: 'bg-cyan-700',
    Executor: 'bg-blue-700',
    Debugger: 'bg-amber-700',
    Researcher: 'bg-pink-700',
    Validator: 'bg-green-700',
    TEST: 'bg-teal-700',
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

function AgentsView({ agents }: { agents: Record<string, string> }) {
  const agentDescriptions: Record<string, { desc: string; tasks: string[] }> = {
    Supervisor: {
      desc: 'Координирует работу всех агентов, распределяет задачи',
      tasks: ['Управление конвейером', 'Распределение задач', 'Мониторинг статусов'],
    },
    Architect: {
      desc: 'Парсит текстовое описание в JSON-спецификацию',
      tasks: ['LLM парсинг', 'Fallback regex', 'Валидация спецификации'],
    },
    Builder: {
      desc: 'Генерирует SimTalk код из JSON-спецификации',
      tasks: ['Генерация createObject', 'Генерация Connector.connect', 'Установка параметров'],
    },
    Executor: {
      desc: 'Выполняет код через COM/REST/Files',
      tasks: ['Выполнение SimTalk', 'Обработка ошибок', 'Повторные попытки'],
    },
    Debugger: {
      desc: 'Анализирует ошибки и ищет решения',
      tasks: ['Анализ ошибок', 'Поиск в базе знаний', 'Генерация исправлений'],
    },
    Researcher: {
      desc: 'Исследует API, тестирует методы',
      tasks: ['Тестирование методов', 'Интроспекция', 'Накопление знаний'],
    },
    Validator: {
      desc: 'Проверяет корректность созданной модели',
      tasks: ['Подсчёт объектов', 'Проверка соединений', 'Валидация параметров'],
    },
  }

  return (
    <div className="space-y-4">
      <div className="rounded-xl bg-gray-900 border border-gray-800 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Архитектура параллельных агентов</h3>
        <div className="bg-gray-950 rounded-lg p-4 text-sm text-gray-300">
          <p className="mb-2">Система использует <strong>7 специализированных агентов</strong>, работающих параллельно:</p>
          <ul className="space-y-1 list-disc list-inside text-xs text-gray-400">
            <li>Каждый агент имеет свою зону ответственности</li>
            <li>Агенты работают асинхронно через asyncio</li>
            <li>База знаний накапливает опыт и решения</li>
            <li>При ошибках автоматически запускается отладка</li>
          </ul>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(agentDescriptions).map(([name, info]) => (
          <div key={name} className="rounded-xl bg-gray-900 border border-gray-800 p-4">
            <div className="flex items-center gap-3 mb-3">
              <AgentIcon name={name} />
              <div>
                <h4 className="font-semibold text-white">{name}</h4>
                <AgentBadge status={agents[name] || 'idle'} />
              </div>
            </div>
            <p className="text-xs text-gray-400 mb-3">{info.desc}</p>
            <div className="space-y-1">
              {info.tasks.map((task, i) => (
                <div key={i} className="text-xs text-gray-500 flex items-center gap-2">
                  <span className="w-1 h-1 rounded-full bg-gray-600"></span>
                  {task}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function SpecView({ spec }: { spec: Spec | null }) {
  if (!spec) {
    return (
      <div className="rounded-xl bg-gray-900 border border-gray-800 p-12 text-center">
        <div className="text-4xl mb-3">📄</div>
        <div className="text-gray-400">JSON-спецификация пока пуста</div>
      </div>
    )
  }

  return (
    <div className="rounded-xl bg-gray-900 border border-gray-800 overflow-hidden">
      <div className="px-4 py-2 border-b border-gray-800 flex items-center justify-between">
        <span className="text-sm text-gray-400">JSON-спецификация</span>
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
      </div>
    )
  }

  return (
    <div className="rounded-xl bg-gray-900 border border-gray-800 p-6">
      <h3 className="text-sm font-medium text-gray-300 mb-4">Схема модели</h3>
      
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
                <div className="text-[10px] text-gray-500 mt-1">({obj.x}, {obj.y})</div>
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
    </div>
  )
}

function KnowledgeView() {
  const [methods, setMethods] = useState<KnowledgeMethod[]>([])
  const [classes, setClasses] = useState<KnowledgeClass[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const [mRes, cRes] = await Promise.all([
          fetch(`${API_BASE}/knowledge/methods`),
          fetch(`${API_BASE}/knowledge/classes`),
        ])
        setMethods(await mRes.json())
        setClasses(await cRes.json())
      } catch (err) {
        console.error('Ошибка загрузки базы знаний:', err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) {
    return (
      <div className="rounded-xl bg-gray-900 border border-gray-800 p-12 text-center">
        <div className="text-4xl mb-3 animate-pulse">🧠</div>
        <div className="text-gray-400">Загрузка базы знаний...</div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="rounded-xl bg-gray-900 border border-gray-800 p-6">
        <h3 className="text-lg font-semibold text-white mb-2">🧠 База знаний</h3>
        <p className="text-sm text-gray-400">
          Система накапливает опыт работы с Plant Simulation API. 
          При ошибках автоматически ищет решения в базе.
        </p>
      </div>

      {/* Methods */}
      <div className="rounded-xl bg-gray-900 border border-gray-800 overflow-hidden">
        <div className="px-4 py-2 border-b border-gray-800">
          <span className="text-sm text-gray-400">Методы API ({methods.length})</span>
        </div>
        <div className="divide-y divide-gray-800 max-h-[300px] overflow-y-auto">
          {methods.map((method, i) => (
            <div key={i} className="p-3 hover:bg-gray-800/30">
              <div className="flex items-center gap-2 mb-1">
                <span className={method.success_rate > 0.8 ? 'text-green-400' : method.success_rate > 0.5 ? 'text-yellow-400' : 'text-red-400'}>
                  {method.success_rate > 0.8 ? '✅' : method.success_rate > 0.5 ? '⚠️' : '❌'}
                </span>
                <span className="text-sm text-white font-medium">{method.name}</span>
                <span className="text-xs text-gray-500 ml-auto">
                  {Math.round(method.success_rate * 100)}% ({method.successes}/{method.attempts})
                </span>
              </div>
              <code className="text-[11px] text-cyan-300 font-mono block truncate">{method.template}</code>
              {method.notes && <div className="text-[11px] text-gray-500 mt-1">{method.notes}</div>}
            </div>
          ))}
        </div>
      </div>

      {/* Classes */}
      <div className="rounded-xl bg-gray-900 border border-gray-800 overflow-hidden">
        <div className="px-4 py-2 border-b border-gray-800">
          <span className="text-sm text-gray-400">Классы объектов ({classes.length})</span>
        </div>
        <div className="divide-y divide-gray-800 max-h-[300px] overflow-y-auto">
          {classes.map((cls, i) => (
            <div key={i} className="p-3 hover:bg-gray-800/30">
              <div className="flex items-center gap-2 mb-1">
                <span className={cls.verified ? 'text-green-400' : 'text-yellow-400'}>
                  {cls.verified ? '✅' : '⚠️'}
                </span>
                <span className="text-sm text-white font-medium">{cls.name}</span>
              </div>
              <code className="text-[11px] text-cyan-300 font-mono block truncate">{cls.create_method}</code>
              {cls.notes && <div className="text-[11px] text-gray-500 mt-1">{cls.notes}</div>}
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
