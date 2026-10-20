import { useState } from 'react'

export default function CodeExplorer() {
  const [activeSnippet, setActiveSnippet] = useState(0)
  
  const snippets = [
    {
      title: 'Подключение к Plant Simulation',
      language: 'python',
      status: 'working',
      code: `import pythoncom
import win32com.client

pythoncom.CoInitialize()
app = win32com.client.Dispatch(
    "Tecnomatix.PlantSimulation.RemoteControl"
)
app.SetNoMessageBox(True)

try:
    app.SetSuppressOpenGL(True)
except Exception:
    pass

app.NewModel()  # Новая пустая модель`,
    },
    {
      title: 'Создание объектов MaterialFlow',
      language: 'python',
      status: 'working',
      code: `code = """
var pa : object
pa := .MaterialFlow.Source.derive(root)
pa.setName("SRC_1")

var pb : object
pb := .MaterialFlow.Station.derive(root)
pb.setName("ST_1")

var pc : object
pc := .MaterialFlow.Buffer.derive(root)
pc.setName("BUF_1")

var pd : object
pd := .MaterialFlow.Drain.derive(root)
pd.setName("DRN_1")
"""
app.ExecuteSimTalk(code)`,
    },
    {
      title: 'Установка параметров',
      language: 'python',
      status: 'working',
      code: `# Интервал источника (секунды)
app.ExecuteSimTalk('root.SRC_1.interval := 120')

# Время обработки (секунды)
app.ExecuteSimTalk('root.ST_1.procTime := 15')

# Ёмкость буфера
app.ExecuteSimTalk('root.BUF_1.capacity := 5')`,
    },
    {
      title: 'Fallback regex-парсер',
      language: 'python',
      status: 'working',
      code: `import re

def fallback_parser(desc):
    objects = []
    connections = []
    
    if re.search(r'источник|source|генератор', desc, re.I):
        objects.append({"name": "SRC_1", "class": "Source", "params": {}})
    
    if re.search(r'станция|station|обработк', desc, re.I):
        objects.append({"name": "ST_1", "class": "Station", "params": {}})
    
    if re.search(r'накопитель|буфер|buffer', desc, re.I):
        objects.append({"name": "BUF_1", "class": "Buffer", "params": {}})
    
    if re.search(r'сход|drain|выход', desc, re.I):
        objects.append({"name": "DRN_1", "class": "Drain", "params": {}})
    
    # Параметры
    interval_match = re.search(r'интервал[а-я]*\\s+(\\d+)', desc, re.I)
    if interval_match and objects:
        objects[0]["params"]["interval"] = int(interval_match.group(1))
    
    proc_match = re.search(r'(?:обработк|время)[а-я]*\\s+(\\d+)', desc, re.I)
    if proc_match and len(objects) > 1:
        objects[1]["params"]["procTime"] = int(proc_match.group(1))
    
    capacity_match = re.search(r'(?:накопитель|емкост)[а-я]*\\s*(?:на\\s+)?(\\d+)', desc, re.I)
    if capacity_match:
        for obj in objects:
            if obj["class"] == "Buffer":
                obj["params"]["capacity"] = int(capacity_match.group(1))
                break
    
    # Последовательные соединения
    for i in range(len(objects) - 1):
        connections.append([objects[i]["name"], objects[i+1]["name"]])
    
    return {"objects": objects, "connections": connections}`,
    },
    {
      title: 'Создание EventController',
      language: 'python',
      status: 'working',
      code: `app.ExecuteSimTalk("""
    var ec : object
    ec := .MaterialFlow.EventController.derive(root)
""")`,
    },
    {
      title: 'Сохранение и закрытие модели',
      language: 'python',
      status: 'working',
      code: `# Сохранение
app.SaveModel(r"C:\\ProgramData\\Siemens\\PS_AI_Agent\\model.spp")

# Закрытие
app.CloseModel()`,
    },
    {
      title: '❌ НЕ РАБОТАЕТ: Соединения (все варианты)',
      language: 'python',
      status: 'broken',
      code: `# Вариант 1: succ := (read-only)
app.ExecuteSimTalk('root.SRC_1.succ := root.ST_1')
# → cannot assign to left hand side

# Вариант 2: Connector.derive (4 args)
app.ExecuteSimTalk('.MaterialFlow.Connector.derive(root, "C1", src, dst)')
# → Wrong number of parameters: 4 passed, at most 3

# Вариант 3: connect()
app.ExecuteSimTalk('root.SRC_1.connect(root.ST_1)')
# → Unknown identifier 'connect'

# Вариант 4: setFrom/setTo
app.ExecuteSimTalk('c.setFrom(root.SRC_1)')
# → Unknown identifier 'setFrom'

# Вариант 5: startpoint/endpoint
app.ExecuteSimTalk('c.startpoint := root.SRC_1')
# → Unknown identifier 'startpoint'

# ... и ещё 10 вариантов — все не работают`,
    },
    {
      title: '❌ НЕ РАБОТАЕТ: Устаревший синтаксис',
      language: 'python',
      status: 'broken',
      code: `# SingleProc → не существует в 2404!
app.ExecuteSimTalk('.MaterialFlow.SingleProc.derive(root)')
# → Unknown identifier 'SingleProc'

# create() → не существует, используйте derive()!
app.ExecuteSimTalk('.MaterialFlow.Source.create(root)')
# → Unknown identifier 'create'

# .name := → read-only!
app.ExecuteSimTalk('pa.name := "SRC_1"')
# → cannot assign to left hand side

# return в ExecuteSimTalk → только внутри методов!
app.ExecuteSimTalk('return root.name;')
# → syntax errors

# Одинарные кавычки → только двойные!
app.ExecuteSimTalk("pa.setName('SRC_1')")
# → syntax errors`,
    },
  ]

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-white">Исследователь кода</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="lg:col-span-1 space-y-2">
          {snippets.map((snippet, i) => (
            <button
              key={i}
              onClick={() => setActiveSnippet(i)}
              className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all ${
                activeSnippet === i
                  ? 'bg-blue-600/20 border border-blue-600/40 text-blue-200'
                  : 'bg-gray-800/50 border border-transparent text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              <div className="flex items-center gap-2">
                <span className={snippet.status === 'working' ? 'text-green-400' : 'text-red-400'}>
                  {snippet.status === 'working' ? '✅' : '❌'}
                </span>
                <span className="truncate">{snippet.title}</span>
              </div>
            </button>
          ))}
        </div>
        
        {/* Code Display */}
        <div className="lg:col-span-3">
          <div className="rounded-xl bg-gray-950 border border-gray-800 overflow-hidden">
            <div className="bg-gray-900 px-4 py-3 border-b border-gray-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                  snippets[activeSnippet].status === 'working'
                    ? 'bg-green-800/40 text-green-300'
                    : 'bg-red-800/40 text-red-300'
                }`}>
                  {snippets[activeSnippet].status === 'working' ? '✅ Работает' : '❌ Не работает'}
                </span>
                <span className="text-sm text-white font-medium">{snippets[activeSnippet].title}</span>
              </div>
              <span className="text-xs text-gray-500 bg-gray-800 px-2 py-1 rounded">
                {snippets[activeSnippet].language}
              </span>
            </div>
            <div className="p-4 overflow-x-auto max-h-[600px] overflow-y-auto">
              <pre className="text-sm font-mono leading-relaxed">
                <code className={snippets[activeSnippet].status === 'working' ? 'text-green-200' : 'text-red-200'}>
                  {snippets[activeSnippet].code}
                </code>
              </pre>
            </div>
          </div>
          
          {/* Copy button */}
          <div className="mt-3 flex justify-end">
            <button
              onClick={() => navigator.clipboard.writeText(snippets[activeSnippet].code)}
              className="px-4 py-2 rounded-lg bg-gray-800 text-gray-300 text-sm hover:bg-gray-700 hover:text-white transition-colors"
            >
              📋 Копировать код
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
