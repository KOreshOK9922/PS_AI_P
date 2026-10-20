export default function Architecture() {
  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-bold text-white">Архитектура системы</h2>
      
      {/* System Diagram */}
      <div className="rounded-xl bg-gray-900 border border-gray-800 p-8">
        <h3 className="text-lg font-semibold text-white mb-6">Компоненты и связи</h3>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Input */}
          <div className="space-y-4">
            <div className="text-center text-sm text-gray-500 uppercase tracking-wide mb-2">Ввод</div>
            <ComponentBox
              title="Веб-интерфейс"
              subtitle="localhost:7860"
              icon="🌐"
              color="blue"
              items={['Ввод описания линии', 'Просмотр журнала', 'Статус агентов']}
            />
            <ComponentBox
              title="Текстовый парсер"
              subtitle="Regex fallback"
              icon="📝"
              color="cyan"
              items={['Извлечение объектов', 'Параметры из текста', 'Последовательность']}
            />
          </div>
          
          {/* Middle Column - Processing */}
          <div className="space-y-4">
            <div className="text-center text-sm text-gray-500 uppercase tracking-wide mb-2">Обработка</div>
            <ComponentBox
              title="Ollama LLM"
              subtitle="qwen2.5-coder:7b"
              icon="🧠"
              color="purple"
              items={['Архитектор: текст → JSON', 'Отладчик: ошибка → фикс', 'Локально, без облака']}
            />
            <ComponentBox
              title="Строитель"
              subtitle="Детерминированный"
              icon="🔧"
              color="green"
              items={['JSON → SimTalk', 'Генерация кода', 'Валидация синтаксиса']}
            />
          </div>
          
          {/* Right Column - Output */}
          <div className="space-y-4">
            <div className="text-center text-sm text-gray-500 uppercase tracking-wide mb-2">Вывод</div>
            <ComponentBox
              title="COM-интерфейс"
              subtitle="win32com.client"
              icon="🔌"
              color="amber"
              items={['ExecuteSimTalk()', 'GetValue()', 'SaveModel()']}
            />
            <ComponentBox
              title="Plant Simulation"
              subtitle="2404"
              icon="🏭"
              color="red"
              items={['MaterialFlow объекты', 'EventController', 'Модель .spp']}
            />
          </div>
        </div>
      </div>

      {/* Agent Roles */}
      <div className="rounded-xl bg-gray-900 border border-gray-800 p-6">
        <h3 className="text-lg font-semibold text-white mb-6">Роли агентов</h3>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <AgentRole
            name="Архитектор"
            type="LLM"
            status="working"
            desc="Парсит текст в JSON-спецификацию модели"
            icon="🏗️"
          />
          <AgentRole
            name="Строитель"
            type="Детерминированный"
            status="working"
            desc="Генерирует SimTalk код из спецификации"
            icon="🔨"
          />
          <AgentRole
            name="Исполнитель"
            type="COM"
            status="partial"
            desc="Выполняет код в Plant Simulation"
            icon="⚡"
          />
          <AgentRole
            name="Отладчик"
            type="LLM"
            status="working"
            desc="Анализирует ошибки и предлагает исправления"
            icon="🐛"
          />
          <AgentRole
            name="Валидатор"
            type="Детерминированный"
            status="working"
            desc="Сохраняет и проверяет готовую модель"
            icon="✅"
          />
        </div>
      </div>

      {/* Data Flow */}
      <div className="rounded-xl bg-gray-900 border border-gray-800 p-6">
        <h3 className="text-lg font-semibold text-white mb-6">Поток данных</h3>
        <div className="space-y-3">
          <DataFlowStep
            step={1}
            from="Пользователь"
            to="Веб-интерфейс"
            data='Текст: "Источник 3 мин, станция 20 сек, буфер 10, сход"'
            color="blue"
          />
          <DataFlowStep
            step={2}
            from="Веб-интерфейс"
            to="Архитектор (LLM)"
            data='JSON: {"objects": [...], "connections": [...]}'
            color="purple"
          />
          <DataFlowStep
            step={3}
            from="Архитектор"
            to="Строитель"
            data='SimTalk: "var pa:object; pa:=.MaterialFlow.Source.derive(root)"'
            color="green"
          />
          <DataFlowStep
            step={4}
            from="Строитель"
            to="Исполнитель (COM)"
            data='app.ExecuteSimTalk(code)'
            color="amber"
          />
          <DataFlowStep
            step={5}
            from="Исполнитель"
            to="Plant Simulation"
            data='Создание объектов, установка параметров, сохранение .spp'
            color="red"
          />
        </div>
      </div>
    </div>
  )
}

