export default function Header() {
  return (
    <header className="bg-gray-900 border-b border-gray-800">
      <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-xl">
            🏭
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">PS AI Agent</h1>
            <p className="text-xs text-gray-400">Plant Simulation 2404 • Автономный ИИ-строитель моделей</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-yellow-900/30 border border-yellow-700/40">
            <div className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse"></div>
            <span className="text-xs text-yellow-300">Частично работоспособен</span>
          </div>
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-800 border border-gray-700">
            <span className="text-xs text-gray-400">v2.0-beta</span>
          </div>
        </div>
      </div>
    </header>
  )
}
