import { useState } from 'react'

export default function ApiFindings() {
  const [filter, setFilter] = useState<'all' | 'working' | 'broken'>('all')
  
  const findings = [
    {
      id: 1,
      category: 'Создание объектов',
      status: 'working' as const,
      title: 'derive() — правильный метод создания',
      description: 'В PS 2404 используется derive() вместо create() из учебников',
      code: `var pa : object
pa := .MaterialFlow.Source.derive(root)
pa.setName("SRC_1")`,
      source: 'Подтверждено экспериментально',
    },
    {
      id: 2,
      category: 'Имена классов',
      status: 'working' as const,
      title: 'Station вместо SingleProc',
      description: 'В PS 2404 класс однопозиционной станции называется Station',
      code: `var pb : object
pb := .MaterialFlow.Station.derive(root)
pb.setName("ST_1")`,
      source: 'Подтверждено экспериментально',
    },
    {
      id: 3,
      category: 'Переименование',
      status: 'working' as const,
      title: 'setName() — единственный способ',
      description: 'Атрибут .name только для чтения, использовать setName()',
      code: `pa.setName("SRC_1")
// НЕ РАБОТАЕТ: pa.name := "SRC_1"`,
      source: 'Подтверждено экспериментально',
    },
    {
      id: 4,
      category: 'Параметры',
      status: 'working' as const,
      title: 'Установка параметров через :=',
      description: 'interval, procTime, capacity работают через присваивание',
      code: `root.SRC_1.interval := 120
root.ST_1.procTime := 15
root.BUF_1.capacity := 5`,
      source: 'Подтверждено экспериментально',
    },
    {
      id: 5,
      category: 'Соединения',
      status: 'broken' as const,
      title: 'succ — только для чтения',
      description: 'Атрибут succ нельзя присвоить — read-only в PS 2404',
      code: `root.SRC_1.succ := root.ST_1
// Ошибка: cannot assign to left hand side`,
      source: '15 попыток, все неудачны',
    },
    {
      id: 6,
      category: 'Соединения',
      status: 'broken' as const,
      title: 'Connector.derive — неправильная сигнатура',
      description: 'derive принимает максимум 3 аргумента, не может создать соединение',
      code: `.MaterialFlow.Connector.derive(root, "C1", src, dst)
// Ошибка: Wrong number of parameters: 4 passed, at most 3`,
      source: 'Подтверждено экспериментально',
    },
    {
      id: 7,
      category: 'Соединения',
      status: 'broken' as const,
      title: 'Нет метода connect()',
      description: 'Методы connect, connectTo, addSucc, setSucc не существуют',
      code: `root.SRC_1.connect(root.ST_1)
// Ошибка: Unknown identifier 'connect'`,
      source: 'Проверено 6 вариантов методов',
    },
    {
      id: 8,
      category: 'Строки',
      status: 'working' as const,
      title: 'Только двойные кавычки',
      description: 'SimTalk в PS 2404 принимает только двойные кавычки для строк',
      code: `pa.setName("SRC_1")  // ✅ Работает
pa.setName('SRC_1')  // ❌ Syntax error`,
      source: 'Подтверждено экспериментально',
    },
    {
      id: 9,
      category: 'GetValue',
      status: 'working' as const,
      title: 'GetValue принимает 1-2 аргумента',
      description: 'Нельзя передавать 3 аргумента. Для чтения использовать ExecuteSimTalk',
      code: `// НЕ работает:
app.GetValue("root.PA", "interval")  // 3 args error

// Работает:
app.ExecuteSimTalk('var t : object; t := root.SRC_1;')`,
      source: 'Подтверждено экспериментально',
    },
    {
      id: 10,
      category: 'Координаты',
      status: 'broken' as const,
      title: 'Невозможно прочитать координаты',
      description: 'xPos, yPos, posX, posY, x, y, iconX, iconY — все вызывают ошибки',
      code: `app.GetValue("root.PA", "xPos")
app.GetValue("root.PA", "yPos")
// Все: takes from 1 to 2 positional arguments but 3 were given`,
      source: 'Проверено 8 вариантов атрибутов',
    },
    {
      id: 11,
      category: 'Авто-соединение',
      status: 'broken' as const,
      title: 'Размещение вплотную не создаёт Connector',
      description: 'Из документации: объекты рядом должны авто-соединяться. В PS 2404 через COM — нет.',
      code: `pa.xPos := 100; pa.yPos := 200
pb.xPos := 200; pb.yPos := 200
// Объекты рядом, но соединения нет`,
      source: 'Из документации Twente, не подтверждено',
    },
    {
      id: 12,
      category: 'Python Module',
      status: 'broken' as const,
      title: 'Встроенный Python недоступен через COM',
      description: 'PythonModule.execute, sourceCode, pythonCode — все неизвестные идентификаторы',
      code: `root.PYTHON_MODULE.execute
root.PYTHON_MODULE.sourceCode := "print(1)"
// Ошибка: Unknown identifier`,
      source: 'Подтверждено экспериментально',
    },
  ]

  const filtered = filter === 'all' ? findings : findings.filter(f => f.status === filter)

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Подтверждённые факты API</h2>
        <div className="flex gap-2">
          <FilterBtn active={filter === 'all'} onClick={() => setFilter('all')} label="Все" count={findings.length} />
          <FilterBtn active={filter === 'working'} onClick={() => setFilter('working')} label="Работает" count={findings.filter(f => f.status === 'working').length} />
          <FilterBtn active={filter === 'broken'} onClick={() => setFilter('broken')} label="Не работает" count={findings.filter(f => f.status === 'broken').length} />
        </div>
      </div>

      <div className="space-y-4">
        {filtered.map((finding) => (
          <FindingCard key={finding.id} finding={finding} />
        ))}
      </div>
    </div>
  )
}

function FilterBtn({ active, onClick, label, count }: {
  active: boolean; onClick: () => void; label: string; count: number
}) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
        active
          ? 'bg-blue-600 text-white'
          : 'bg-gray-800 text-gray-400 hover:text-white'
      }`}
    >
      {label} ({count})
    </button>
  )
}

function FindingCard({ finding }: { finding: {
  id: number; category: string; status: 'working' | 'broken'; title: string;
  description: string; code: string; source: string;
}}) {
  const [expanded, setExpanded] = useState(false)
  
  return (
    <div className={`rounded-xl border p-5 transition-all ${
      finding.status === 'working'
        ? 'bg-green-950/10 border-green-800/30 hover:border-green-700/50'
        : 'bg-red-950/10 border-red-800/30 hover:border-red-700/50'
    }`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${
              finding.status === 'working'
                ? 'bg-green-800/40 text-green-300'
                : 'bg-red-800/40 text-red-300'
            }`}>
              {finding.status === 'working' ? '✅ OK' : '❌ FAIL'}
            </span>
            <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded">{finding.category}</span>
          </div>
          <h4 className="font-semibold text-white mb-1">{finding.title}</h4>
          <p className="text-sm text-gray-400">{finding.description}</p>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-gray-500 hover:text-white text-sm px-2 py-1 rounded hover:bg-gray-800 transition-colors"
        >
          {expanded ? '▲' : '▼'}
        </button>
      </div>
      
      {expanded && (
        <div className="mt-4 space-y-3">
          <div className="bg-gray-900 rounded-lg p-4 font-mono text-sm overflow-x-auto">
            <pre className="text-cyan-300 whitespace-pre-wrap">{finding.code}</pre>
          </div>
          <div className="text-xs text-gray-500">
            📌 Источник: {finding.source}
          </div>
        </div>
      )}
    </div>
  )
}
