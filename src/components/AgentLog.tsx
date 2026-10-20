import { useState } from 'react'

export default function AgentLog() {
  const [selectedLog, setSelectedLog] = useState(0)
  
  const logs = [
    {
      id: 'agent_log_v1',
      name: 'plant_swarm_v1.py',
      time: '2024-12-15 14:23',
      status: 'partial',
      entries: [
        { time: '14:23:01', level: 'INFO', agent: 'SYSTEM', msg: 'Запуск системы PS AI Agent v1' },
        { time: '14:23:02', level: 'INFO', agent: 'SYSTEM', msg: 'Подключение к Ollama: http://localhost:11434' },
        { time: '14:23:03', level: 'INFO', agent: 'SYSTEM', msg: 'Ollama доступна, модель: qwen2.5-coder:7b' },
        { time: '14:23:04', level: 'INFO', agent: 'SYSTEM', msg: 'COM: Tecnomatix.PlantSimulation.RemoteControl' },
        { time: '14:23:05', level: 'INFO', agent: 'EXECUTOR', msg: 'app.NewModel() — OK' },
        { time: '14:23:06', level: 'INFO', agent: 'EXECUTOR', msg: 'app.SetNoMessageBox(True) — OK' },
        { time: '14:23:10', level: 'INFO', agent: 'ARCHITECT', msg: 'Получено описание: "Линия: источник 3 мин, станция 20 сек, буфер 10, сход"' },
        { time: '14:23:15', level: 'INFO', agent: 'ARCHITECT', msg: 'LLM вернула JSON-спецификацию' },
        { time: '14:23:16', level: 'INFO', agent: 'BUILDER', msg: 'Генерация SimTalk кода...' },
        { time: '14:23:17', level: 'INFO', agent: 'EXECUTOR', msg: '.MaterialFlow.Source.derive(root) — OK' },
        { time: '14:23:18', level: 'INFO', agent: 'EXECUTOR', msg: 'pa.setName("SRC_1") — OK' },
        { time: '14:23:19', level: 'INFO', agent: 'EXECUTOR', msg: '.MaterialFlow.Station.derive(root) — OK' },
        { time: '14:23:20', level: 'INFO', agent: 'EXECUTOR', msg: 'pb.setName("ST_1") — OK' },
        { time: '14:23:21', level: 'INFO', agent: 'EXECUTOR', msg: '.MaterialFlow.Buffer.derive(root) — OK' },
        { time: '14:23:22', level: 'INFO', agent: 'EXECUTOR', msg: 'pc.setName("BUF_1") — OK' },
        { time: '14:23:23', level: 'INFO', agent: 'EXECUTOR', msg: '.MaterialFlow.Drain.derive(root) — OK' },
        { time: '14:23:24', level: 'INFO', agent: 'EXECUTOR', msg: 'pd.setName("DRN_1") — OK' },
        { time: '14:23:25', level: 'INFO', agent: 'EXECUTOR', msg: 'root.SRC_1.interval := 180 — OK' },
        { time: '14:23:26', level: 'INFO', agent: 'EXECUTOR', msg: 'root.ST_1.procTime := 20 — OK' },
        { time: '14:23:27', level: 'INFO', agent: 'EXECUTOR', msg: 'root.BUF_1.capacity := 10 — OK' },
        { time: '14:23:30', level: 'INFO', agent: 'EXECUTOR', msg: 'Попытка соединения: root.SRC_1.succ := root.ST_1' },
        { time: '14:23:31', level: 'ERROR', agent: 'EXECUTOR', msg: 'ОШИБКА: cannot assign to left hand side' },
        { time: '14:23:32', level: 'INFO', agent: 'DEBUGGER', msg: 'Анализ ошибки... Попытка 2: Connector.derive' },
        { time: '14:23:33', level: 'ERROR', agent: 'EXECUTOR', msg: 'ОШИБКА: Wrong number of parameters' },
        { time: '14:23:34', level: 'INFO', agent: 'DEBUGGER', msg: 'Попытка 3: connect() метод' },
        { time: '14:23:35', level: 'ERROR', agent: 'EXECUTOR', msg: 'ОШИБКА: Unknown identifier connect' },
        { time: '14:23:36', level: 'WARN', agent: 'DEBUGGER', msg: 'Все методы соединений не работают. Завершение.' },
      ]
    },
    {
      id: 'agent_log_v2',
      name: 'plant_swarm_v2.py',
      time: '2024-12-16 10:05',
      status: 'partial',
      entries: [
        { time: '10:05:01', level: 'INFO', agent: 'SYSTEM', msg: 'Запуск PS AI Agent v2 (с fallback-парсером)' },
        { time: '10:05:02', level: 'INFO', agent: 'SYSTEM', msg: 'Ollama недоступна — активирован fallback regex-парсер' },
        { time: '10:05:03', level: 'INFO', agent: 'PARSER', msg: 'Найдено: источник (SRC_1), станция (ST_1), накопитель (BUF_1), сход (DRN_1)' },
        { time: '10:05:04', level: 'INFO', agent: 'PARSER', msg: 'Параметры: interval=3min→180s, procTime=20s, capacity=10' },
        { time: '10:05:05', level: 'INFO', agent: 'PARSER', msg: 'Соединения: SRC_1→ST_1→BUF_1→DRN_1' },
        { time: '10:05:10', level: 'INFO', agent: 'EXECUTOR', msg: 'Все 4 объекта созданы успешно' },
        { time: '10:05:15', level: 'INFO', agent: 'EXECUTOR', msg: 'Параметры установлены' },
        { time: '10:05:20', level: 'ERROR', agent: 'EXECUTOR', msg: 'Соединения: 15 попыток, все неудачны' },
        { time: '10:05:25', level: 'WARN', agent: 'SYSTEM', msg: 'Модель создана без соединений. Сохранение невозможно.' },
      ]
    },
    {
      id: 'api_introspection',
      name: 'ps_api_introspection.py',
      time: '2024-12-17 16:42',
      status: 'failed',
      entries: [
        { time: '16:42:01', level: 'INFO', agent: 'SYSTEM', msg: 'Запуск интроспекции API' },
        { time: '16:42:02', level: 'INFO', agent: 'SYSTEM', msg: 'Попытка создания тестовых объектов...' },
        { time: '16:42:03', level: 'ERROR', agent: 'SYSTEM', msg: 'Ошибка создания PA/PB — скрипт упал' },
        { time: '16:42:04', level: 'WARN', agent: 'SYSTEM', msg: 'Интроспекция не завершена. Требуется исправление.' },
      ]
    },
  ]

  const levelColors: Record<string, string> = {
    INFO: 'text-blue-400',
    WARN: 'text-yellow-400',
    ERROR: 'text-red-400',
    DEBUG: 'text-gray-400',
  }

  const agentColors: Record<string, string> = {
    SYSTEM: 'bg-gray-700',
    ARCHITECT: 'bg-purple-700',
    BUILDER: 'bg-green-700',
    EXECUTOR: 'bg-blue-700',
    DEBUGGER: 'bg-amber-700',
    PARSER: 'bg-cyan-700',
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-white">Журнал агентов</h2>
      
      {/* Log Selector */}
      <div className="flex gap-3 overflow-x-auto pb-2">
        {logs.map((log, i) => (
          <button
            key={log.id}
            onClick={() => setSelectedLog(i)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm whitespace-nowrap transition-all ${
              selectedLog === i
                ? 'bg-blue-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:text-white'
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${
              log.status === 'partial' ? 'bg-yellow-400' : log.status === 'failed' ? 'bg-red-400' : 'bg-green-400'
            }`}></span>
            {log.name}
            <span className="text-xs opacity-60">{log.time}</span>
          </button>
        ))}
      </div>

      {/* Log Content */}
      <div className="rounded-xl bg-gray-950 border border-gray-800 overflow-hidden">
        <div className="bg-gray-900 px-4 py-2 border-b border-gray-800 flex items-center justify-between">
          <span className="text-sm text-gray-400 font-mono">{logs[selectedLog].name}</span>
          <span className="text-xs text-gray-500">{logs[selectedLog].time}</span>
        </div>
        <div className="p-4 max-h-[600px] overflow-y-auto font-mono text-xs space-y-0.5">
          {logs[selectedLog].entries.map((entry, i) => (
            <div key={i} className="flex items-start gap-3 py-0.5 hover:bg-gray-900/50 px-2 rounded">
              <span className="text-gray-600 shrink-0">{entry.time}</span>
              <span className={`shrink-0 w-12 ${levelColors[entry.level]}`}>{entry.level}</span>
              <span className={`shrink-0 px-1.5 py-0.5 rounded text-[10px] text-white ${agentColors[entry.agent] || 'bg-gray-600'}`}>
                {entry.agent}
              </span>
              <span className={`${entry.level === 'ERROR' ? 'text-red-300' : entry.level === 'WARN' ? 'text-yellow-300' : 'text-gray-300'}`}>
                {entry.msg}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
