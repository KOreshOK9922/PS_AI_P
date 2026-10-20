export default function StatusPanel() {
  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-bold text-white">Статус системы</h2>
      
      {/* Overall Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Working */}
        <div className="rounded-xl bg-green-950/20 border border-green-800/40 p-6">
          <h3 className="text-lg font-semibold text-green-300 mb-4 flex items-center gap-2">
            <span className="text-xl">✅</span> Подтверждено работает
          </h3>
          <div className="space-y-3">
            <StatusItem
              name="Создание объектов"
              detail="Source, Station, Buffer, Drain, EventController"
              code='.MaterialFlow.Source.derive(root)'
            />
            <StatusItem
              name="Переименование"
              detail="Метод setName()"
              code='pa.setName("SRC_1")'
            />
            <StatusItem
              name="Установка параметров"
              detail="interval, procTime, capacity"
              code='root.SRC_1.interval := 120'
            />
            <StatusItem
              name="Удаление объектов"
              detail="Метод deleteObject"
              code='root.SRC_1.deleteObject'
            />
            <StatusItem
              name="Сохранение модели"
              detail="SaveModel()"
              code='app.SaveModel(r"C:\\path\\model.spp")'
            />
            <StatusItem
              name="Ollama LLM"
              detail="qwen2.5-coder:7b на localhost:11434"
              code='POST /api/generate'
            />
            <StatusItem
              name="Fallback-парсер"
              detail="Regex-парсер при недоступности LLM"
              code='re.search(r"источник|source", desc)'
            />
          </div>
        </div>
        
        {/* Not Working */}
        <div className="rounded-xl bg-red-950/20 border border-red-800/40 p-6">
          <h3 className="text-lg font-semibold text-red-300 mb-4 flex items-center gap-2">
            <span className="text-xl">❌</span> Не работает
          </h3>
          <div className="space-y-3">
            <StatusItem
              name="Создание соединений"
              detail="ГЛАВНАЯ ПРОБЛЕМА — 15 попыток, все неудачны"
              code='root.SRC_1.succ := root.ST_1  // Error!'
              failed
            />
            <StatusItem
              name="Чтение координат"
              detail="xPos, yPos, posX, posY — все ошибки"
              code='app.GetValue("root.PA", "xPos")'
              failed
            />
            <StatusItem
              name="Встроенный Python"
              detail="PythonModule не запускается через COM"
              code='root.PYTHON_MODULE.execute'
              failed
            />
            <StatusItem
              name="GUI-автоматизация"
              detail="pywinauto не находит кнопку Connector"
              code='win.descendants(control_type="Button")'
              failed
            />
            <StatusItem
              name="VLM (llava:7b)"
              detail="Не может читать интерфейс PS"
              code='"low resolution, no text labels"'
              failed
            />
          </div>
        </div>
      </div>

      {/* Connection Attempts Table */}
      <div className="rounded-xl bg-gray-900 border border-gray-800 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Все попытки создания соединений</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left py-2 px-3 text-gray-400 font-medium">#</th>
                <th className="text-left py-2 px-3 text-gray-400 font-medium">Метод</th>
                <th className="text-left py-2 px-3 text-gray-400 font-medium">Код</th>
                <th className="text-left py-2 px-3 text-gray-400 font-medium">Ошибка</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {connectionAttempts.map((attempt, i) => (
                <tr key={i} className="hover:bg-gray-800/50">
                  <td className="py-2 px-3 text-gray-500">{i + 1}</td>
                  <td className="py-2 px-3 text-gray-200">{attempt.method}</td>
                  <td className="py-2 px-3 font-mono text-xs text-cyan-300">{attempt.code}</td>
                  <td className="py-2 px-3 text-xs text-red-300 max-w-xs truncate">{attempt.error}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Class Names */}
      <div className="rounded-xl bg-gray-900 border border-gray-800 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Несоответствие имён классов (2404 vs учебники)</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="rounded-lg bg-red-950/20 border border-red-800/30 p-4">
            <h4 className="text-sm font-semibold text-red-300 mb-3">❌ Из учебников (2017, 2019)</h4>
            <div className="space-y-2 font-mono text-sm">
              <div className="text-red-200">SingleProc</div>
              <div className="text-red-200">ParallelProc</div>
              <div className="text-red-200">.MUs.Entity</div>
              <div className="text-red-200">.create(root)</div>
              <div className="text-red-200">pa.name := "..."</div>
            </div>
          </div>
          <div className="rounded-lg bg-green-950/20 border border-green-800/30 p-4">
            <h4 className="text-sm font-semibold text-green-300 mb-3">✅ Plant Simulation 2404</h4>
            <div className="space-y-2 font-mono text-sm">
              <div className="text-green-200">Station</div>
              <div className="text-green-200">ParallelStation</div>
              <div className="text-green-200">.MUs.Part</div>
              <div className="text-green-200">.derive(root)</div>
              <div className="text-green-200">pa.setName("...")</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function StatusItem({ name, detail, code, failed = false }: {
  name: string; detail: string; code: string; failed?: boolean
}) {
  return (
    <div className={`rounded-lg p-3 ${failed ? 'bg-red-900/10' : 'bg-green-900/10'}`}>
      <div className="flex items-center justify-between mb-1">
        <span className="font-medium text-sm text-white">{name}</span>
        <span className={`text-xs px-2 py-0.5 rounded-full ${failed ? 'bg-red-800/40 text-red-300' : 'bg-green-800/40 text-green-300'}`}>
          {failed ? 'FAIL' : 'OK'}
        </span>
      </div>
      <p className="text-xs text-gray-400 mb-1">{detail}</p>
      <code className="text-xs text-cyan-300 font-mono block truncate">{code}</code>
    </div>
  )
}

const connectionAttempts = [
  { method: 'succ :=', code: 'root.SRC_1.succ := root.ST_1', error: 'cannot assign to left hand side' },
  { method: 'succ(1) :=', code: 'root.SRC_1.succ(1) := root.ST_1', error: 'cannot assign to left hand side' },
  { method: 'Connector.derive (4 args)', code: '.MaterialFlow.Connector.derive(root, "C1", src, dst)', error: 'Wrong number of parameters: 4 passed, at most 3' },
  { method: 'Connector.derive (strings)', code: '.MaterialFlow.Connector.derive(root, "C1", "SRC", "ST")', error: 'Incompatible types: integer expected' },
  { method: 'startpoint/endpoint', code: 'c.startpoint := root.SRC_1', error: 'Unknown identifier startpoint' },
  { method: 'setFrom/setTo', code: 'c.setFrom(root.SRC_1)', error: 'Unknown identifier setFrom' },
  { method: 'fromObject/toObject', code: 'c.fromObject := root.SRC_1', error: 'Unknown identifier fromObject' },
  { method: 'start/end', code: 'c.start := root.SRC_1', error: 'Unknown identifier start' },
  { method: 'pred/succ on connector', code: 'c.pred := root.SRC_1', error: 'Unknown identifier pred' },
  { method: 'connect()', code: 'root.SRC_1.connect(root.ST_1)', error: 'Unknown identifier connect' },
  { method: 'connectTo()', code: 'root.SRC_1.connectTo(root.ST_1)', error: 'Unknown identifier connectTo' },
  { method: 'addSucc()', code: 'root.SRC_1.addSucc(root.ST_1)', error: 'Unknown identifier addSucc' },
  { method: 'insertSucc()', code: 'root.SRC_1.insertSucc(1, root.ST_1)', error: 'Unknown identifier insertSucc' },
  { method: 'setSucc()', code: 'root.SRC_1.setSucc(1, root.ST_1)', error: 'Unknown identifier setSucc' },
  { method: 'setAttribute()', code: 'root.SRC_1.setAttribute("succ", root.ST_1)', error: 'Unknown identifier setAttribute' },
]