function ComponentBox({ title, subtitle, icon, color, items }: {
  title: string; subtitle: string; icon: string; color: string; items: string[]
}) {
  const borderColors: Record<string, string> = {
    blue: 'border-blue-700/40',
    cyan: 'border-cyan-700/40',
    purple: 'border-purple-700/40',
    green: 'border-green-700/40',
    amber: 'border-amber-700/40',
    red: 'border-red-700/40',
  }
  const bgColors: Record<string, string> = {
    blue: 'bg-blue-950/30',
    cyan: 'bg-cyan-950/30',
    purple: 'bg-purple-950/30',
    green: 'bg-green-950/30',
    amber: 'bg-amber-950/30',
    red: 'bg-red-950/30',
  }
  
  return (
    <div className={`rounded-xl border ${borderColors[color]} ${bgColors[color]} p-4`}>
      <div className="flex items-center gap-3 mb-3">
        <span className="text-2xl">{icon}</span>
        <div>
          <div className="font-semibold text-white text-sm">{title}</div>
          <div className="text-xs text-gray-400">{subtitle}</div>
        </div>
      </div>
      <ul className="space-y-1">
        {items.map((item, i) => (
          <li key={i} className="text-xs text-gray-300 flex items-center gap-2">
            <span className="w-1 h-1 rounded-full bg-gray-500"></span>
            {item}
          </li>
        ))}
      </ul>
    </div>
  )
}

function AgentRole({ name, type, status, desc, icon }: {
  name: string; type: string; status: 'working' | 'partial' | 'broken'; desc: string; icon: string
}) {
  const statusColors = {
    working: 'bg-green-500',
    partial: 'bg-yellow-500',
    broken: 'bg-red-500',
  }
  const statusLabels = {
    working: 'Работает',
    partial: 'Частично',
    broken: 'Сломан',
  }
  
  return (
    <div className="rounded-lg bg-gray-800 border border-gray-700 p-4 text-center">
      <div className="text-3xl mb-2">{icon}</div>
      <div className="font-semibold text-white text-sm">{name}</div>
      <div className="text-xs text-gray-400 mb-2">{type}</div>
      <div className="flex items-center justify-center gap-1 mb-2">
        <div className={`w-2 h-2 rounded-full ${statusColors[status]}`}></div>
        <span className="text-xs text-gray-300">{statusLabels[status]}</span>
      </div>
      <p className="text-xs text-gray-400">{desc}</p>
    </div>
  )
}

function DataFlowStep({ step, from, to, data, color }: {
  step: number; from: string; to: string; data: string; color: string
}) {
  const bgColors: Record<string, string> = {
    blue: 'bg-blue-600/20',
    purple: 'bg-purple-600/20',
    green: 'bg-green-600/20',
    amber: 'bg-amber-600/20',
    red: 'bg-red-600/20',
  }
  
  return (
    <div className={`flex items-center gap-4 rounded-lg ${bgColors[color]} border border-gray-800 p-3`}>
      <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-sm font-bold text-white shrink-0">
        {step}
      </div>
      <div className="flex items-center gap-2 text-sm">
        <span className="text-gray-300 font-medium">{from}</span>
        <span className="text-gray-600">→</span>
        <span className="text-gray-300 font-medium">{to}</span>
      </div>
      <div className="ml-auto text-xs text-gray-400 font-mono hidden md:block max-w-md truncate">
        {data}
      </div>
    </div>
  )
}
