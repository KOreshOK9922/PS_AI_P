import { useState, useEffect, useRef } from 'react'

interface LogEntry {
  timestamp: string
  agent: string
  message: string
  level: string
}

interface Task {
  task_id: string
  status: string
  phase: string
  agents: Record<string, string>
  artifacts: Record<string, any>
  created_at: string
}

const API_BASE = 'http://localhost:8000'

export default function App() {
  const [requirement, setRequirement] = useState('')
  const [taskId, setTaskId] = useState<string | null>(null)
  const [taskStatus, setTaskStatus] = useState<Task | null>(null)
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [activeTab, setActiveTab] = useState<'control' | 'logs' | 'artifacts'>('control')
  const [backendOnline, setBackendOnline] = useState(false)
  const [ollamaOnline, setOllamaOnline] = useState(false)
  const logEndRef = useRef<HTMLDivElement>(null)
  const logIdRef = useRef(0)

  // Health check
  useEffect(() => {
    const check = async () => {
      try {
        const r = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(2000) })
        const d = await r.json()
        setBackendOnline(true)
        setOllamaOnline(d.ollama ?? false)
      } catch {
        setBackendOnline(false)
        setOllamaOnline(false)
      }
    }
    check()
    const iv = setInterval(check, 5000)
    return () => clearInterval(iv)
  }, [])

  // Poll logs
  useEffect(() => {
    if (!taskId) return

    const poll = async () => {
      try {
        const [logsRes, statusRes] = await Promise.all([
          fetch(`${API_BASE}/api/logs/${taskId}?after=${logIdRef.current}`),
          fetch(`${API_BASE}/api/status/${taskId}`)
        ])
        
        const newLogs: LogEntry[] = await logsRes.json()
        const status: Task = await statusRes.json()
        
        if (newLogs.length > 0) {
          logIdRef.current += newLogs.length
          setLogs(prev => [...prev, ...newLogs])
        }
        
        setTaskStatus(status)
        
        if (status.status === 'completed' || status.status === 'failed' || status.status === 'error') {
          // Stop polling
        }
      } catch (err) {
        console.error('Polling error:', err)
      }
    }

    const iv = setInterval(poll, 1000)
    return () => clearInterval(iv)
  }, [taskId])

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  const startTask = async () => {
    if (!requirement.trim()) return

    try {
      const r = await fetch(`${API_BASE}/api/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          requirement,
          max_iterations: 3
        })
      })
      
      const data = await r.json()
      setTaskId(data.task_id)
      setLogs([])
      logIdRef.current = 0
    } catch (err) {
      console.error('Failed to start task:', err)
    }
  }

  const reset = () => {
    setTaskId(null)
    setTaskStatus(null)
    setLogs([])
    logIdRef.current = 0
  }

  const agentColors: Record<string, string> = {
    'Orchestrator': 'bg-indigo-600',
    'Product Analyst': 'bg-blue-600',
    'System Architect': 'bg-purple-600',
    'Lead Engineer': 'bg-green-600',
    'QA Engineer': 'bg-yellow-600',
    'Code Reviewer': 'bg-red-600',
    'DevOps Engineer': 'bg-pink-600'
  }

  const agentIcons: Record<string, string> = {
    'Orchestrator': '🎯',
    'Product Analyst': '📊',
    'System Architect': '🏛️',
    'Lead Engineer': '💻',
    'QA Engineer': '🧪',
    'Code Reviewer': '🔍',
    'DevOps Engineer': '🚀'
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-xl">
              🤖
            </div>
            <div>
              <h1 className="text-lg font-bold">Multi-Agent Code Generation</h1>
              <p className="text-xs text-gray-400">7 специализированных агентов • Локальная LLM</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <StatusDot label="Backend" online={backendOnline} />
            <StatusDot label="Ollama" online={ollamaOnline} />
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Panel */}
          <div className="lg:col-span-1 space-y-4">
            {/* Input */}
            <div className="rounded-xl bg-gray-900 border border-gray-800 p-4">
              <label className="text-sm font-medium text-gray-300 mb-2 block">
                Требование к системе
              </label>
              <textarea
                value={requirement}
                onChange={e => setRequirement(e.target.value)}
                placeholder="Опишите что нужно создать..."
                className="w-full h-40 bg-gray-950 border border-gray-700 rounded-lg p-3 text-sm text-gray-200 placeholder-gray-600 resize-none focus:outline-none focus:border-blue-600"
                disabled={taskId !== null && taskStatus?.status === 'running'}
              />
              
              <button
                onClick={startTask}
                disabled={!requirement.trim() || (taskId !== null && taskStatus?.status === 'running')}
                className="w-full mt-3 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 text-white font-medium text-sm transition-colors"
              >
                {taskStatus?.status === 'running' ? '⏳ Выполняется...' : '▶ Запустить'}
              </button>

              {taskId && (
                <button
                  onClick={reset}
                  className="w-full mt-2 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm transition-colors"
                >
                  ↺ Сброс
                </button>
              )}
            </div>

            {/* Agents Status */}
            <div className="rounded-xl bg-gray-900 border border-gray-800 p-4">
              <h3 className="text-sm font-medium text-gray-300 mb-3">Агенты</h3>
              <div className="space-y-2">
                {Object.entries(agentIcons).map(([agent, icon]) => (
                  <div key={agent} className="flex items-center gap-3 p-2 rounded-lg bg-gray-800/50">
                    <span className="text-lg">{icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-medium text-gray-200">{agent}</div>
                      <div className="text-[11px] text-gray-500">
                        {taskStatus?.agents?.[agent] || 'Ожидание'}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Examples */}
            <div className="rounded-xl bg-gray-900 border border-gray-800 p-4">
              <h3 className="text-sm font-medium text-gray-300 mb-3">Примеры</h3>
              <div className="space-y-2">
                {[
                  'Создай REST API для управления пользователями с регистрацией и авторизацией',
                  'Создай CLI утилиту для конвертации CSV в JSON',
                  'Создай React компонент для отображения графика с фильтрацией'
                ].map((ex, i) => (
                  <button
                    key={i}
                    onClick={() => setRequirement(ex)}
                    className="w-full text-left text-xs text-gray-400 hover:text-blue-300 p-2 rounded bg-gray-800/30 hover:bg-gray-800 transition-colors"
                  >
                    {ex}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Right Panel */}
          <div className="lg:col-span-2 space-y-4">
            {/* Tabs */}
            <div className="flex gap-1 bg-gray-900 rounded-xl p-1 border border-gray-800">
              {([
                ['control', '📡 Управление'],
                ['logs', '📋 Логи'],
                ['artifacts', '📦 Артефакты']
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
            {activeTab === 'control' && (
              <div className="space-y-4">
                {/* Status Banner */}
                <div className="rounded-xl bg-gray-900 border border-gray-800 p-6 text-center">
                  <div className="text-4xl mb-2">
                    {taskStatus?.status === 'running' ? '⚙️' : 
                     taskStatus?.status === 'completed' ? '✅' : 
                     taskStatus?.status === 'failed' ? '❌' : '💤'}
                  </div>
                  <div className={`text-lg font-semibold ${
                    taskStatus?.status === 'running' ? 'text-blue-400' :
                    taskStatus?.status === 'completed' ? 'text-green-400' :
                    taskStatus?.status === 'failed' ? 'text-red-400' : 'text-gray-400'
                  }`}>
                    {taskStatus?.status === 'running' ? `Фаза: ${taskStatus.phase}` :
                     taskStatus?.status === 'completed' ? 'Задача завершена' :
                     taskStatus?.status === 'failed' ? 'Задача не выполнена' :
                     'Ожидание запуска'}
                  </div>
                </div>

                {/* Recent Logs */}
                <div className="rounded-xl bg-gray-900 border border-gray-800 overflow-hidden">
                  <div className="px-4 py-2 border-b border-gray-800 flex items-center justify-between">
                    <span className="text-sm text-gray-400">Живой журнал</span>
                    <span className="text-xs text-gray-600">{logs.length} записей</span>
                  </div>
                  <div className="p-3 max-h-[400px] overflow-y-auto font-mono text-xs space-y-0.5">
                    {logs.length === 0 && (
                      <div className="text-gray-600 text-center py-8">
                        {taskId ? 'Ожидание логов...' : 'Нажмите "Запустить" для начала работы'}
                      </div>
                    )}
                    {logs.slice(-30).map((log, i) => (
                      <div key={i} className="flex items-start gap-2 py-0.5 hover:bg-gray-800/30 px-1 rounded">
                        <span className="text-gray-600 shrink-0">
                          {new Date(log.timestamp).toLocaleTimeString('ru-RU')}
                        </span>
                        <span className={`shrink-0 px-1 rounded text-[10px] text-white ${
                          agentColors[log.agent] || 'bg-gray-600'
                        }`}>
                          {log.agent}
                        </span>
                        <span className={
                          log.level === 'ERROR' ? 'text-red-300' :
                          log.level === 'WARN' ? 'text-yellow-300' : 'text-gray-300'
                        }>
                          {log.message}
                        </span>
                      </div>
                    ))}
                    <div ref={logEndRef} />
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'logs' && (
              <div className="rounded-xl bg-gray-900 border border-gray-800 overflow-hidden">
                <div className="px-4 py-2 border-b border-gray-800 flex items-center justify-between">
                  <span className="text-sm text-gray-400">Полный журнал</span>
                  <span className="text-xs text-gray-600">{logs.length} записей</span>
                </div>
                <div className="p-3 max-h-[600px] overflow-y-auto font-mono text-xs space-y-0.5">
                  {logs.length === 0 && (
                    <div className="text-gray-600 text-center py-8">Журнал пуст</div>
                  )}
                  {logs.map((log, i) => (
                    <div key={i} className="flex items-start gap-2 py-0.5 hover:bg-gray-800/30 px-1 rounded">
                      <span className="text-gray-600 shrink-0">
                        {new Date(log.timestamp).toLocaleTimeString('ru-RU')}
                      </span>
                      <span className={`shrink-0 px-1 rounded text-[10px] text-white ${
                        agentColors[log.agent] || 'bg-gray-600'
                      }`}>
                        {log.agent}
                      </span>
                      <span className={
                        log.level === 'ERROR' ? 'text-red-300' :
                        log.level === 'WARN' ? 'text-yellow-300' : 'text-gray-300'
                      }>
                        {log.message}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'artifacts' && (
              <div className="space-y-4">
                {!taskStatus?.artifacts || Object.keys(taskStatus.artifacts).length === 0 ? (
                  <div className="rounded-xl bg-gray-900 border border-gray-800 p-12 text-center">
                    <div className="text-4xl mb-3">📦</div>
                    <div className="text-gray-400">Артефакты пока не созданы</div>
                    <div className="text-xs text-gray-600 mt-1">
                      Запустите задачу для генерации кода
                    </div>
                  </div>
                ) : (
                  Object.entries(taskStatus.artifacts).map(([name, content]) => (
                    <div key={name} className="rounded-xl bg-gray-900 border border-gray-800 overflow-hidden">
                      <div className="px-4 py-2 border-b border-gray-800 flex items-center justify-between">
                        <span className="text-sm text-gray-400 font-mono">{name}</span>
                        <button
                          onClick={() => navigator.clipboard.writeText(typeof content === 'string' ? content : JSON.stringify(content, null, 2))}
                          className="text-xs text-gray-500 hover:text-white px-2 py-1 rounded hover:bg-gray-800"
                        >
                          📋 Копировать
                        </button>
                      </div>
                      <div className="p-4 max-h-[400px] overflow-y-auto">
                        <pre className="text-sm font-mono text-gray-300 whitespace-pre-wrap">
                          {typeof content === 'string' ? content : JSON.stringify(content, null, 2)}
                        </pre>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function StatusDot({ label, online }: { label: string; online: boolean }) {
  return (
    <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-gray-800">
      <div className={`w-2 h-2 rounded-full ${online ? 'bg-green-400' : 'bg-red-400'} ${online ? 'animate-pulse' : ''}`} />
      <span className="text-[11px] text-gray-400">{label}</span>
    </div>
  )
}
