import { useState } from 'react'
import Header from './components/Header'
import Architecture from './components/Architecture'
import StatusPanel from './components/StatusPanel'
import ApiFindings from './components/ApiFindings'
import Recommendations from './components/Recommendations'
import AgentLog from './components/AgentLog'
import CodeExplorer from './components/CodeExplorer'

type Tab = 'overview' | 'architecture' | 'status' | 'api' | 'recommendations' | 'log' | 'code'

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>('overview')

  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: 'overview', label: 'Обзор', icon: '📊' },
    { id: 'architecture', label: 'Архитектура', icon: '🏗️' },
    { id: 'status', label: 'Статус', icon: '📡' },
    { id: 'api', label: 'API факты', icon: '🔬' },
    { id: 'recommendations', label: 'Решения', icon: '💡' },
    { id: 'log', label: 'Журнал', icon: '📋' },
    { id: 'code', label: 'Код', icon: '💻' },
  ]

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <Header />
      
      {/* Navigation */}
      <nav className="sticky top-0 z-50 bg-gray-900/95 backdrop-blur border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex overflow-x-auto gap-1 py-2">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
                  activeTab === tab.id
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }`}
              >
                <span>{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {activeTab === 'overview' && <Overview />}
        {activeTab === 'architecture' && <Architecture />}
        {activeTab === 'status' && <StatusPanel />}
        {activeTab === 'api' && <ApiFindings />}
        {activeTab === 'recommendations' && <Recommendations />}
        {activeTab === 'log' && <AgentLog />}
        {activeTab === 'code' && <CodeExplorer />}
      </main>
    </div>
  )
}

function Overview() {
  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-blue-900/50 to-purple-900/50 border border-blue-800/30 p-8">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiMyMDIwMjAiIGZpbGwtb3BhY2l0eT0iMC4xIj48cGF0aCBkPSJNMzYgMzRoLTJ2LTRoMnY0em0wLTZ2LTRoLTJ2NGgyem0tNiA2aDJ2LTRoLTJ2NHptMC02aDJ2LTRoLTJ2NHoiLz48L2c+PC9nPjwvc3ZnPg==')] opacity-20"></div>
        <div className="relative">
          <h2 className="text-3xl font-bold text-white mb-3">
            AI-Агент для Siemens Plant Simulation 2404
          </h2>
          <p className="text-blue-200 text-lg mb-6 max-w-3xl">
            Автономная система ИИ-агентов для построения моделей производственных линий 
            по текстовому описанию. Использует локальную LLM (qwen2.5-coder:7b) и COM-интерфейс.
          </p>
          <div className="flex flex-wrap gap-3">
            <span className="px-3 py-1 rounded-full bg-blue-600/30 text-blue-300 text-sm border border-blue-600/30">
              🤖 Ollama + qwen2.5-coder:7b
            </span>
            <span className="px-3 py-1 rounded-full bg-green-600/30 text-green-300 text-sm border border-green-600/30">
              🏭 Plant Simulation 2404
            </span>
            <span className="px-3 py-1 rounded-full bg-purple-600/30 text-purple-300 text-sm border border-purple-600/30">
              🐍 Python 3.15 + COM
            </span>
            <span className="px-3 py-1 rounded-full bg-amber-600/30 text-amber-300 text-sm border border-amber-600/30">
              🌐 Web UI :7860
            </span>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard title="Рабочих API" value="6" total="20+" color="green" />
        <StatCard title="Попыток соединений" value="15" total="15" color="red" />
        <StatCard title="Агентов в системе" value="5" total="5" color="blue" />
        <StatCard title="Вариантов решения" value="4" total="4" color="purple" />
      </div>

      {/* Key Problem */}
      <div className="rounded-xl bg-red-950/30 border border-red-800/40 p-6">
        <h3 className="text-xl font-bold text-red-300 mb-3 flex items-center gap-2">
          <span className="text-2xl">⚠️</span> Ключевая проблема
        </h3>
        <p className="text-red-200 mb-4">
          Plant Simulation 2404 не позволяет программно создавать соединения между объектами 
          MaterialFlow через COM-интерфейс. Все 15 проверенных методов из учебников (2017, 2019) 
          не работают в версии 2404.
        </p>
        <div className="bg-gray-900 rounded-lg p-4 font-mono text-sm">
          <div className="text-red-400">// Все попытки возвращают ошибку:</div>
          <div className="text-yellow-300">"You cannot assign a value to the expression on the left hand side"</div>
          <div className="text-red-400 mt-2">// или:</div>
          <div className="text-yellow-300">"Unknown identifier 'connect'"</div>
        </div>
      </div>

      {/* Pipeline Flow */}
      <div className="rounded-xl bg-gray-900 border border-gray-800 p-6">
        <h3 className="text-xl font-bold text-white mb-6">Конвейер обработки</h3>
        <div className="flex flex-col md:flex-row items-center gap-4">
          <PipelineStep num={1} title="Ввод" desc="Текстовое описание линии" color="blue" />
          <Arrow />
          <PipelineStep num={2} title="Архитектор" desc="LLM → JSON-спецификация" color="purple" />
          <Arrow />
          <PipelineStep num={3} title="Строитель" desc="JSON → SimTalk код" color="cyan" />
          <Arrow />
          <PipelineStep num={4} title="Исполнитель" desc="COM → Plant Simulation" color="green" />
          <Arrow />
          <PipelineStep num={5} title="Результат" desc="Готовая модель .spp" color="amber" />
        </div>
      </div>
    </div>
  )
}

function StatCard({ title, value, total, color }: { title: string; value: string; total: string; color: string }) {
  const colors: Record<string, string> = {
    green: 'from-green-600/20 to-green-900/20 border-green-700/40 text-green-400',
    red: 'from-red-600/20 to-red-900/20 border-red-700/40 text-red-400',
    blue: 'from-blue-600/20 to-blue-900/20 border-blue-700/40 text-blue-400',
    purple: 'from-purple-600/20 to-purple-900/20 border-purple-700/40 text-purple-400',
  }
  
  return (
    <div className={`rounded-xl bg-gradient-to-br ${colors[color]} border p-5`}>
      <div className={`text-3xl font-bold ${colors[color].split(' ').pop()}`}>{value}<span className="text-lg text-gray-500">/{total}</span></div>
      <div className="text-sm text-gray-400 mt-1">{title}</div>
    </div>
  )
}

function PipelineStep({ num, title, desc, color }: { num: number; title: string; desc: string; color: string }) {
  const bgColors: Record<string, string> = {
    blue: 'bg-blue-600/20 border-blue-600/40',
    purple: 'bg-purple-600/20 border-purple-600/40',
    cyan: 'bg-cyan-600/20 border-cyan-600/40',
    green: 'bg-green-600/20 border-green-600/40',
    amber: 'bg-amber-600/20 border-amber-600/40',
  }
  
  return (
    <div className={`flex flex-col items-center p-4 rounded-xl border ${bgColors[color]} min-w-[140px]`}>
      <div className="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center text-sm font-bold text-white mb-2">
        {num}
      </div>
      <div className="font-semibold text-white text-sm">{title}</div>
      <div className="text-xs text-gray-400 text-center mt-1">{desc}</div>
    </div>
  )
}

function Arrow() {
  return (
    <div className="hidden md:block text-gray-600 text-2xl">→</div>
  )
}
