export default function Recommendations() {
  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-bold text-white">Рекомендации по решению</h2>
      
      {/* Solution Options */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SolutionCard
          variant="A"
          title="Ручной шаблон"
          difficulty="Лёгкий"
          time="5 минут"
          reliability="Высокая"
          recommended
          description="Пользователь создаёт шаблон модели вручную с соединениями. Агент копирует объекты и меняет только параметры."
          steps={[
            'Пользователь создаёт модель с Source → Station → Buffer → Drain',
            'Соединяет объекты коннекторами в GUI',
            'Сохраняет как template.spp',
            'Агент загружает шаблон через app.LoadModel()',
            'Агент копирует объекты: copySelection → pasteFromClipboard',
            'Агент меняет параметры через ExecuteSimTalk',
          ]}
          pros={['Самый простой путь', '100% работает', 'Не требует новых API']}
          cons={['Требует участие человека', 'Ограниченная гибкость']}
        />
        
        <SolutionCard
          variant="B"
          title="Встроенный Python 2404"
          difficulty="Средний"
          time="2-4 часа"
          reliability="Средняя"
          description="Использовать встроенный Python в Plant Simulation 2404 для создания соединений через нативный API."
          steps={[
            'Изучить документацию "DCOM до встроенного Python"',
            'Найти правильный способ создания PythonModule',
            'Запустить Python-скрипт внутри PS',
            'Использовать нативный Python API для соединений',
            'Возможно: connector = Connector(from_obj, to_obj)',
          ]}
          pros={['Полностью автоматический', 'Нативный API PS', 'Долгосрочное решение']}
          cons={['Требует исследование документации', 'Может не работать через COM']}
        />
        
        <SolutionCard
          variant="C"
          title="GUI-автоматизация"
          difficulty="Сложный"
          time="4-8 часов"
          reliability="Низкая"
          description="Использовать pyautogui для кликов по интерфейсу Plant Simulation. Ненадёжно, но возможно."
          steps={[
            'Калибровать координаты элементов GUI',
            'pyautogui.click() на кнопке Connector',
            'Кликнуть на Source, затем на Station',
            'Повторить для всех соединений',
            'Добавить задержки и проверки',
          ]}
          pros={['Не требует новых API', 'Работает с любой версией']}
          cons={['Очень ненадёжно', 'Зависит от разрешения экрана', 'Медленно', 'Хрупкое решение']}
        />
        
        <SolutionCard
          variant="D"
          title="Интроспекция API"
          difficulty="Средний"
          time="1-2 часа"
          reliability="Средняя"
          description="Получить полный список атрибутов и методов объектов через COM для поиска неизвестного метода соединений."
          steps={[
            'Исправить ps_api_introspection.py',
            'Создать тестовые объекты',
            'Вызвать putAttributeNamesIntoTable()',
            'Получить список всех атрибутов Source/Connector',
            'Найти метод создания соединений',
          ]}
          pros={['Может найти скрытый API', 'Научный подход']}
          cons={['Требует исправления скрипта', 'Может не дать результата']}
        />
      </div>

      {/* Don't Repeat */}
      <div className="rounded-xl bg-gray-900 border border-gray-800 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">⛔ Не повторять эти попытки</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <DontDo item="succ := — атрибут только для чтения" />
          <DontDo item="create() — метод не существует, используйте derive()" />
          <DontDo item="SingleProc — используйте Station" />
          <DontDo item="pa.name := — используйте pa.setName()" />
          <DontDo item="return в ExecuteSimTalk — только внутри методов" />
          <DontDo item='GetValue("root.PA", "interval") — неправильный синтаксис' />
          <DontDo item="Одинарные кавычки — только двойные" />
          <DontDo item=".MUs.Entity — используйте .MUs.Part" />
        </div>
      </div>

      {/* Critical Facts for LLM */}
      <div className="rounded-xl bg-gray-900 border border-gray-800 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">📝 Критические факты для промптов LLM</h3>
        <div className="bg-gray-950 rounded-lg p-4 font-mono text-sm overflow-x-auto">
          <pre className="text-green-300 whitespace-pre-wrap">{`В Plant Simulation 2404:
- Класс станции: Station (не SingleProc!)
- Метод создания: derive (не create!)
- Переименование: setName() (не .name := !)
- Удаление: deleteObject
- Соединения: succ только для чтения, 
  программное создание не работает через COM
- Строки: только двойные кавычки
- return: только внутри методов
- EventController: .MaterialFlow.EventController.derive(root)
- Параметры: interval, procTime, capacity (числа в секундах)`}</pre>
        </div>
      </div>
    </div>
  )
}

function SolutionCard({ variant, title, difficulty, time, reliability, recommended, description, steps, pros, cons }: {
  variant: string; title: string; difficulty: string; time: string; reliability: string;
  recommended?: boolean; description: string; steps: string[]; pros: string[]; cons: string[];
}) {
  return (
    <div className={`rounded-xl border p-6 relative ${
      recommended
        ? 'bg-blue-950/20 border-blue-700/40 ring-1 ring-blue-600/20'
        : 'bg-gray-900 border-gray-800'
    }`}>
      {recommended && (
        <div className="absolute -top-3 left-4 px-3 py-0.5 bg-blue-600 rounded-full text-xs font-medium text-white">
          ⭐ Рекомендуется
        </div>
      )}
      
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-lg bg-gray-800 flex items-center justify-center font-bold text-lg text-blue-400">
          {variant}
        </div>
        <div>
          <h4 className="font-semibold text-white">{title}</h4>
          <div className="flex gap-3 text-xs text-gray-400">
            <span>⏱️ {time}</span>
            <span>📊 {difficulty}</span>
            <span>🎯 {reliability}</span>
          </div>
        </div>
      </div>
      
      <p className="text-sm text-gray-300 mb-4">{description}</p>
      
      <div className="mb-4">
        <h5 className="text-xs font-semibold text-gray-400 uppercase mb-2">Шаги</h5>
        <ol className="space-y-1">
          {steps.map((step, i) => (
            <li key={i} className="text-xs text-gray-300 flex items-start gap-2">
              <span className="text-blue-400 font-mono shrink-0">{i + 1}.</span>
              {step}
            </li>
          ))}
        </ol>
      </div>
      
      <div className="grid grid-cols-2 gap-3">
        <div>
          <h5 className="text-xs font-semibold text-green-400 mb-1">Плюсы</h5>
          {pros.map((pro, i) => (
            <div key={i} className="text-xs text-green-300/80 flex items-center gap-1">
              <span>+</span> {pro}
            </div>
          ))}
        </div>
        <div>
          <h5 className="text-xs font-semibold text-red-400 mb-1">Минусы</h5>
          {cons.map((con, i) => (
            <div key={i} className="text-xs text-red-300/80 flex items-center gap-1">
              <span>-</span> {con}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function DontDo({ item }: { item: string }) {
  return (
    <div className="flex items-center gap-2 rounded-lg bg-red-950/20 border border-red-900/30 px-3 py-2">
      <span className="text-red-400">🚫</span>
      <span className="text-sm text-red-200">{item}</span>
    </div>
  )
}
